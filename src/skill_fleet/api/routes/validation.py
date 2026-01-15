"""Validation routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...validators.skill_validator import SkillValidator
from ..dependencies import SkillsRoot

router = APIRouter()


class ValidateSkillRequest(BaseModel):
    """Request body for validating a skill."""

    path: str = Field(..., description="Taxonomy-relative path to the skill")


class ValidationCheck(BaseModel):
    """Result of a single validation check."""

    name: str
    status: str  # "pass", "fail", "warn"
    messages: list[str] = Field(default_factory=list)


class ValidationResponse(BaseModel):
    """Response model for skill validation."""

    passed: bool
    checks: list[ValidationCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


@router.post("/validate", response_model=ValidationResponse)
async def validate_skill(
    request: ValidateSkillRequest,
    skills_root: SkillsRoot,
) -> ValidationResponse:
    """Validate a skill at the specified path.

    Performs comprehensive validation including:
    - Metadata validation (required fields, formats)
    - Directory structure validation
    - Documentation validation (SKILL.md)
    - Frontmatter validation (agentskills.io compliance)
    - Examples validation
    - Naming conventions validation
    """
    path = request.path
    if not path:
        raise HTTPException(status_code=400, detail="path is required")

    validator = SkillValidator(skills_root)

    # Validate and resolve the user-provided reference string (no traversal/escape).
    try:
        candidate_path = validator.resolve_skill_ref(path)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid path") from err

    result = validator.validate_complete(candidate_path)

    # Convert raw dict to response model
    checks = [
        ValidationCheck(
            name=check.get("name", "unknown"),
            status=check.get("status", "fail"),
            messages=check.get("messages", []),
        )
        for check in result.get("checks", [])
    ]

    return ValidationResponse(
        passed=result.get("passed", False),
        checks=checks,
        warnings=result.get("warnings", []),
        errors=result.get("errors", []),
    )
