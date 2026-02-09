"""CLI command for showing skill usage analytics."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ...common.paths import default_skills_root, ensure_skills_root_initialized
from ..client import SkillFleetClient


def analytics_command(
    user_id: str = typer.Option("all", "--user-id", help="Filter by user ID or 'all'"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
    api_url: str = typer.Option(
        None,
        "--api-url",
        help="API server URL (default: SKILL_FLEET_API_URL env var or http://localhost:8000)",
    ),
):
    """Show skill usage analytics and recommendations via API."""
    # Resolve API URL
    if api_url is None:
        api_url = os.getenv("SKILL_FLEET_API_URL", "http://localhost:8000")

    # Ensure skills root is initialized
    _ = ensure_skills_root_initialized(Path(skills_root))

    # Normalize user_id
    user_filter = None if user_id == "all" else user_id
    rec_user_id = "default" if user_id == "all" else user_id

    # Call API
    async def _get_analytics():
        client = SkillFleetClient(base_url=api_url)
        try:
            stats = await client.get_analytics(user_id=user_filter)
            recs = await client.get_recommendations(user_id=rec_user_id)
            return stats, recs
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from None
        except Exception as e:
            typer.echo(f"Analytics request failed: {e}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            await client.close()

    stats, recs = asyncio.run(_get_analytics())

    # Output results
    if json_output:
        output = {"analytics": stats, "recommendations": recs}
        print(json.dumps(output, indent=2))
        return

    # Human-readable output
    console = Console()
    console.print(f"\n[bold cyan]Skill Usage Analytics[/bold cyan] (User: {user_id})\n")

    console.print(f"Total Events: {stats['total_events']}")
    console.print(f"Success Rate: {stats['success_rate']:.1%}")
    console.print(f"Unique Skills Used: {stats['unique_skills_used']}\n")

    if stats["most_used_skills"]:
        table = Table(title="Most Used Skills")
        table.add_column("Skill ID", style="cyan")
        table.add_column("Usage Count", style="magenta")
        for skill_id, count in stats["most_used_skills"]:
            table.add_row(skill_id, str(count))
        console.print(table)
        console.print()

    if stats["common_combinations"]:
        table = Table(title="Common Skill Combinations")
        table.add_column("Skills", style="cyan")
        table.add_column("Co-occurrence", style="magenta")
        for combo in stats["common_combinations"]:
            table.add_row(", ".join(combo["skills"]), str(combo["count"]))
        console.print(table)
        console.print()

    # Recommendations
    recommendations = recs.get("recommendations", [])
    if recommendations:
        console.print("[bold green]Recommendations:[/bold green]")
        for rec in recommendations:
            console.print(
                f"  • [cyan]{rec['skill_id']}[/cyan]: {rec['reason']} ([yellow]{rec['priority']}[/yellow])"
            )
    else:
        console.print("[italic]No recommendations at this time.[/italic]")
