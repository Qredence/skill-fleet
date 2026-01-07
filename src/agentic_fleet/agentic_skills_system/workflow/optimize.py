"""Optimization scripts for DSPy skill creation workflows.

This module provides:
- MIPROv2 optimization for prompt tuning
- GEPA optimization for reflective prompt evolution
- Save/load functionality for optimized programs
- MLflow tracking integration (optional)

Approved LLM Models:
- gemini-3-flash-preview: Primary model for all workflow steps
- gemini-3-pro-preview: For GEPA reflection (stronger reasoning)
- deepseek-v3.2: Cost-effective alternative
- Nemotron-3-Nano-30B-A3B: Lightweight/fast operations
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import dspy

if TYPE_CHECKING:
    from .programs import SkillCreationProgram

logger = logging.getLogger(__name__)


# =============================================================================
# Approved Models Configuration
# =============================================================================

APPROVED_MODELS = {
    "gemini-3-flash-preview": "google/gemini-3-flash-preview",
    "gemini-3-pro-preview": "google/gemini-3-pro-preview",
    "deepseek-v3.2": "deepinfra/deepseek-v3.2",
    "Nemotron-3-Nano-30B-A3B": "nvidia/Nemotron-3-Nano-30B-A3B",
}

DEFAULT_MODEL = "gemini-3-flash-preview"
REFLECTION_MODEL = "gemini-3-pro-preview"  # For GEPA reflection


def get_lm(
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    **kwargs,
) -> dspy.LM:
    """Get a DSPy LM instance for an approved model.

    Args:
        model_name: Name of approved model (without provider prefix)
        temperature: LLM temperature
        **kwargs: Additional LM configuration

    Returns:
        Configured dspy.LM instance

    Raises:
        ValueError: If model is not in approved list
    """
    if model_name not in APPROVED_MODELS:
        raise ValueError(
            f"Model '{model_name}' is not approved. "
            f"Use one of: {list(APPROVED_MODELS.keys())}"
        )

    model_path = APPROVED_MODELS[model_name]
    return dspy.LM(model_path, temperature=temperature, **kwargs)


# =============================================================================
# MIPROv2 Optimization
# =============================================================================


def optimize_with_miprov2(
    program: "SkillCreationProgram",
    trainset_path: str | Path = "workflow/data/trainset.json",
    output_path: str | Path = "workflow/optimized/miprov2/",
    model: str = DEFAULT_MODEL,
    auto: Literal["light", "medium", "heavy"] = "medium",
    max_bootstrapped_demos: int = 4,
    max_labeled_demos: int = 4,
    num_threads: int = 8,
) -> "SkillCreationProgram":
    """Optimize skill creation workflow with MIPROv2.

    MIPROv2 (Multi-stage Instruction Proposal Optimizer v2) tunes:
    - Instructions for each signature
    - Few-shot example selection
    - Prompt structure

    Args:
        program: SkillCreationProgram to optimize
        trainset_path: Path to training data JSON
        output_path: Directory to save optimized program
        model: Approved model name for optimization
        auto: Optimization intensity ("light", "medium", "heavy")
        max_bootstrapped_demos: Max examples from successful rollouts
        max_labeled_demos: Max examples from training set
        num_threads: Number of parallel threads

    Returns:
        Optimized SkillCreationProgram
    """
    from dspy.teleprompt import MIPROv2

    from .evaluation import load_trainset, skill_creation_metric, split_dataset

    # Configure with approved model
    lm = get_lm(model)
    dspy.configure(lm=lm)
    logger.info(f"Configured DSPy with model: {model}")

    # Load and split training data
    examples = load_trainset(trainset_path)
    train, val = split_dataset(examples, train_ratio=0.8)
    logger.info(f"Loaded {len(examples)} examples: {len(train)} train, {len(val)} val")

    # Configure optimizer
    optimizer = MIPROv2(
        metric=skill_creation_metric,
        auto=auto,
        max_bootstrapped_demos=max_bootstrapped_demos,
        max_labeled_demos=max_labeled_demos,
        num_threads=num_threads,
    )

    logger.info(f"Starting MIPROv2 optimization (auto={auto})...")

    # Run optimization
    optimized = optimizer.compile(
        program,
        trainset=train,
        valset=val,
    )

    # Save optimized program
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    optimized.save(str(output_path), save_program=True)

    logger.info(f"Optimized program saved to {output_path}")
    return optimized


# =============================================================================
# GEPA Optimization
# =============================================================================


def optimize_with_gepa(
    program: "SkillCreationProgram",
    trainset_path: str | Path = "workflow/data/trainset.json",
    output_path: str | Path = "workflow/optimized/gepa/",
    model: str = DEFAULT_MODEL,
    reflection_model: str = REFLECTION_MODEL,
    auto: Literal["light", "medium", "heavy"] = "medium",
    track_stats: bool = True,
) -> "SkillCreationProgram":
    """Optimize skill creation workflow with GEPA.

    GEPA (Genetic-Pareto Reflective Prompt Optimizer) uses:
    - Reflective mutation based on LLM traces
    - Pareto frontier for multi-objective optimization
    - Textual feedback for improvement

    Args:
        program: SkillCreationProgram to optimize
        trainset_path: Path to training data JSON
        output_path: Directory to save optimized program
        model: Approved model name for program execution
        reflection_model: Model for GEPA reflection (should be strong)
        auto: Optimization intensity
        track_stats: Whether to track detailed statistics

    Returns:
        Optimized SkillCreationProgram
    """
    from .evaluation import load_trainset, skill_creation_metric, split_dataset

    # Configure with approved model
    lm = get_lm(model)
    dspy.configure(lm=lm)
    logger.info(f"Configured DSPy with model: {model}")

    # Get reflection LM (stronger model for analysis)
    reflection_lm = get_lm(reflection_model, temperature=1.0)
    logger.info(f"Using reflection model: {reflection_model}")

    # Load and split training data
    examples = load_trainset(trainset_path)
    train, val = split_dataset(examples, train_ratio=0.8)
    logger.info(f"Loaded {len(examples)} examples: {len(train)} train, {len(val)} val")

    # Configure GEPA optimizer
    optimizer = dspy.GEPA(
        metric=skill_creation_metric,
        reflection_lm=reflection_lm,
        auto=auto,
        track_stats=track_stats,
    )

    logger.info(f"Starting GEPA optimization (auto={auto})...")

    # Run optimization
    optimized = optimizer.compile(
        program,
        trainset=train,
        valset=val,
    )

    # Save optimized program
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    optimized.save(str(output_path), save_program=True)

    logger.info(f"Optimized program saved to {output_path}")
    return optimized


# =============================================================================
# Load/Save Utilities
# =============================================================================


def load_optimized_program(
    path: str | Path = "workflow/optimized/miprov2/",
) -> "SkillCreationProgram":
    """Load a previously optimized program.

    Args:
        path: Directory containing the saved program

    Returns:
        Loaded SkillCreationProgram with optimized state
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Optimized program not found at {path}")

    program = dspy.load(str(path))
    logger.info(f"Loaded optimized program from {path}")
    return program


def save_program_state(
    program: "SkillCreationProgram",
    path: str | Path,
    save_program: bool = False,
) -> None:
    """Save program state to disk.

    Args:
        program: Program to save
        path: Output path (file for state-only, dir for full program)
        save_program: If True, save full program (uses cloudpickle)
    """
    path = Path(path)

    if save_program:
        path.mkdir(parents=True, exist_ok=True)
        program.save(str(path), save_program=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        program.save(str(path), save_program=False)

    logger.info(f"Saved program to {path} (full_program={save_program})")


# =============================================================================
# MLflow Integration (Optional)
# =============================================================================


def optimize_with_tracking(
    program: "SkillCreationProgram",
    trainset_path: str | Path = "workflow/data/trainset.json",
    output_path: str | Path = "workflow/optimized/tracked/",
    optimizer_type: Literal["miprov2", "gepa"] = "miprov2",
    model: str = DEFAULT_MODEL,
    experiment_name: str = "skills-fleet-optimization",
    **optimizer_kwargs,
) -> "SkillCreationProgram":
    """Optimize with MLflow tracking enabled.

    Requires: pip install mlflow>=2.21.1

    Args:
        program: Program to optimize
        trainset_path: Path to training data
        output_path: Output directory
        optimizer_type: Which optimizer to use
        model: Approved model name
        experiment_name: MLflow experiment name
        **optimizer_kwargs: Additional optimizer arguments

    Returns:
        Optimized program
    """
    try:
        import mlflow
    except ImportError:
        logger.warning("MLflow not installed. Running without tracking.")
        if optimizer_type == "miprov2":
            return optimize_with_miprov2(
                program, trainset_path, output_path, model, **optimizer_kwargs
            )
        else:
            return optimize_with_gepa(
                program, trainset_path, output_path, model, **optimizer_kwargs
            )

    # Enable MLflow autologging for DSPy
    mlflow.dspy.autolog(
        log_compiles=True,
        log_evals=True,
        log_traces_from_compile=True,
    )

    mlflow.set_experiment(experiment_name)
    logger.info(f"MLflow experiment: {experiment_name}")

    with mlflow.start_run():
        # Log configuration
        mlflow.log_params({
            "optimizer": optimizer_type,
            "model": model,
            "trainset": str(trainset_path),
        })

        # Run optimization
        if optimizer_type == "miprov2":
            optimized = optimize_with_miprov2(
                program, trainset_path, output_path, model, **optimizer_kwargs
            )
        else:
            optimized = optimize_with_gepa(
                program, trainset_path, output_path, model, **optimizer_kwargs
            )

        # Log the optimized model
        mlflow.dspy.log_model(optimized, "optimized_skill_creator")

    return optimized


# =============================================================================
# Quick Evaluation
# =============================================================================


def quick_evaluate(
    program: "SkillCreationProgram",
    trainset_path: str | Path = "workflow/data/trainset.json",
    model: str = DEFAULT_MODEL,
    n_examples: int | None = None,
) -> dict:
    """Run a quick evaluation on the program.

    Args:
        program: Program to evaluate
        trainset_path: Path to evaluation data
        model: Model to use for evaluation
        n_examples: Number of examples to evaluate (None = all)

    Returns:
        Evaluation results dict
    """
    from .evaluation import (
        evaluate_program,
        load_trainset,
        print_evaluation_report,
        skill_creation_metric,
    )

    # Configure model
    lm = get_lm(model)
    dspy.configure(lm=lm)

    # Load examples
    examples = load_trainset(trainset_path)
    if n_examples:
        examples = examples[:n_examples]

    # Create minimal parent_skills_getter for evaluation
    def dummy_parent_getter(path: str) -> str:
        return "[]"

    # Run evaluation
    results = evaluate_program(
        program,
        examples,
        metric=skill_creation_metric,
        existing_skills=[],
        taxonomy_structure={},
        parent_skills_getter=dummy_parent_getter,
    )

    print_evaluation_report(results)
    return results


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """CLI entry point for optimization."""
    import argparse

    parser = argparse.ArgumentParser(description="Optimize skill creation workflow")
    parser.add_argument(
        "--optimizer",
        choices=["miprov2", "gepa"],
        default="miprov2",
        help="Optimizer algorithm",
    )
    parser.add_argument(
        "--model",
        choices=list(APPROVED_MODELS.keys()),
        default=DEFAULT_MODEL,
        help="LLM model to use",
    )
    parser.add_argument(
        "--trainset",
        default="workflow/data/trainset.json",
        help="Path to training data",
    )
    parser.add_argument(
        "--output",
        default="workflow/optimized/",
        help="Output directory",
    )
    parser.add_argument(
        "--auto",
        choices=["light", "medium", "heavy"],
        default="medium",
        help="Optimization intensity",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Enable MLflow tracking",
    )
    parser.add_argument(
        "--evaluate-only",
        action="store_true",
        help="Only run evaluation, don't optimize",
    )

    args = parser.parse_args()

    # Import program
    from .programs import SkillCreationProgram

    program = SkillCreationProgram()

    if args.evaluate_only:
        quick_evaluate(program, args.trainset, args.model)
        return

    output_path = Path(args.output) / args.optimizer

    if args.track:
        optimize_with_tracking(
            program,
            args.trainset,
            output_path,
            optimizer_type=args.optimizer,
            model=args.model,
            auto=args.auto,
        )
    elif args.optimizer == "miprov2":
        optimize_with_miprov2(
            program,
            args.trainset,
            output_path,
            model=args.model,
            auto=args.auto,
        )
    else:
        optimize_with_gepa(
            program,
            args.trainset,
            output_path,
            model=args.model,
            auto=args.auto,
        )


if __name__ == "__main__":
    main()
