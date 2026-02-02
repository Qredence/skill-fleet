"""
Conversational interface routes for v1 API.

This module provides endpoints for chat and conversational interactions
using modern DSPy modules with streaming support.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from skill_fleet.dspy import dspy_context
from skill_fleet.dspy.streaming import stream_prediction
from skill_fleet.infrastructure.db.database import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as DbSession


logger = logging.getLogger(__name__)

router = APIRouter()

# Type alias for database dependency
DbSessionDep = Annotated["DbSession", Depends(get_db)]


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str
    reasoning: str | None = None
    suggested_actions: list[str] | None = None
    session_id: str
    metadata: dict[str, Any] | None = None


class SessionHistoryResponse(BaseModel):
    """Session history response model."""

    session_id: str
    messages: list[dict[str, Any]]


async def _process_chat_message(
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Process a chat message using DSPy modules.

    Args:
        message: User message
        context: Optional conversation context

    Returns:
        Dictionary with response, reasoning, and metadata

    """
    from skill_fleet.core.modules.conversational import ConversationalModule

    module = ConversationalModule()

    with dspy_context():
        result = await module.aforward(
            message=message,
            context=context or {},
        )

    return {
        "response": getattr(result, "response", ""),
        "reasoning": getattr(result, "reasoning", None),
        "suggested_actions": getattr(result, "suggested_actions", []),
        "metadata": getattr(result, "metadata", {}),
    }


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: DbSessionDep,
) -> ChatResponse:
    """
    Send a message and get a response.

    Args:
        request: Chat request with message and context
        db: Database session

    Returns:
        Chat response with AI-generated content

    """
    try:
        result = await _process_chat_message(
            message=request.message,
            context=request.context,
        )

        return ChatResponse(
            response=result["response"],
            reasoning=result.get("reasoning"),
            suggested_actions=result.get("suggested_actions"),
            session_id=request.session_id or "default",
            metadata=result.get("metadata"),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/session/{session_id}", response_model=dict[str, str])
async def create_session(
    session_id: str,
    db: DbSessionDep,
) -> dict[str, str]:
    """
    Create or resume a conversation session.

    Args:
        session_id: Unique session identifier
        db: Database session

    Returns:
        Session creation confirmation

    """
    # For now, just return success
    # TODO: Implement actual session persistence
    return {
        "session_id": session_id,
        "status": "created",
        "message": "Session created successfully",
    }


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    db: DbSessionDep,
) -> SessionHistoryResponse:
    """
    Get the history of a conversation session.

    Args:
        session_id: Session identifier
        db: Database session

    Returns:
        Session history with all messages

    """
    # For now, return empty history
    # TODO: Implement session history persistence
    return SessionHistoryResponse(
        session_id=session_id,
        messages=[],
    )


@router.get("/sessions", response_model=dict[str, Any])
async def list_sessions(
    db: DbSessionDep,
) -> dict[str, Any]:
    """
    List all active conversation sessions.

    Args:
        db: Database session

    Returns:
        List of active sessions

    """
    # For now, return empty list
    # TODO: Implement session listing
    return {
        "sessions": [],
        "total": 0,
    }


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    db: DbSessionDep,
) -> StreamingResponse:
    """
    Stream chat responses.

    Args:
        request: Chat request with message and context
        db: Database session

    Returns:
        Streaming response with SSE events

    """
    from skill_fleet.core.modules.conversational import ConversationalModule

    async def event_generator() -> AsyncIterator[str]:
        module = ConversationalModule()

        with dspy_context():
            async for event in stream_prediction(
                module,
                message=request.message,
                context=request.context or {},
            ):
                import json

                yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
