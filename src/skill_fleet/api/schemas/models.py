"""Pydantic schemas for API models.

Following FastAPI best practices and codebase patterns (see core/models.py),
all Pydantic models for request/response validation are defined in this module.
This keeps models separate from business logic and route handlers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from ...core.models import ChecklistState


class TDDWorkflowState(BaseModel):
    """TDD workflow state for job tracking."""

    phase: str | None = None  # "red", "green", "refactor", "complete"
    checklist: ChecklistState = Field(default_factory=ChecklistState)
    baseline_tests_run: bool = False
    compliance_tests_run: bool = False
    rationalizations_identified: list[str] = Field(default_factory=list)


class DeepUnderstandingState(BaseModel):
    """Deep understanding phase state."""

    questions_asked: list[dict[str, Any]] = Field(default_factory=list)
    answers: list[dict[str, Any]] = Field(default_factory=list)
    research_performed: list[dict[str, Any]] = Field(default_factory=list)
    understanding_summary: str = ""
    user_problem: str = ""
    user_goals: list[str] = Field(default_factory=list)
    readiness_score: float = 0.0
    complete: bool = False


class JobState(BaseModel):
    """Represents the current state of a background job."""

    job_id: str
    status: str = "pending"  # pending, running, pending_hitl, completed, failed
    hitl_type: str | None = None
    hitl_data: dict[str, Any] | None = None
    hitl_response: dict[str, Any] | None = None
    result: Any | None = None
    error: str | None = None
    saved_path: str | None = None  # Path where skill was saved

    # Enhanced features from ConversationalSkillAgent
    tdd_workflow: TDDWorkflowState = Field(default_factory=TDDWorkflowState)
    deep_understanding: DeepUnderstandingState = Field(
        default_factory=DeepUnderstandingState
    )
    multi_skill_queue: list[str] = Field(default_factory=list)
    current_skill_index: int = 0
    task_description_refined: str = ""

    # Session persistence
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # User context
    user_id: str = "default"
    user_context: dict[str, Any] = Field(default_factory=dict)
