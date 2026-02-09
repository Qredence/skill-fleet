"""CLI command for generating <available_skills> XML."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer

from ...common.paths import default_skills_root, ensure_skills_root_initialized
from ..client import SkillFleetClient


def generate_xml_command(
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    output: str = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
    user_id: str = typer.Option(
        None, "--user-id", help="User ID for personalized taxonomy (filters mounted skills)"
    ),
    api_url: str = typer.Option(
        None,
        "--api-url",
        help="API server URL (default: SKILL_FLEET_API_URL env var or http://localhost:8000)",
    ),
):
    """Generate <available_skills> XML for agent prompt injection via API."""
    # Resolve API URL
    if api_url is None:
        api_url = os.getenv("SKILL_FLEET_API_URL", "http://localhost:8000")

    # Ensure skills root is initialized
    _ = ensure_skills_root_initialized(Path(skills_root))

    # Call API
    async def _generate():
        client = SkillFleetClient(base_url=api_url)
        try:
            return await client.generate_xml(user_id=user_id)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from None
        except Exception as e:
            typer.echo(f"XML generation failed: {e}", err=True)
            raise typer.Exit(code=1) from None
        finally:
            await client.close()

    xml_content = asyncio.run(_generate())

    # Output results
    if output:
        Path(output).write_text(xml_content, encoding="utf-8")
        typer.echo(f"XML written to: {output}")
    else:
        print(xml_content)
