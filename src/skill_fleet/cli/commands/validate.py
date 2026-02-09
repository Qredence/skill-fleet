"""CLI command for validating a skill's metadata and structure."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import cast

import typer

from ...common.paths import default_skills_root, ensure_skills_root_initialized
from ..client import SkillFleetClient


def validate_command(
    skill_path: str = typer.Argument(..., help="Path to a skill directory or JSON file"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
    use_llm: bool = typer.Option(
        True, "--use-llm/--no-llm", help="Enable LLM-based validation (requires API keys)"
    ),
    api_url: str = typer.Option(
        None,
        "--api-url",
        help="API server URL (default: SKILL_FLEET_API_URL env var or http://localhost:8000)",
    ),
):
    """Validate a skill's metadata and structure via API."""
    # Resolve API URL
    if api_url is None:
        api_url = os.getenv("SKILL_FLEET_API_URL", "http://localhost:8000")

    # Ensure skills root is initialized
    skills_root_path = ensure_skills_root_initialized(Path(skills_root))

    # Normalize skill path to taxonomy-relative reference
    raw = Path(skill_path)
    if raw.is_absolute():
        try:
            rel = raw.resolve().relative_to(skills_root_path.resolve())
            normalized_path = rel.as_posix()
        except ValueError:
            # Path is outside skills root
            typer.echo(
                f"Error: Skill path must be relative to skills root ({skills_root_path})",
                err=True,
            )
            raise typer.Exit(code=2) from None
    else:
        normalized_path = raw.as_posix()

    # Call API
    async def _validate():
        client = SkillFleetClient(base_url=api_url)
        try:
            return await client.validate_skill(skill_path=normalized_path, use_llm=use_llm)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from None
        except Exception as e:
            typer.echo(f"Validation failed: {e}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            await client.close()

    results = asyncio.run(_validate())

    # Output results
    if json_output:
        print(json.dumps(results, indent=2))
        if not results.get("passed"):
            raise typer.Exit(code=2)
        return

    # Human-readable output
    status = "passed" if results.get("passed") else "failed"
    score = results.get("score", 0.0)
    print(f"validation: {status} (score: {score:.2f})")

    errors = results.get("errors", [])
    if errors:
        print("errors:")
        for message in cast("list[str]", errors):
            print(f"  - {message}")

    warnings = results.get("warnings", [])
    if warnings:
        print("warnings:")
        for message in cast("list[str]", warnings):
            print(f"  - {message}")

    # Show detailed checks if available
    checks = results.get("checks", [])
    if checks and not json_output:
        print(f"\nchecks performed: {len(checks)}")

    if not results.get("passed"):
        raise typer.Exit(code=2)
