"""Validation routes."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ...validators.skill_validator import SkillValidator

router = APIRouter()


@router.post("/validate")
async def validate_skill(request: dict):
    """Validate a skill at the specified path."""
    path = request.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="path is required")

    skills_root = Path(os.environ.get("SKILL_FLEET_SKILLS_ROOT", "skills"))
    validator = SkillValidator(skills_root)

    # Normalize and constrain the requested path to the skills_root directory
    skills_root_resolved = skills_root.resolve()
    relative_path = Path(path)
    # Disallow absolute paths from the request
    if relative_path.is_absolute():
        raise HTTPException(status_code=400, detail="Invalid path")
    candidate_path = (skills_root_resolved / relative_path).resolve()
    try:
        # Ensure the candidate_path is within the skills_root directory
        candidate_path.relative_to(skills_root_resolved)
    except ValueError as err:
        # Chain the original ValueError to distinguish this HTTPException from
        # errors raised while handling the exception (satisfies ruff B904)
        raise HTTPException(status_code=400, detail="Invalid path") from err

    return validator.validate_complete(candidate_path)
