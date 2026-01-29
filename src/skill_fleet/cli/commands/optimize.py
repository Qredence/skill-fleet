"""
CLI command for optimizing the workflow.

.. deprecated::
    This command is temporarily unavailable during migration to new workflow architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import typer


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
    """
    Optimize the skill creation workflow using MIPROv2, GEPA, or auto-selected optimizer.

    .. deprecated::
        This command is temporarily unavailable during migration to new workflow architecture.
    """
    print(
        "Error: The optimize command is temporarily unavailable.",
        file=sys.stderr,
    )
    print(
        "The workflow optimization feature is being migrated to the new workflow architecture.",
        file=sys.stderr,
    )
    raise typer.Exit(code=1)
