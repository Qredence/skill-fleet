"""CLI command for generating <available_skills> XML."""

from __future__ import annotations

from pathlib import Path

import typer

from ...common.paths import default_skills_root
from ...taxonomy.manager import TaxonomyManager


def generate_xml_command(
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    output: str = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
):
    """Generate <available_skills> XML for agent prompt injection."""
    taxonomy = TaxonomyManager(Path(skills_root))
    xml_content = taxonomy.generate_available_skills_xml()

    if output:
        Path(output).write_text(xml_content, encoding="utf-8")
        print(f"XML written to: {output}")
    else:
        print(xml_content)
