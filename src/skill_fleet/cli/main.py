"""Compatibility CLI entrypoints used by tests and scripts.

Provides simple, programmatic `create_skill(args)` and `validate_skill(args)`
functions that wrap existing library components. The implementations are
intentionally small and easy to patch in unit tests.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.creator import TaxonomySkillCreator
from ..llm.dspy_config import configure_dspy
from ..llm.fleet_config import load_fleet_config
from ..taxonomy.manager import TaxonomyManager
from ..validators.skill_validator import SkillValidator


def create_skill(args: Any) -> int:
    """Programmatic entrypoint for creating a skill.

    Args is an object with attributes used by the tests:
    - task: str
    - auto_approve: bool
    - config: str (path to fleet config)
    - skills_root: str
    - max_iterations, feedback_type, etc. are accepted but optional
    """
    # Load fleet config (tests patch this)
    config_path = Path(args.config) if getattr(args, "config", None) else None
    config = load_fleet_config(config_path) if config_path else {}

    # Configure DSPy (tests patch configure_dspy)
    configure_dspy(config)

    # Taxonomy manager
    skills_root = Path(getattr(args, "skills_root", "./skills"))
    taxonomy = TaxonomyManager(skills_root)

    # Creator
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy)

    # Call the creator with a simple contract; tests mock the creator
    task = getattr(args, "task", "")
    result = creator(task)

    status = (result or {}).get("status")
    if status in {"approved", "exists", "completed"}:
        return 0
    return 2


def validate_skill(args: Any) -> int:
    """Programmatic entrypoint for validating a skill directory.

    Args must provide:
    - skill_path: str
    - skills_root: str
    """
    skills_root = Path(args.skills_root) if hasattr(args, "skills_root") else Path("./skills")
    validator = SkillValidator(skills_root)

    skill_path = args.skill_path if hasattr(args, "skill_path") else ""
    raw = Path(skill_path)

    # Maintain compatibility with existing tests and scripts: call validate_complete,
    # but ensure the final path cannot escape skills_root.
    if raw.is_absolute():
        try:
            rel = raw.resolve().relative_to(skills_root.resolve())
        except ValueError:
            result = {"passed": False}
        else:
            try:
                candidate = validator.resolve_skill_ref(rel.as_posix())
            except ValueError:
                result = {"passed": False}
            else:
                result = validator.validate_complete(candidate)
        passed = bool(result.get("passed"))
        return 0 if passed else 2

    candidate = raw
    try:
        candidate_path = validator.resolve_skill_ref(candidate.as_posix())
    except ValueError:
        result = {"passed": False}
    else:
        result = validator.validate_complete(candidate_path)
    passed = bool(result.get("passed"))
    return 0 if passed else 2


__all__ = ["create_skill", "validate_skill"]
