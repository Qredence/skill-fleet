"""Pydantic schemas for conversational interface API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    """Request body for sending a message in conversation."""

    session_id: str | None = Field(
        default=None, description="Session ID (optional for new sessions)"
    )
    message: str = Field(..., description="User message to send")
    user_id: str = Field(default="default", description="User ID for context")


class SendMessageResponse(BaseModel):
    """Response model for sending a message."""

    session_id: str
    message_id: str
    response: str
    context: dict[str, Any] | None = None


class SessionHistoryResponse(BaseModel):
    """Response model for retrieving session history."""

    session_id: str
    messages: list[dict[str, Any]]
    metadata: dict[str, Any]
