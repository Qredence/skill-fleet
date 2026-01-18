"""CLI command for migrating skills to agentskills.io format."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ...common.migration import migrate_all_skills
from ...common.paths import default_skills_root, ensure_skills_root_initialized


def migrate_command(
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without writing"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
):
    """Migrate existing skills to agentskills.io format."""
    skills_root_path = ensure_skills_root_initialized(Path(skills_root))

    if json_output:
        # Quiet mode for JSON output
        result = migrate_all_skills(skills_root_path, dry_run=dry_run, verbose=False)
        print(json.dumps(result, indent=2))
        if result["failed"] > 0:
            raise typer.Exit(code=1)
        return

    print(f"\n{'=' * 60}")
    print("Migrating skills to agentskills.io format")
    print(f"Skills root: {skills_root_path}")
    if dry_run:
        print("[DRY RUN MODE - no changes will be written]")
    print(f"{'=' * 60}\n")

    result = migrate_all_skills(skills_root_path, dry_run=dry_run, verbose=True)

    if result["failed"] > 0:
        raise typer.Exit(code=1)
