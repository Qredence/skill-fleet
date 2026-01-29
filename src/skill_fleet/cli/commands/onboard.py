"""
CLI command for interactive user onboarding.

.. deprecated::
    This command is temporarily unavailable during migration to new workflow architecture.
"""

from __future__ import annotations

import sys

import typer


def onboard_command(
    user_id: str = typer.Option(..., "--user-id", help="Unique user identifier"),
    skills_root: str = typer.Option("./skills", "--skills-root", help="Skills taxonomy root"),
    profiles_path: str = typer.Option(
        "./profiles", "--profiles-path", help="Path to bootstrap profiles JSON"
    ),
):
    """
    Interactive onboarding workflow for new users.

    .. deprecated::
        This command is temporarily unavailable during migration to new workflow architecture.
    """
    print(
        "Error: The onboard command is temporarily unavailable.",
        file=sys.stderr,
    )
    print(
        "The onboarding feature is being migrated to the new workflow architecture.",
        file=sys.stderr,
    )
    raise typer.Exit(code=1)
