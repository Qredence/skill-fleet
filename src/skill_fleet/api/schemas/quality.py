"""Pydantic schemas for quality assurance API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ValidateRequest(BaseModel):
    """Request body for validating a skill or content."""

    skill_id: str | None = Field(
        default=None, description="Skill ID (optional if content provided)"
    )
    content: str | None = Field(
        default=None, description="Content to validate (optional if skill_id provided)"
    )
    validation_type: str = Field(
        default="skill", description="Type of validation: skill, content, or section"
    )


class ValidateResponse(BaseModel):
    """Response model for validation."""

    passed: bool
    status: str
    score: float
    issues: list[dict[str, Any]]
    recommendations: list[str]


class AssessQualityRequest(BaseModel):
    """Request body for assessing content quality."""

    skill_id: str | None = Field(
        default=None, description="Skill ID (optional if content provided)"
    )
    content: str | None = Field(
        default=None, description="Content to assess (optional if skill_id provided)"
    )
    criteria: list[str] = Field(
        default_factory=list, description="Specific quality criteria to assess"
    )


class AssessQualityResponse(BaseModel):
    """Response model for quality assessment."""

    overall_score: float
    dimensions: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]


class AutoFixRequest(BaseModel):
    """Request body for auto-fixing issues."""

    skill_id: str | None = Field(
        default=None, description="Skill ID (optional if content provided)"
    )
    content: str | None = Field(
        default=None, description="Content to fix (optional if skill_id provided)"
    )
    issues: list[dict[str, Any]] = Field(..., description="Issues to fix")


class AutoFixResponse(BaseModel):
    """Response model for auto-fix."""

    fixed_content: str
    fixes_applied: list[dict[str, Any]]
    remaining_issues: list[dict[str, Any]]
    confidence: float
