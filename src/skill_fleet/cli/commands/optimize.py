"""CLI command for optimizing the workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Literal, cast

import click
import typer

from ...common.dspy_compat import coerce_reasoning_text

from ...core.dspy.optimization.selector import OptimizerContext, OptimizerSelector
from ...core.dspy.skill_creator import SkillCreationProgram
from ...core.optimization.optimizer import (
    APPROVED_MODELS,
    optimize_with_gepa,
    optimize_with_miprov2,
    optimize_with_tracking,
    quick_evaluate,
)


def optimize_command(
    optimizer: str = typer.Option(
        "miprov2",
        "--optimizer",
        help="Optimizer algorithm. Use --auto-select to auto-choose.",
        click_type=click.Choice(["miprov2", "gepa", "bootstrap_fewshot", "reflection_metrics"]),
    ),
    model: str = typer.Option(
        "gemini-3-flash-preview",
        "--model",
        help="LLM model to use (default: gemini-3-flash-preview)",
        click_type=click.Choice(
            [
                "gemini-3-flash-preview",
                "gemini-3-pro-preview",
                "deepseek-v3.2",
                "Nemotron-3-Nano-30B-A3B",
            ]
        ),
    ),
    trainset: str = typer.Option(
        str(
            Path(__file__).parent.parent.parent.parent.parent
            / "config"
            / "training"
            / "trainset.json"
        ),
        "--trainset",
        help="Path to training data JSON",
    ),
    output: str = typer.Option(
        str(Path(__file__).parent.parent.parent.parent.parent / "config" / "optimized"),
        "--output",
        help="Output directory for optimized program",
    ),
    auto: str = typer.Option(
        "medium",
        "--auto",
        help="Optimization intensity (default: medium)",
        click_type=click.Choice(["light", "medium", "heavy"]),
    ),
    track: bool = typer.Option(
        False, "--track", help="Enable MLflow tracking (requires mlflow>=2.21.1)"
    ),
    evaluate_only: bool = typer.Option(
        False, "--evaluate-only", help="Only run evaluation, don't optimize"
    ),
    n_examples: int | None = typer.Option(
        None,
        "--n-examples",
        help="Number of examples to evaluate (for --evaluate-only)",
    ),
    auto_select: bool = typer.Option(
        False,
        "--auto-select",
        help="Automatically select best optimizer based on trainset, budget, and task",
    ),
    budget: float = typer.Option(
        10.0,
        "--budget",
        help="Budget in USD for optimization (used with --auto-select)",
    ),
    quality_target: float = typer.Option(
        0.85,
        "--quality-target",
        help="Target quality score 0.0-1.0 (used with --auto-select)",
    ),
    time_limit: int | None = typer.Option(
        None,
        "--time-limit",
        help="Maximum time in minutes (used with --auto-select)",
    ),
) -> None:
    """Optimize the skill creation workflow using MIPROv2, GEPA, or auto-selected optimizer."""
    # Handle auto-selection
    if auto_select:
        optimizer, auto = _handle_auto_selection(
            trainset_path=trainset,
            budget=budget,
            quality_target=quality_target,
            time_limit=time_limit,
        )

    # Validate model
    if model not in APPROVED_MODELS:
        print(f"Error: Model '{model}' is not approved.", file=sys.stderr)
        print(f"Approved models: {list(APPROVED_MODELS.keys())}", file=sys.stderr)
        raise typer.Exit(code=2)

    print(f"\n{'=' * 60}")
    print("DSPy Workflow Optimization")
    print(f"{'=' * 60}")
    print(f"Optimizer: {optimizer}")
    print(f"Model: {model}")
    print(f"Trainset: {trainset}")
    print(f"Output: {output}")
    print(f"Intensity: {auto}")

    if evaluate_only:
        print("\n[EVALUATE ONLY MODE]\n")
        program = SkillCreationProgram()
        quick_evaluate(program, trainset, model, n_examples=n_examples)
        return

    if track:
        print("MLflow tracking: ENABLED")

    print(f"{'=' * 60}\n")

    # Create program
    program = SkillCreationProgram()

    # Run optimization
    try:
        if track:
            optimize_with_tracking(
                program,
                trainset_path=trainset,
                output_path=output,
                optimizer_type=cast("Literal['miprov2', 'gepa']", optimizer),
                model=model,
                auto=cast("Literal['light', 'medium', 'heavy']", auto),
            )
        elif optimizer == "miprov2":
            optimize_with_miprov2(
                program,
                trainset_path=trainset,
                output_path=output,
                model=model,
                auto=cast("Literal['light', 'medium', 'heavy']", auto),
            )
        else:
            optimize_with_gepa(
                program,
                trainset_path=trainset,
                output_path=output,
                model=model,
                auto=cast("Literal['light', 'medium', 'heavy']", auto),
            )

        print(f"\n[SUCCESS] Optimized program saved to: {output}")

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Make sure the trainset file exists.", file=sys.stderr)
        raise typer.Exit(code=2) from e
    except Exception as e:
        print(f"\nError during optimization: {e}", file=sys.stderr)
        raise typer.Exit(code=1) from e


def _handle_auto_selection(
    trainset_path: str,
    budget: float,
    quality_target: float,
    time_limit: int | None,
) -> tuple[str, str]:
    """
    Handle auto-selection of optimizer.

    Returns:
        Tuple of (optimizer_name, auto_setting)
    """
    from ...config.training.manager import TrainingDataManager

    # Use TrainingDataManager to get size
    path = Path(trainset_path)
    if not path.exists():
        print(f"Error: Trainset not found: {trainset_path}", file=sys.stderr)
        raise typer.Exit(code=2)

    try:
        manager = TrainingDataManager(path.parent)
        examples = manager.get_trainset()
        trainset_size = len(examples) if examples else 0

        # Fallback to file reading if manager returns empty but file exists
        if trainset_size == 0 and path.exists():
            with open(path) as f:
                trainset_data = json.load(f)
                if isinstance(trainset_data, dict) and "examples" in trainset_data:
                    trainset_size = len(trainset_data["examples"])
                elif isinstance(trainset_data, list):
                    trainset_size = len(trainset_data)
                else:
                    trainset_size = 50
    except Exception:
        # Fallback logic
        with open(path) as f:
            trainset_data = json.load(f)
            if isinstance(trainset_data, dict) and "examples" in trainset_data:
                trainset_size = len(trainset_data["examples"])
            elif isinstance(trainset_data, list):
                trainset_size = len(trainset_data)
            else:
                trainset_size = 50

    # Create context
    context = OptimizerContext(
        trainset_size=trainset_size,
        budget_dollars=budget,
        quality_target=quality_target,
        time_constraint_minutes=time_limit,
    )

    # Get recommendation
    selector = OptimizerSelector()
    recommendation = selector.recommend(context)

    # Display recommendation
    print(f"\n{'=' * 60}")
    print("🤖 Optimizer Auto-Selection")
    print(f"{'=' * 60}")
    print(f"Trainset size: {trainset_size}")
    print(f"Budget: ${budget:.2f}")
    print(f"Quality target: {quality_target}")
    if time_limit:
        print(f"Time limit: {time_limit} min")

    print(f"\n✅ Recommended: {recommendation.recommended.value}")
    print(f"   Config: auto={recommendation.config.auto}")
    print(f"   Estimated cost: ${recommendation.estimated_cost:.2f}")
    print(f"   Estimated time: {recommendation.estimated_time_minutes} minutes")
    print(f"   Confidence: {recommendation.confidence:.0%}")
    print(f"\n📝 Reasoning: {coerce_reasoning_text(recommendation.reasoning)}")

    if recommendation.alternatives:
        print("\n🔄 Alternatives:")
        for alt in recommendation.alternatives:
            risk = alt.get("quality_risk", "N/A")
            risk_str = f"{risk:+.0%}" if isinstance(risk, float) else str(risk)
            print(f"   - {alt['optimizer']}: {alt['cost']} | {alt['time']} | Risk: {risk_str}")

    print(f"{'=' * 60}\n")

    # Ask for confirmation
    confirm = typer.confirm("Proceed with recommended optimizer?", default=True)
    if not confirm:
        # Let user override
        override = typer.prompt(
            "Enter optimizer to use",
            default=recommendation.recommended.value,
        )
        auto_override = typer.prompt(
            "Enter auto setting",
            default=recommendation.config.auto,
        )
        return override, auto_override

    return recommendation.recommended.value, recommendation.config.auto
