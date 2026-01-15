"""DSPy optimization module for improving skill generation quality.

This module provides optimization capabilities using DSPy's MIPROv2 and
BootstrapFewShot optimizers to improve skill creation programs.

Optimization workflow:
1. Load gold-standard training examples
2. Configure optimizer (MIPROv2 or BootstrapFewShot)
3. Run optimization with quality metrics
4. Save optimized program for future use
5. Compare baseline vs optimized performance

Usage:
    from skill_fleet.core.dspy.optimization import SkillOptimizer

    optimizer = SkillOptimizer()

    # Run optimization
    optimized_program = optimizer.optimize(program, trainset)

    # Save optimized program
    optimizer.save_optimized_program(optimized_program, "my_optimized_program")

    # Load and use optimized program
    loaded_program = optimizer.load_optimized_program("my_optimized_program")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import dspy
import yaml

from ...common.paths import default_config_path, find_repo_root
from ...llm.dspy_config import configure_dspy
from .evaluation import SkillEvaluator
from .metrics import skill_quality_metric
from .training import GoldStandardLoader

logger = logging.getLogger(__name__)

OptimizerType = Literal["miprov2", "bootstrap_fewshot"]


@dataclass
class OptimizationResult:
    """Result of an optimization run."""

    optimizer_type: str
    baseline_score: float
    optimized_score: float
    improvement: float
    improvement_pct: float
    training_examples: int
    optimization_time_seconds: float
    program_path: str | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "optimizer_type": self.optimizer_type,
            "baseline_score": self.baseline_score,
            "optimized_score": self.optimized_score,
            "improvement": self.improvement,
            "improvement_pct": self.improvement_pct,
            "training_examples": self.training_examples,
            "optimization_time_seconds": self.optimization_time_seconds,
            "program_path": self.program_path,
            "config": self.config,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        return f"""
Optimization Results ({self.optimizer_type})
{"=" * 50}
Baseline Score:  {self.baseline_score:.3f}
Optimized Score: {self.optimized_score:.3f}
Improvement:     {self.improvement:+.3f} ({self.improvement_pct:+.1f}%)
Training Examples: {self.training_examples}
Time: {self.optimization_time_seconds:.1f}s
{"=" * 50}
"""


class SkillOptimizer:
    """Optimizer for skill creation programs.

    This class provides methods for optimizing DSPy programs using
    MIPROv2 or BootstrapFewShot optimizers.
    """

    def __init__(
        self,
        config_path: Path | None = None,
        configure_lm: bool = True,
    ):
        """Initialize the optimizer.

        Args:
            config_path: Path to config.yaml (default: auto-detect)
            configure_lm: Whether to configure DSPy LM on init
        """
        self.config_path = config_path or default_config_path()
        self.config = self._load_config()
        self.optimization_config = self.config.get("optimization", {})
        self.repo_root = find_repo_root(self.config_path)

        # Determine optimized programs directory
        training_config = self.optimization_config.get("training", {})
        relative_path = training_config.get("optimized_programs_dir", "config/optimized")
        if self.repo_root:
            self.optimized_dir = self.repo_root / relative_path
        else:
            self.optimized_dir = Path(relative_path)

        if configure_lm:
            configure_dspy(self.config_path, default_task="skill_optimize")

        self.gold_loader = GoldStandardLoader(config_path=self.config_path)
        self.evaluator = SkillEvaluator(config_path=self.config_path, configure_lm=False)

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _get_optimizer_config(self, optimizer_type: OptimizerType) -> dict[str, Any]:
        """Get configuration for specific optimizer type."""
        return self.optimization_config.get(optimizer_type, {})

    def optimize(
        self,
        program: dspy.Module,
        trainset: list[dspy.Example] | None = None,
        optimizer_type: OptimizerType | None = None,
        **kwargs,
    ) -> dspy.Module:
        """Optimize a skill creation program.

        Args:
            program: DSPy program to optimize
            trainset: Training examples (default: load from gold standards)
            optimizer_type: Type of optimizer to use (default: from config)
            **kwargs: Additional optimizer arguments

        Returns:
            Optimized DSPy program
        """
        # Load training set if not provided
        if trainset is None:
            trainset = self.gold_loader.load_trainset(min_quality=0.8)

        if not trainset:
            logger.warning("No training examples available. Returning original program.")
            return program

        # Determine optimizer type
        if optimizer_type is None:
            optimizer_type = self.optimization_config.get("default_optimizer", "miprov2")

        logger.info(f"Starting optimization with {optimizer_type} using {len(trainset)} examples")

        # Run optimization
        if optimizer_type == "miprov2":
            return self._optimize_miprov2(program, trainset, **kwargs)
        elif optimizer_type == "bootstrap_fewshot":
            return self._optimize_bootstrap_fewshot(program, trainset, **kwargs)
        else:
            raise ValueError(f"Unknown optimizer type: {optimizer_type}")

    def _optimize_miprov2(
        self,
        program: dspy.Module,
        trainset: list[dspy.Example],
        **kwargs,
    ) -> dspy.Module:
        """Optimize using MIPROv2.

        Args:
            program: Program to optimize
            trainset: Training examples
            **kwargs: Override config options

        Returns:
            Optimized program
        """
        from dspy.teleprompt import MIPROv2

        config = self._get_optimizer_config("miprov2")

        # Merge config with kwargs
        optimizer_kwargs = {
            "metric": skill_quality_metric,
            "auto": config.get("auto", "medium"),
            "num_threads": config.get("num_threads", 4),
            "verbose": config.get("verbose", True),
        }
        optimizer_kwargs.update(kwargs)

        # Create optimizer
        optimizer = MIPROv2(**optimizer_kwargs)

        # Compile (optimize) the program
        compile_kwargs = {
            "trainset": trainset,
            "max_bootstrapped_demos": config.get("max_bootstrapped_demos", 4),
            "max_labeled_demos": config.get("max_labeled_demos", 4),
        }

        optimized_program = optimizer.compile(program, **compile_kwargs)

        logger.info("MIPROv2 optimization complete")
        return optimized_program

    def _optimize_bootstrap_fewshot(
        self,
        program: dspy.Module,
        trainset: list[dspy.Example],
        **kwargs,
    ) -> dspy.Module:
        """Optimize using BootstrapFewShot.

        Args:
            program: Program to optimize
            trainset: Training examples
            **kwargs: Override config options

        Returns:
            Optimized program
        """
        from dspy.teleprompt import BootstrapFewShot

        config = self._get_optimizer_config("bootstrap_fewshot")

        # Merge config with kwargs
        optimizer_kwargs = {
            "metric": skill_quality_metric,
            "max_bootstrapped_demos": config.get("max_bootstrapped_demos", 4),
            "max_labeled_demos": config.get("max_labeled_demos", 4),
            "max_rounds": config.get("max_rounds", 1),
            "max_errors": config.get("max_errors", 5),
        }
        optimizer_kwargs.update(kwargs)

        # Create optimizer
        optimizer = BootstrapFewShot(**optimizer_kwargs)

        # Compile (optimize) the program
        optimized_program = optimizer.compile(program, trainset=trainset)

        logger.info("BootstrapFewShot optimization complete")
        return optimized_program

    def optimize_and_evaluate(
        self,
        program: dspy.Module,
        trainset: list[dspy.Example] | None = None,
        testset: list[dspy.Example] | None = None,
        optimizer_type: OptimizerType | None = None,
        save_program: bool = True,
        program_name: str | None = None,
    ) -> tuple[dspy.Module, OptimizationResult]:
        """Optimize a program and evaluate improvement.

        Args:
            program: Program to optimize
            trainset: Training examples
            testset: Test examples for evaluation
            optimizer_type: Type of optimizer
            save_program: Whether to save the optimized program
            program_name: Name for saved program

        Returns:
            Tuple of (optimized_program, optimization_result)
        """
        import time

        # Load datasets if not provided
        if trainset is None:
            trainset = self.gold_loader.load_trainset(min_quality=0.8)
        if testset is None:
            testset = self.gold_loader.load_testset(min_quality=0.6)

        if not trainset:
            raise ValueError("No training examples available")

        # Determine optimizer type
        if optimizer_type is None:
            optimizer_type = self.optimization_config.get("default_optimizer", "miprov2")

        # Evaluate baseline
        logger.info("Evaluating baseline program...")
        if testset:
            baseline_score, _ = self.evaluator.evaluate_program(
                program, testset, display_progress=True, display_table=False
            )
        else:
            baseline_score = 0.0

        # Run optimization
        start_time = time.time()
        optimized_program = self.optimize(program, trainset, optimizer_type=optimizer_type)
        optimization_time = time.time() - start_time

        # Evaluate optimized program
        logger.info("Evaluating optimized program...")
        if testset:
            optimized_score, _ = self.evaluator.evaluate_program(
                optimized_program, testset, display_progress=True, display_table=False
            )
        else:
            optimized_score = 0.0

        # Calculate improvement
        improvement = optimized_score - baseline_score
        improvement_pct = (improvement / baseline_score * 100) if baseline_score > 0 else 0.0

        # Save program if requested
        program_path = None
        if save_program:
            if program_name is None:
                program_name = (
                    f"optimized_{optimizer_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            program_path = self.save_optimized_program(optimized_program, program_name)

        # Create result
        result = OptimizationResult(
            optimizer_type=optimizer_type,
            baseline_score=baseline_score,
            optimized_score=optimized_score,
            improvement=improvement,
            improvement_pct=improvement_pct,
            training_examples=len(trainset),
            optimization_time_seconds=optimization_time,
            program_path=str(program_path) if program_path else None,
            config=self._get_optimizer_config(optimizer_type),
            metadata={
                "timestamp": datetime.now().isoformat(),
                "testset_size": len(testset) if testset else 0,
            },
        )

        logger.info(result.summary())
        return optimized_program, result

    def save_optimized_program(
        self,
        program: dspy.Module,
        name: str,
    ) -> Path:
        """Save an optimized program to disk.

        Args:
            program: Optimized program to save
            name: Name for the saved program

        Returns:
            Path to saved program directory
        """
        program_dir = self.optimized_dir / name
        program_dir.mkdir(parents=True, exist_ok=True)

        # Save the program
        program.save(str(program_dir / "program"))

        # Save metadata
        metadata = {
            "name": name,
            "saved_at": datetime.now().isoformat(),
            "dspy_version": getattr(dspy, "__version__", "unknown"),
        }
        with open(program_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved optimized program to {program_dir}")
        return program_dir

    def load_optimized_program(
        self,
        name: str,
        program_class: type[dspy.Module] | None = None,
    ) -> dspy.Module | None:
        """Load a previously saved optimized program.

        Args:
            name: Name of the saved program
            program_class: Class to instantiate (if needed)

        Returns:
            Loaded program or None if not found
        """
        program_dir = self.optimized_dir / name

        if not program_dir.exists():
            logger.warning(f"Optimized program not found: {name}")
            return None

        try:
            # Load the program
            program_path = program_dir / "program"
            if program_class:
                program = program_class()
                program.load(str(program_path))
            else:
                # Try to load without class (may not work for all programs)
                program = dspy.Module()
                program.load(str(program_path))

            logger.info(f"Loaded optimized program from {program_dir}")
            return program

        except Exception as e:
            logger.error(f"Error loading optimized program {name}: {e}")
            return None

    def optimize_with_miprov2(
        self,
        training_examples: list[dict[str, str]],
        auto: str = "medium",
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 4,
    ) -> dspy.Module:
        """Optimize using MIPROv2 with training examples from API.

        This method is designed for use from async contexts (e.g., FastAPI background tasks).
        It uses dspy.context() to avoid async configuration issues.

        Args:
            training_examples: List of dicts with 'path' and 'content' keys
            auto: MIPROv2 auto setting ('light', 'medium', 'heavy')
            max_bootstrapped_demos: Maximum bootstrapped demonstrations
            max_labeled_demos: Maximum labeled demonstrations

        Returns:
            Optimized DSPy program
        """
        from dspy.teleprompt import MIPROv2

        from ...llm.fleet_config import build_lm_for_task, load_fleet_config
        from .skill_creator import SkillCreationProgram

        # Build LM for this context (don't use global configure)
        config = load_fleet_config(self.config_path)
        lm = build_lm_for_task(config, "skill_optimize")

        # Convert training examples to dspy.Example objects
        trainset = []
        for ex in training_examples:
            trainset.append(
                dspy.Example(
                    task_description=f"Create a skill based on: {ex['path']}",
                    skill_content=ex["content"],
                ).with_inputs("task_description")
            )

        if not trainset:
            raise ValueError("No valid training examples provided")

        # Use dspy.context() for async safety
        with dspy.context(lm=lm):
            # Create program to optimize
            program = SkillCreationProgram(quality_assured=True, hitl_enabled=False)

            # Create optimizer
            optimizer = MIPROv2(
                metric=skill_quality_metric,
                auto=auto,
                num_threads=self.optimization_config.get("miprov2", {}).get("num_threads", 4),
                verbose=self.optimization_config.get("miprov2", {}).get("verbose", True),
            )

            # Compile (optimize) the program
            optimized_program = optimizer.compile(
                program,
                trainset=trainset,
                max_bootstrapped_demos=max_bootstrapped_demos,
                max_labeled_demos=max_labeled_demos,
            )

        logger.info("MIPROv2 optimization complete (async-safe)")
        return optimized_program

    def optimize_with_bootstrap(
        self,
        training_examples: list[dict[str, str]],
        max_bootstrapped_demos: int = 4,
        max_labeled_demos: int = 4,
    ) -> dspy.Module:
        """Optimize using BootstrapFewShot with training examples from API.

        This method is designed for use from async contexts (e.g., FastAPI background tasks).
        It uses dspy.context() to avoid async configuration issues.

        Args:
            training_examples: List of dicts with 'path' and 'content' keys
            max_bootstrapped_demos: Maximum bootstrapped demonstrations
            max_labeled_demos: Maximum labeled demonstrations

        Returns:
            Optimized DSPy program
        """
        from dspy.teleprompt import BootstrapFewShot

        from ...llm.fleet_config import build_lm_for_task, load_fleet_config
        from .skill_creator import SkillCreationProgram

        # Build LM for this context (don't use global configure)
        config = load_fleet_config(self.config_path)
        lm = build_lm_for_task(config, "skill_optimize")

        # Convert training examples to dspy.Example objects
        trainset = []
        for ex in training_examples:
            trainset.append(
                dspy.Example(
                    task_description=f"Create a skill based on: {ex['path']}",
                    skill_content=ex["content"],
                ).with_inputs("task_description")
            )

        if not trainset:
            raise ValueError("No valid training examples provided")

        # Use dspy.context() for async safety
        with dspy.context(lm=lm):
            # Create program to optimize
            program = SkillCreationProgram(quality_assured=True, hitl_enabled=False)

            # Get config
            bs_config = self._get_optimizer_config("bootstrap_fewshot")

            # Create optimizer
            optimizer = BootstrapFewShot(
                metric=skill_quality_metric,
                max_bootstrapped_demos=max_bootstrapped_demos,
                max_labeled_demos=max_labeled_demos,
                max_rounds=bs_config.get("max_rounds", 1),
                max_errors=bs_config.get("max_errors", 5),
            )

            # Compile (optimize) the program
            optimized_program = optimizer.compile(program, trainset=trainset)

        logger.info("BootstrapFewShot optimization complete (async-safe)")
        return optimized_program

    def list_optimized_programs(self) -> list[dict[str, Any]]:
        """List all saved optimized programs.

        Returns:
            List of program metadata dictionaries
        """
        programs: list[dict[str, Any]] = []

        if not self.optimized_dir.exists():
            return programs

        for program_dir in self.optimized_dir.iterdir():
            if program_dir.is_dir():
                metadata_file = program_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = json.load(f)
                        metadata["path"] = str(program_dir)
                        programs.append(metadata)
                else:
                    programs.append(
                        {
                            "name": program_dir.name,
                            "path": str(program_dir),
                        }
                    )

        return programs


def run_optimization(
    program: dspy.Module | None = None,
    optimizer_type: OptimizerType | None = None,
    save_program: bool = True,
    program_name: str | None = None,
    verbose: bool = True,
) -> tuple[dspy.Module, OptimizationResult]:
    """Run optimization on a skill creation program.

    This is a convenience function for running optimization from CLI or scripts.

    Args:
        program: Program to optimize (default: SkillCreationProgram)
        optimizer_type: Type of optimizer to use
        save_program: Whether to save the optimized program
        program_name: Name for saved program
        verbose: Whether to print results

    Returns:
        Tuple of (optimized_program, optimization_result)
    """
    # Import here to avoid circular imports
    if program is None:
        from .skill_creator import SkillCreationProgram

        program = SkillCreationProgram(quality_assured=True, hitl_enabled=False)

    optimizer = SkillOptimizer()
    optimized_program, result = optimizer.optimize_and_evaluate(
        program=program,
        optimizer_type=optimizer_type,
        save_program=save_program,
        program_name=program_name,
    )

    if verbose:
        print(result.summary())

    return optimized_program, result


__all__ = [
    "OptimizationResult",
    "OptimizerType",
    "SkillOptimizer",
    "run_optimization",
]
