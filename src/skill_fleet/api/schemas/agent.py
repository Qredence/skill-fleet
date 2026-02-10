"""Schemas for ReAct agent API endpoints."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AgentWorkflowIntent = Literal[
    "start_skill_creation",
    "check_status",
    "submit_hitl",
    "promote_draft",
    "chat",
]


class AgentUIAction(BaseModel):
    """Optional UI-driven action to disambiguate user intent."""

    type: str = Field(..., description="Action type from the frontend")
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Action payload with type-specific fields",
    )


class AgentMessageRequest(BaseModel):
    """Request model for ReAct agent messages."""

    message: str = Field(..., description="User prompt for the ReAct agent")
    session_id: str | None = Field(default=None, description="Conversation session ID")
    user_id: str = Field(default="default", description="User ID for contextualization")
    context: dict[str, Any] | None = Field(
        default=None,
        description="Optional UI/runtime context",
    )
    active_job_id: str | None = Field(
        default=None,
        description="Active workflow job ID from the UI session",
    )
    workflow_intent: AgentWorkflowIntent | None = Field(
        default=None,
        description="Optional explicit workflow intent from the UI",
    )
    ui_action: AgentUIAction | None = Field(
        default=None,
        description="Optional structured action payload from UI controls",
    )
    stream: bool = Field(default=False, description="Whether streaming is requested")


class AgentMessageResponse(BaseModel):
    """Response model for ReAct agent message endpoint."""

    response: str
    reasoning: str | None = None
    suggested_actions: list[str] | None = None
    session_id: str
    active_job_id: str | None = None
    phase: str | None = None
    awaiting_hitl: bool = False
    hitl_type: str | None = None
    job_status: str | None = None
    next_step: dict[str, Any] | None = None
    recommended_ui_actions: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
