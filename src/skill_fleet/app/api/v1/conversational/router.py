"""
Conversational interface routes for v1 API.

This module provides endpoints for chat and conversational interactions.
These routes use the conversational workflow orchestrator.

Endpoints:
    POST /api/v1/chat/message - Send a message in a conversation
    POST /api/v1/chat/session/{session_id} - Create or resume a session
    GET  /api/v1/chat/session/{session_id}/history - Get session history
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .....api.schemas.conversational import (
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
)
from .....workflows.conversational_interface.orchestrator import (
    ConversationalOrchestrator,
    ConversationContext,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session storage (TODO: Replace with Redis for production)
_sessions: dict[str, ConversationContext] = {}

if TYPE_CHECKING:
    from .....workflows.conversational_interface.orchestrator import ConversationalOrchestrator


def _generate_message_id() -> str:
    """Generate a unique message ID."""
    import uuid
    return f"msg-{uuid.uuid4().hex[:8]}"


def _get_or_create_session(session_id: str) -> ConversationContext:
    """
    Get existing session or create a new one.

    Args:
        session_id: Session identifier

    Returns:
        ConversationContext for the session

    """
    orchestrator = ConversationalOrchestrator()

    if session_id in _sessions:
        return _sessions[session_id]

    # Create new session
    context = orchestrator.initialize_conversation_sync(
        initial_message="",
        metadata={"created_at": datetime.now(UTC).isoformat()},
        enable_mlflow=False,
    )
    _sessions[session_id] = context

    logger.info(f"Created new conversation session: {session_id}")
    return context


@router.post("/message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    """
    Send a message in a conversation.

    Args:
        request: Message request with session_id, message, and user_id

    Returns:
        SendMessageResponse: Response with session_id, message_id, response text, and context

    Raises:
        HTTPException: If message processing fails

    """
    orchestrator = ConversationalOrchestrator()

    # Generate or use provided session_id
    session_id = request.session_id
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())[:12]

    # Get or create session context
    context = _get_or_create_session(session_id)

    # Add user message to context
    from .....workflows.conversational_interface.orchestrator import ConversationMessage

    user_message = ConversationMessage(
        role="user",
        content=request.message,
        metadata={"user_id": request.user_id},
    )
    context.messages.append(user_message)

    try:
        # Interpret user intent
        intent_result = await orchestrator.interpret_intent(
            user_message=request.message,
            context=context,
            enable_mlflow=False,
        )

        intent_type = intent_result.get("intent_type", "unknown")
        updated_state = intent_result.get("updated_state", context.state.value)

        # Generate response based on intent
        response_text = ""
        context_metadata = {}

        if intent_type == "create_skill":
            # Move to deep understanding
            understanding_result = await orchestrator.deep_understanding(
                context=context,
                enable_mlflow=False,
            )

            context.current_understanding = understanding_result.get("enhanced_understanding", "")

            # Generate confirmation
            confirmation_result = await orchestrator.confirm_understanding(
                context=context,
                enable_mlflow=False,
            )

            response_text = confirmation_result.get("confirmation_summary", "")
            context_metadata["confirmation_completeness"] = confirmation_result.get("completeness_score", 0.0)

            # Update state
            context.state = context.CONFIRMING_UNDERSTANDING

        elif intent_type == "clarify":
            # Generate clarifying question
            question_result = await orchestrator.generate_clarifying_question(
                context=context,
                enable_mlflow=False,
            )

            response_text = question_result.get("question", "Could you please provide more details?")
            context_metadata["question_options"] = question_result.get("question_options", [])

        elif intent_type == "refine":
            response_text = "I understand you want to refine the skill. Please provide the skill content and your feedback."
            context.state = context.COLLECTING_FEEDBACK

        elif intent_type == "multi_skill":
            response_text = "I see you want to create multiple skills. Let's work on them one at a time. Which would you like to start with?"
        else:
            response_text = "I understand. How can I help you create or improve a skill today?"

        # Add assistant response to context
        assistant_message = ConversationMessage(
            role="assistant",
            content=response_text,
            metadata={
                "message_id": _generate_message_id(),
                "intent_type": intent_type,
                "state": updated_state,
                **context_metadata,
            },
        )
        context.messages.append(assistant_message)

        # Update session in storage
        _sessions[session_id] = context

        return SendMessageResponse(
            session_id=session_id,
            message_id=assistant_message.metadata.get("message_id", ""),
            response=response_text,
            context={
                "state": updated_state,
                "intent_type": intent_type,
                "message_count": len(context.messages),
                **context_metadata,
            },
        )

    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {e}"
        ) from e


@router.post("/session/{session_id}", response_model=dict[str, str])
async def create_session(session_id: str) -> dict[str, str]:
    """
    Create or resume a conversation session.

    Args:
        session_id: Unique session identifier

    Returns:
        Dictionary with session_id and status

    Raises:
        HTTPException: If session creation fails

    """
    try:
        context = _get_or_create_session(session_id)

        return {
            "session_id": session_id,
            "status": "active" if context else "new",
            "state": context.state.value if context else "initializing",
            "message_count": len(context.messages) if context else 0,
        }

    except Exception as e:
        logger.exception(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {e}"
        ) from e


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str) -> SessionHistoryResponse:
    """
    Get the history of a conversation session.

    Args:
        session_id: Unique session identifier

    Returns:
        SessionHistoryResponse: Session history with messages and metadata

    Raises:
        HTTPException: If session not found (404)

    """
    if session_id not in _sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Session not found: {session_id}"
        )

    context = _sessions[session_id]

    # Convert messages to dict format for API response
    messages = []
    for msg in context.messages:
        messages.append({
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "metadata": msg.metadata,
        })

    # Build metadata
    metadata = {
        "state": context.state.value,
        "message_count": len(context.messages),
        "created_at": context.created_at,
        "has_understanding": bool(context.current_understanding),
        "examples_count": len(context.collected_examples),
        **context.metadata,
    }

    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        metadata=metadata,
    )


# Additional endpoint for listing sessions
@router.get("/sessions", response_model=dict[str, Any])
async def list_sessions() -> dict[str, Any]:
    """
    List all active conversation sessions.

    Returns:
        Dictionary with session count and session summaries

    """
    sessions = []
    for session_id, context in _sessions.items():
        sessions.append({
            "session_id": session_id,
            "state": context.state.value,
            "message_count": len(context.messages),
            "created_at": context.created_at,
            "last_activity": context.messages[-1].timestamp if context.messages else context.created_at,
        })

    return {
        "count": len(sessions),
        "sessions": sessions,
    }
