"""CLI command for optimizing the workflow."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import typer

from ...core.dspy.programs import SkillCreationProgram
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
        help="Optimizer algorithm (default: miprov2)",
        click_type=click.Choice(["miprov2", "gepa"]),
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
    n_examples: int = typer.Option(
        None,
        "--n-examples",
        help="Number of examples to evaluate (for --evaluate-only)",
    ),
):
    """Optimize the skill creation workflow using MIPROv2 or GEPA."""
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
                optimizer_type=optimizer,
                model=model,
                auto=auto,
            )
        elif optimizer == "miprov2":
            optimize_with_miprov2(
                program,
                trainset_path=trainset,
                output_path=output,
                model=model,
                auto=auto,
            )
        else:
            optimize_with_gepa(
                program,
                trainset_path=trainset,
                output_path=output,
                model=model,
                auto=auto,
            )

        print(f"\n[SUCCESS] Optimized program saved to: {output}")

    except FileNotFoundError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("Make sure the trainset file exists.", file=sys.stderr)
        raise typer.Exit(code=2) from e
    except Exception as e:
        print(f"\nError during optimization: {e}", file=sys.stderr)
        raise typer.Exit(code=1) from e
