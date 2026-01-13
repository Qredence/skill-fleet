"""Validation routes."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...validators.skill_validator import SkillValidator

router = APIRouter()


class ValidateSkillRequest(BaseModel):
    """Request body for validating a skill."""

    path: str


@router.post("/validate")
async def validate_skill(request: ValidateSkillRequest):
    """Validate a skill at the specified path."""
    path = request.path
    if not path:
        raise HTTPException(status_code=400, detail="path is required")

    # skills_root is configured server-side; request.path is untrusted.
    skills_root = Path(os.environ.get("SKILL_FLEET_SKILLS_ROOT", "skills"))
    validator = SkillValidator(skills_root)

    # Validate and resolve the user-provided reference string (no traversal/escape).
    try:
        candidate_path = validator.resolve_skill_ref(path)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid path") from err

    return validator.validate_complete(candidate_path)
