"""
Compatibility CLI entrypoints used by tests and scripts.

Provides simple, programmatic `create_skill(args)` and `validate_skill(args)`
functions that wrap existing library components. The implementations are
intentionally small and easy to patch in unit tests.

.. deprecated::
    These entrypoints are temporarily unavailable during migration to
    new workflow architecture.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from ..validators.skill_validator import SkillValidator


def create_skill(args: Any) -> int:
    """
    Programmatic entrypoint for creating a skill.

    .. deprecated::
        This function is temporarily unavailable during migration to
        new workflow architecture.
    """
    print(
        "Error: The create_skill function is temporarily unavailable.",
        file=sys.stderr,
    )
    print(
        "The skill creation feature is being migrated to the new workflow architecture.",
        file=sys.stderr,
    )
    return 1


def validate_skill(args: Any) -> int:
    """
    Programmatic entrypoint for validating a skill directory.

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
