"""
CLI command for evaluating skill quality.

.. deprecated::
    This command is temporarily unavailable during migration to new workflow architecture.
"""

from __future__ import annotations

import sys

import typer


def evaluate_command(
    path: str = typer.Argument(
        ...,
        help="Path to skill directory or SKILL.md file to evaluate",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results as JSON",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed metrics breakdown",
    ),
):
    """
    Evaluate skill quality using calibrated metrics.

    .. deprecated::
        This command is temporarily unavailable during migration to new workflow architecture.
    """
    print(
        "Error: The evaluate command is temporarily unavailable.",
        file=sys.stderr,
    )
    print(
        "The skill evaluation feature is being migrated to the new workflow architecture.",
        file=sys.stderr,
    )
    raise typer.Exit(code=1)


def evaluate_batch_command(
    paths: list[str] = typer.Argument(
        ...,
        help="Paths to skill directories to evaluate",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output results as JSON",
    ),
):
    """
    Evaluate multiple skills and show summary statistics.

    .. deprecated::
        This command is temporarily unavailable during migration to new workflow architecture.
    """
    print(
        "Error: The evaluate-batch command is temporarily unavailable.",
        file=sys.stderr,
    )
    print(
        "The skill evaluation feature is being migrated to the new workflow architecture.",
        file=sys.stderr,
    )
    raise typer.Exit(code=1)
