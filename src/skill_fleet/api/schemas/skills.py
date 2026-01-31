"""Pydantic schemas for skill-related API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateSkillRequest(BaseModel):
    """Request body for creating a new skill."""

    task_description: str = Field(
        ...,
        description="Description of the skill to create",
        min_length=10,
    )
    user_id: str = Field(default="default", description="User ID for context")


class CreateSkillResponse(BaseModel):
    """Response model for skill creation."""

    job_id: str = Field(..., description="Unique identifier for the background job")
    status: str = Field(default="pending", description="Initial job status")


class SkillDetailResponse(BaseModel):
    """Detailed information about a skill."""

    skill_id: str
    name: str
    description: str
    version: str
    type: str
    metadata: dict[str, Any]
    content: str | None = None


class ValidateSkillResponse(BaseModel):
    """Response model for skill validation."""

    passed: bool
    status: str
    score: float
    issues: list[dict[str, Any]]


class RefineSkillRequest(BaseModel):
    """Request body for refining a skill."""

    feedback: str = Field(..., description="User feedback for refinement")
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Optional focus areas (e.g., examples, clarity, structure)",
    )
    user_id: str = Field(default="default", description="User ID for context")


class RefineSkillResponse(BaseModel):
    """Response model for skill refinement."""

    job_id: str
    status: str
    message: str
