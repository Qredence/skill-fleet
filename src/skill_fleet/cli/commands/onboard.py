"""CLI command for interactive user onboarding."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from ...common.paths import (
    default_profiles_path,
    default_skills_root,
    ensure_skills_root_initialized,
)
from ...core.creator import TaxonomySkillCreator
from ...onboarding.bootstrap import SkillBootstrapper
from ...taxonomy.manager import TaxonomyManager
from ..onboarding_cli import collect_onboarding_responses

console = Console()


def onboard_command(
    user_id: str = typer.Option(..., "--user-id", help="Unique user identifier"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    profiles_path: str = typer.Option(
        str(default_profiles_path()), "--profiles-path", help="Path to bootstrap profiles JSON"
    ),
):
    """Interactive onboarding workflow for new users.

    Guides users through setting up their personalized skill set by:
    - Collecting user preferences and context
    - Loading bootstrap profiles for role-based initialization
    - Creating initial skills based on user needs
    - Saving user configuration for future sessions

    Args:
        user_id: Unique identifier for the user
        skills_root: Root directory for the skills taxonomy
        profiles_path: Path to JSON file containing bootstrap profiles
    """
    console.print("\n[bold cyan]Welcome to the Agentic Skills System![/bold cyan]\n")
    console.print("Let's set up your personalized skill set.\n")

    skills_root_path = ensure_skills_root_initialized(Path(skills_root))
    taxonomy = TaxonomyManager(skills_root_path)
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)
    bootstrapper = SkillBootstrapper(
        taxonomy_manager=taxonomy, skill_creator=creator, profiles_path=Path(profiles_path)
    )

    responses = collect_onboarding_responses()

    console.print("\n[bold green]Setting up your skills...[/bold green]\n")

    with Progress() as progress:
        task = progress.add_task("[cyan]Bootstrapping skills...", total=100)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        user_profile = loop.run_until_complete(bootstrapper.onboard_user(user_id, responses))

        progress.update(task, completed=100)

    console.print("\n[bold green]✓ Onboarding complete![/bold green]\n")
    console.print(f"Profile: {user_profile['profile']['primaryRole']}")
    console.print(f"Mounted Skills: {len(user_profile['mounted_skills'])}")
    console.print(f"On-Demand Skills: {len(user_profile['on_demand_skills'])}")

    console.print("\n[bold]You're ready to start![/bold]")
    console.print('Try: uv run skill-fleet create "your task here"')
