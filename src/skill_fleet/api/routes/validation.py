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

    skill_path = Path(path)
    if not skill_path.is_absolute():
        skill_path = skills_root / skill_path

    return validator.validate_complete(skill_path)
