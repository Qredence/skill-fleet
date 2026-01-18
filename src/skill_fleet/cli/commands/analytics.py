"""CLI command for showing skill usage analytics."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ...analytics.engine import AnalyticsEngine, RecommendationEngine
from ...common.paths import default_skills_root, ensure_skills_root_initialized
from ...taxonomy.manager import TaxonomyManager


def analytics_command(
    user_id: str = typer.Option("all", "--user-id", help="Filter by user ID or 'all'"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
):
    """Show skill usage analytics and recommendations."""
    skills_root_path = ensure_skills_root_initialized(Path(skills_root))
    taxonomy = TaxonomyManager(skills_root_path)
    analytics_file = skills_root_path / "_analytics" / "usage_log.jsonl"

    engine = AnalyticsEngine(analytics_file)
    stats = engine.analyze_usage(user_id if user_id != "all" else None)

    if json_output:
        print(json.dumps(stats, indent=2))
        return

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
    recommender = RecommendationEngine(engine, taxonomy)
    recs = recommender.recommend_skills(user_id if user_id != "all" else "default")

    if recs:
        console.print("[bold green]Recommendations:[/bold green]")
        for rec in recs:
            console.print(
                f"  • [cyan]{rec['skill_id']}[/cyan]: {rec['reason']} ([yellow]{rec['priority']}[/yellow])"
            )
    else:
        console.print("[italic]No recommendations at this time.[/italic]")
