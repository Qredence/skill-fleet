"""Pydantic schemas for skill-related API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SkillListItem(BaseModel):
    """Brief information about a skill for list endpoints."""

    skill_id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="Skill description")


class CreateSkillRequest(BaseModel):
    """Request body for creating a new skill."""

    task_description: str = Field(
        ...,
        description="Description of the skill to create",
        min_length=10,
    )
    user_id: str = Field(default="default", description="User ID for context")
    enable_hitl_confirm: bool = Field(
        default=False,
        description="Enable AI recap + confirm/revise/cancel step after understanding/planning",
    )
    enable_hitl_preview: bool = Field(
        default=False,
        description="Enable preview + proceed/refine/cancel step after generation",
    )
    enable_hitl_review: bool = Field(
        default=False,
        description="Enable validation review + proceed/refine/cancel step after validation",
    )
    enable_token_streaming: bool = Field(
        default=False,
        description="Enable token-level streaming during generation (emits token_stream events)",
    )
    auto_save_draft_on_preview_confirm: bool = Field(
        default=False,
        description="If preview is confirmed, automatically save the final skill into the draft area",
    )


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


class ValidateSkillRequest(BaseModel):
    """Request body for validating a skill."""

    skill_path: str = Field(
        ...,
        description="Taxonomy-relative path to skill (e.g., 'dspy-basics' or '_drafts/job-123/my-skill')",
    )
    use_llm: bool = Field(
        default=True,
        description="Enable LLM-based validation (requires API keys)",
    )


class ValidateSkillResponse(BaseModel):
    """Response model for skill validation."""

    passed: bool = Field(description="Whether all validation checks passed")
    status: str = Field(description="Overall validation status (passed, warnings, failed)")
    score: float = Field(description="Overall quality score (0.0-1.0)")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    checks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed validation checks performed",
    )


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


class UpdateSkillResponse(BaseModel):
    """Response model for skill update."""

    skill_id: str = Field(..., description="Unique skill identifier")
    status: str = Field(..., description="Update status (e.g., 'updated')")
