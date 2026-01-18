"""CLI command for validating a skill's metadata and structure."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from ...common.paths import default_skills_root, ensure_skills_root_initialized
from ...validators import SkillValidator


def validate_command(
    skill_path: str = typer.Argument(..., help="Path to a skill directory or JSON file"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
):
    """Validate a skill's metadata and structure."""
    skills_root_path = ensure_skills_root_initialized(Path(skills_root))
    validator = SkillValidator(skills_root_path)

    # Treat user input as untrusted; normalize to a taxonomy-relative reference.
    raw = Path(skill_path)
    if raw.is_absolute():
        try:
            rel = raw.resolve().relative_to(skills_root_path.resolve())
        except ValueError:
            results = {
                "passed": False,
                "checks": [],
                "warnings": [],
                "errors": ["Invalid path"],
            }
        else:
            results = validator.validate_complete_ref(rel.as_posix())
    else:
        results = validator.validate_complete_ref(raw.as_posix())

    if json_output:
        print(json.dumps(results, indent=2))
        if not results.get("passed"):
            raise typer.Exit(code=2)
        return

    status = "passed" if results.get("passed") else "failed"
    print(f"validation: {status}")
    if results.get("errors"):
        print("errors:")
        for message in results["errors"]:
            print(f"- {message}")
    if results.get("warnings"):
        print("warnings:")
        for message in results["warnings"]:
            print(f"- {message}")

    if not results.get("passed"):
        raise typer.Exit(code=2)
