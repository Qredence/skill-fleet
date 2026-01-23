"""Conversational interface routes for v1 API.

This module provides endpoints for chat and conversational interactions.
These routes use the conversational workflow orchestrator.

Endpoints:
    POST /api/v1/chat/message - Send a message in a conversation
    POST /api/v1/chat/session/{session_id} - Create or resume a session
    GET  /api/v1/chat/session/{session_id}/history - Get session history
"""

from __future__ import annotations

from fastapi import APIRouter

from ...schemas.conversational import (
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
)

router = APIRouter()


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    """
    Send a message in a conversation.

    Args:
        request: Message request with session_id, message, and user_id

    Returns:
        SendMessageResponse: Response with session_id, message_id, response text, and context

    Note:
        This is a placeholder. The full implementation should:
        - Use the conversational workflow orchestrator
        - Support session management
        - Return LLM responses
    """
    # TODO: Implement using workflows/conversational_interface/orchestrator.py
    return SendMessageResponse(
        session_id=request.session_id or "new-session",
        message_id="msg-123",
        response="This is a placeholder response. The full implementation will use the conversational workflow.",
        context={},
    )


@router.post("/session/{session_id}", response_model=dict[str, str])
async def create_session(session_id: str) -> dict[str, str]:
    """
    Create or resume a conversation session.

    Args:
        session_id: Unique session identifier

    Returns:
        Dictionary with session_id and status

    Note:
        This is a placeholder. The full implementation should:
        - Create or retrieve session state
        - Initialize conversation context
    """
    # TODO: Implement session management
    return {"session_id": session_id, "status": "active"}


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str) -> SessionHistoryResponse:
    """
    Get the history of a conversation session.

    Args:
        session_id: Unique session identifier

    Returns:
        SessionHistoryResponse: Session history with messages and metadata

    Note:
        This is a placeholder. The full implementation should:
        - Retrieve message history from session store
        - Return metadata about the session
    """
    # TODO: Implement session history retrieval
    return SessionHistoryResponse(
        session_id=session_id,
        messages=[],
        metadata={"created_at": "2024-01-23T00:00:00Z"},
    )
