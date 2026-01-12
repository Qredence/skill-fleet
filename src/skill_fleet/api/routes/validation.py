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
    candidate_path = (skills_root_resolved / path).resolve()
    try:
        # Ensure the candidate_path is within the skills_root directory
        candidate_path.relative_to(skills_root_resolved)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    return validator.validate_complete(candidate_path)
