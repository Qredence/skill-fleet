#!/usr/bin/env python3
"""Quick optimization script for Phase 2 - MIPROv2 with expanded training data.

This script runs a focused optimization cycle using:
- trainset_v4.json (50 examples)
- Enhanced signatures from Phase 1
- MIPROv2 with auto='medium' (balanced speed/quality)

Usage:
    uv run python scripts/run_optimization.py
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import dspy

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Imports from skills-fleet
from skill_fleet.core.dspy.metrics.skill_quality import skill_quality_metric
from skill_fleet.core.optimization.optimizer import get_lm

def load_training_data(trainset_path: str = "config/training/trainset_v4.json") -> list[dspy.Example]:
    """Load training examples from JSON.
    
    Args:
        trainset_path: Path to training set JSON file
    
    Returns:
        List of DSPy Example objects
    """
    logger.info(f"Loading training data from {trainset_path}")
    
    with open(trainset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert to DSPy Examples with proper input marking
    examples = []
    for item in data:
        example = dspy.Example(
            task_description=item["task_description"],
            expected_taxonomy_path=item.get("expected_taxonomy_path", ""),
            expected_name=item.get("expected_name", ""),
            expected_skill_style=item.get("expected_skill_style", "comprehensive"),
            expected_subdirectories=item.get("expected_subdirectories", []),
            expected_keywords=item.get("expected_keywords", []),
            expected_description=item.get("expected_description", ""),
        ).with_inputs("task_description")
        examples.append(example)
    
    logger.info(f"Loaded {len(examples)} training examples")
    return examples


class SimpleSkillProgram(dspy.Module):
    """Simple skill program for optimization testing."""
    
    def __init__(self):
        super().__init__()
        from skill_fleet.core.dspy.signatures.phase1_understanding import GatherRequirements
        self.gather = dspy.ChainOfThought(GatherRequirements)
    
    def forward(self, task_description: str):
        result = self.gather(task_description=task_description)
        return result


def create_simple_program() -> dspy.Module:
    """Create a simplified program for testing optimization.
    
    Returns a basic ChainOfThought module that we can optimize quickly.
    For full optimization, use the actual SkillCreationProgram.
    """
    return SimpleSkillProgram()


def simple_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Simple metric for quick optimization testing.
    
    Checks if basic fields are present and reasonable.
    """
    score = 0.0
    
    # Check if we got expected outputs
    if hasattr(prediction, "domain") and prediction.domain:
        score += 0.2
    
    if hasattr(prediction, "category") and prediction.category:
        score += 0.2
    
    if hasattr(prediction, "target_level") and prediction.target_level:
        score += 0.2
    
    if hasattr(prediction, "topics") and len(prediction.topics) >= 3:
        score += 0.2
    
    # Check if category matches expected (if available)
    if hasattr(example, "expected_taxonomy_path") and hasattr(prediction, "category"):
        expected_category = example.expected_taxonomy_path.split("/")[0] if example.expected_taxonomy_path else ""
        if expected_category and prediction.category.lower() in expected_category.lower():
            score += 0.2
    
    return min(score, 1.0)


def run_optimization(
    trainset: list[dspy.Example],
    program: dspy.Module,
    optimizer_type: str = "miprov2",
    auto_level: str = "medium",
) -> dspy.Module:
    """Run DSPy optimization.
    
    Args:
        trainset: Training examples
        program: DSPy program to optimize
        optimizer_type: 'miprov2' or 'gepa'
        auto_level: 'light', 'medium', or 'heavy' (for MIPROv2)
    
    Returns:
        Optimized program
    """
    logger.info(f"Starting {optimizer_type} optimization with auto='{auto_level}'")
    logger.info(f"Training set size: {len(trainset)} examples")
    
    # Create optimizer
    if optimizer_type == "miprov2":
        # MIPROv2 with medium auto level - balanced speed/quality
        optimizer = dspy.MIPROv2(
            metric=simple_metric,
            auto=auto_level,
            num_threads=8,  # Parallel optimization
        )
        
        # Compile with reasonable demo counts
        logger.info("Running MIPROv2 optimization (this may take 5-15 minutes)...")
        optimized = optimizer.compile(
            program,
            trainset=trainset,
            max_bootstrapped_demos=2,  # Conservative for speed
            max_labeled_demos=2,
            num_candidate_programs=8,  # Reduced from default 16 for speed
        )
    
    elif optimizer_type == "bootstrap":
        # BootstrapFewShot for fastest, simplest optimization
        optimizer = dspy.BootstrapFewShot(
            metric=simple_metric,
            max_bootstrapped_demos=2,
            max_labeled_demos=1,
        )
        
        logger.info("Running BootstrapFewShot optimization (fastest)...")
        optimized = optimizer.compile(program, trainset=trainset)
    
    elif optimizer_type == "gepa":
        # GEPA for faster, reflection-based optimization
        # Requires reflection_lm for the optimization process
        from skill_fleet.core.optimization.optimizer import get_lm
        
        reflection_lm = get_lm("gemini-3-flash-preview", temperature=1.0)
        
        # Wrap metric to match GEPA's signature: (gold, pred, trace, pred_name, pred_trace)
        def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
            """GEPA-compatible metric function."""
            score = simple_metric(gold, pred, trace)
            # Return dict with score and optional feedback for GEPA
            return {"score": score, "feedback": f"Score: {score:.2f}"}
        
        optimizer = dspy.GEPA(
            metric=gepa_metric,
            reflection_lm=reflection_lm,
            auto="light",  # Budget: light (fastest), medium, heavy
        )
        
        logger.info("Running GEPA optimization (reflection-based, faster)...")
        optimized = optimizer.compile(program, trainset=trainset)
    
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_type}")
    
    logger.info("✅ Optimization complete!")
    return optimized


def evaluate_program(
    program: dspy.Module,
    testset: list[dspy.Example],
    metric,
) -> dict:
    """Evaluate program on test set.
    
    Args:
        program: DSPy program to evaluate
        testset: Test examples
        metric: Evaluation metric function
    
    Returns:
        Dictionary of evaluation results
    """
    logger.info(f"Evaluating on {len(testset)} test examples...")
    
    from dspy.evaluate import Evaluate
    
    evaluator = Evaluate(
        devset=testset,
        metric=metric,
        num_threads=8,
        display_progress=True,
    )
    
    score = evaluator(program)
    
    # Convert to float if needed (DSPy may return EvaluationResult)
    if hasattr(score, '__float__'):
        score_float = float(score)
    elif isinstance(score, (int, float)):
        score_float = float(score)
    else:
        # Default to string representation and extract number
        score_str = str(score)
        try:
            score_float = float(score_str)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert score to float: {score_str}")
            score_float = 0.0
    
    logger.info(f"Evaluation score: {score_float:.3f}")
    return {"score": score_float, "num_examples": len(testset)}


def main():
    """Main optimization workflow."""
    print("=" * 60)
    print("Phase 2: DSPy Optimization with Expanded Training Data")
    print("=" * 60)
    
    # 1. Configure DSPy with Gemini
    logger.info("Configuring DSPy with Gemini 3 Flash...")
    lm = get_lm("gemini-3-flash-preview", temperature=1.0)  # Gemini 3 requires temp=1.0
    dspy.configure(lm=lm)
    
    # 2. Load training data
    trainset = load_training_data("config/training/trainset_v4.json")
    
    # Split into train/test (80/20)
    split_idx = int(len(trainset) * 0.8)
    train_examples = trainset[:split_idx]
    test_examples = trainset[split_idx:]
    
    logger.info(f"Split: {len(train_examples)} train, {len(test_examples)} test")
    
    # 3. Create program
    logger.info("Creating skill program...")
    program = create_simple_program()
    
    # 4. Baseline evaluation
    logger.info("\n" + "=" * 60)
    logger.info("Baseline Evaluation (before optimization)")
    logger.info("=" * 60)
    baseline_results = evaluate_program(program, test_examples, simple_metric)
    
    # 5. Run optimization
    logger.info("\n" + "=" * 60)
    logger.info("Running Optimization")
    logger.info("=" * 60)
    
    # Quick BootstrapFewShot optimization first (faster for testing)
    optimized = run_optimization(
        trainset=train_examples,
        program=program,
        optimizer_type="bootstrap",  # Faster than MIPROv2 for initial test
    )
    
    # 6. Evaluate optimized
    logger.info("\n" + "=" * 60)
    logger.info("Post-Optimization Evaluation")
    logger.info("=" * 60)
    optimized_results = evaluate_program(optimized, test_examples, simple_metric)
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("Optimization Results Summary")
    print("=" * 60)
    print(f"Training examples: {len(train_examples)}")
    print(f"Test examples: {len(test_examples)}")
    print(f"Baseline score: {baseline_results['score']:.3f}")
    print(f"Optimized score: {optimized_results['score']:.3f}")
    
    improvement = optimized_results['score'] - baseline_results['score']
    print(f"Improvement: {improvement:+.3f} ({improvement/baseline_results['score']*100:+.1f}%)")
    
    # 8. Save optimized program
    output_dir = Path("config/optimized")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "skill_program_bootstrap_v1.pkl"
    
    logger.info(f"\n💾 Saving optimized program to {output_path}")
    
    import pickle
    try:
        with open(output_path, "wb") as f:
            pickle.dump(optimized, f)
        logger.info("✅ Optimization program saved successfully")
    except Exception as e:
        logger.warning(f"⚠️  Could not pickle optimized program: {e}")
        logger.warning("Results will still be saved, but program won't be pickled")
    
    # Save results
    results_path = output_dir / "optimization_results_bootstrap_v1.json"
    results = {
        "optimizer": "BootstrapFewShot",
        "trainset_size": len(train_examples),
        "testset_size": len(test_examples),
        "baseline_score": baseline_results['score'],
        "optimized_score": optimized_results['score'],
        "improvement": improvement,
        "improvement_percent": improvement / baseline_results['score'] * 100 if baseline_results['score'] > 0 else 0,
    }
    
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"💾 Saved results to {results_path}")
    
    print("\n" + "=" * 60)
    print("✅ Optimization Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review optimization results")
    print("2. Run full MIPROv2 optimization for maximum quality")
    print("3. Test optimized program on real skill creation tasks")
    print("=" * 60)


if __name__ == "__main__":
    main()
