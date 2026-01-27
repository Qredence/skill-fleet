"""
Conversational interface routes for v1 API.

This module provides endpoints for chat and conversational interactions.
These routes use the conversational workflow orchestrator with database-backed
session storage via ConversationSessionRepository.

Endpoints:
    POST /api/v1/chat/message - Send a message in a conversation
    POST /api/v1/chat/session/{session_id} - Create or resume a session
    GET  /api/v1/chat/session/{session_id}/history - Get session history
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from .....core.dspy.modules.workflows.conversational import (
    ConversationalOrchestrator,
    ConversationMessage,
    ConversationState,
)
from .....db.database import get_db
from .....db.models import ConversationStateEnum
from .....db.repositories import get_conversation_session_repository
from ...schemas.conversational import (
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session as DbSession

    from .....core.dspy.modules.workflows.conversational import (
        ConversationContext,
    )
    from .....db.models import ConversationSession
    from .....db.repositories import ConversationSessionRepository

logger = logging.getLogger(__name__)

router = APIRouter()

# Type alias for database dependency
DbSessionDep = Annotated["DbSession", Depends(get_db)]


def _generate_message_id() -> str:
    """Generate a unique message ID."""
    import uuid

    return f"msg-{uuid.uuid4().hex[:8]}"


def _db_session_to_context(
    db_session: ConversationSession,
    orchestrator: ConversationalOrchestrator,
) -> ConversationContext:
    """
    Convert a database session to a ConversationContext.

    Args:
        db_session: Database session model
        orchestrator: Orchestrator for context initialization

    Returns:
        ConversationContext populated from database

    """
    # Initialize a fresh context
    context = orchestrator.initialize_conversation_sync(
        initial_message="",
        metadata=db_session.session_metadata or {},
        enable_mlflow=False,
    )

    # Map database state to ConversationState enum
    state_mapping = {
        "EXPLORING": ConversationState.INTERPRETING_INTENT,
        "DEEP_UNDERSTANDING": ConversationState.DEEP_UNDERSTANDING,
        "CONFIRMING": ConversationState.CONFIRMING_UNDERSTANDING,
        "COLLECTING_FEEDBACK": ConversationState.COLLECTING_FEEDBACK,
        "TESTING": ConversationState.TESTING,
        "REVISING": ConversationState.REFINING,
        "COMPLETE": ConversationState.COMPLETED,
    }
    default_state = ConversationState.INTERPRETING_INTENT
    context.state = state_mapping.get(db_session.state, default_state)

    context.task_description = db_session.task_description or ""
    context.current_understanding = db_session.current_understanding or ""

    # Restore messages
    if db_session.messages:
        for msg_data in db_session.messages:
            context.messages.append(
                ConversationMessage(
                    role=msg_data.get("role", "user"),
                    content=msg_data.get("content", ""),
                    metadata=msg_data.get("metadata", {}),
                )
            )

    # Restore examples
    if db_session.collected_examples:
        context.collected_examples = list(db_session.collected_examples)

    return context


def _context_to_db_updates(context: ConversationContext) -> dict[str, Any]:
    """
    Extract database update fields from a ConversationContext.

    Args:
        context: The context to extract from

    Returns:
        Dict of field names to values

    """
    messages = []
    for msg in context.messages:
        messages.append(
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,  # Already a string
                "metadata": msg.metadata,
            }
        )

    return {
        "state": context.state.value if hasattr(context.state, "value") else str(context.state),
        "task_description": context.task_description or None,
        "current_understanding": context.current_understanding or None,
        "messages": messages,
        "collected_examples": context.collected_examples,
    }


def _get_or_create_session(
    session_id: str,
    repo: ConversationSessionRepository,
) -> ConversationSession:
    """
    Get existing session from database or create a new one.

    Args:
        session_id: Session identifier
        repo: Session repository

    Returns:
        ConversationSession from database

    """
    db_session = repo.get_by_id(session_id)
    if db_session:
        return db_session

    # Create new session in database
    db_session = repo.create(
        session_id=session_id,
        user_id="default",
        state=ConversationStateEnum.EXPLORING,
        metadata={"source": "api"},
    )

    logger.info(f"Created new conversation session: {session_id}")
    return db_session


@router.post("/message", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: DbSessionDep,
) -> SendMessageResponse:
    """
    Send a message in a conversation.

    Args:
        request: Message request with session_id, message, and user_id
        db: Database session (injected)

    Returns:
        SendMessageResponse: Response with session_id, message_id, response text, and context

    Raises:
        HTTPException: If message processing fails

    """
    orchestrator = ConversationalOrchestrator()
    repo = get_conversation_session_repository(db)

    # Generate or use provided session_id
    session_id = request.session_id
    if not session_id:
        import uuid

        session_id = str(uuid.uuid4())

    # Get or create session from database
    db_session = _get_or_create_session(session_id, repo)
    context = _db_session_to_context(db_session, orchestrator)

    # Add user message to context
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
            context_metadata["confirmation_completeness"] = confirmation_result.get(
                "completeness_score", 0.0
            )

            # Update state
            context.state = ConversationState.CONFIRMING_UNDERSTANDING

        elif intent_type == "clarify":
            # Generate clarifying question
            question_result = await orchestrator.generate_clarifying_question(
                context=context,
                enable_mlflow=False,
            )

            response_text = question_result.get(
                "question", "Could you please provide more details?"
            )
            context_metadata["question_options"] = question_result.get("question_options", [])

        elif intent_type == "refine":
            response_text = (
                "I understand you want to refine the skill. "
                "Please provide the skill content and your feedback."
            )
            context.state = ConversationState.COLLECTING_FEEDBACK

        elif intent_type == "multi_skill":
            response_text = (
                "I see you want to create multiple skills. "
                "Let's work on them one at a time. Which would you like to start with?"
            )
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

        # Persist updated context to database
        repo.update(db_session, **_context_to_db_updates(context))

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
        raise HTTPException(status_code=500, detail=f"Failed to process message: {e}") from e


@router.post("/session/{session_id}", response_model=dict[str, str])
async def create_session(
    session_id: str,
    db: DbSessionDep,
) -> dict[str, str]:
    """
    Create or resume a conversation session.

    Args:
        session_id: Unique session identifier
        db: Database session (injected)

    Returns:
        Dictionary with session_id and status

    Raises:
        HTTPException: If session creation fails

    """
    try:
        repo = get_conversation_session_repository(db)
        db_session = _get_or_create_session(session_id, repo)

        return {
            "session_id": session_id,
            "status": "active" if db_session else "new",
            "state": db_session.state if db_session else "initializing",
            "message_count": str(len(db_session.messages) if db_session.messages else 0),
        }

    except Exception as e:
        logger.exception(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {e}") from e


@router.get("/session/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    db: DbSessionDep,
) -> SessionHistoryResponse:
    """
    Get the history of a conversation session.

    Args:
        session_id: Unique session identifier
        db: Database session (injected)

    Returns:
        SessionHistoryResponse: Session history with messages and metadata

    Raises:
        HTTPException: If session not found (404)

    """
    repo = get_conversation_session_repository(db)
    db_session = repo.get_by_id(session_id)

    if not db_session:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Convert messages to dict format for API response
    messages = []
    if db_session.messages:
        for msg in db_session.messages:
            messages.append(
                {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                    "timestamp": msg.get("timestamp"),
                    "metadata": msg.get("metadata", {}),
                }
            )

    # Build metadata
    metadata = {
        "state": db_session.state,
        "message_count": len(db_session.messages) if db_session.messages else 0,
        "created_at": db_session.created_at.isoformat() if db_session.created_at else None,
        "has_understanding": bool(db_session.current_understanding),
        "examples_count": len(db_session.collected_examples)
        if db_session.collected_examples
        else 0,
        **(db_session.session_metadata or {}),
    }

    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        metadata=metadata,
    )


@router.get("/sessions", response_model=dict[str, Any])
async def list_sessions(
    db: DbSessionDep,
) -> dict[str, Any]:
    """
    List all active conversation sessions.

    Args:
        db: Database session (injected)

    Returns:
        Dictionary with session count and session summaries

    Raises:
        HTTPException: If session listing fails

    """
    repo = get_conversation_session_repository(db)
    sessions = repo.list_active_summaries(limit=100)

    return {
        "count": len(sessions),
        "sessions": sessions,
    }


@router.post("/stream")
async def stream_chat(
    request: SendMessageRequest,
    db: DbSessionDep,
):
    """
    Stream chat responses.

    Server-Sent Events endpoint for streaming chat responses.

    Args:
        request: Message request with session_id, message, and user_id
        db: Database session (injected)

    Yields:
        Server-sent events with message chunks

    """
    import json

    from fastapi.responses import StreamingResponse

    async def event_generator():
        try:
            orchestrator = ConversationalOrchestrator()
            repo = get_conversation_session_repository(db)
            session_id = request.session_id or str(__import__('uuid').uuid4())
            db_session = _get_or_create_session(session_id, repo)
            context = _db_session_to_context(db_session, orchestrator)

            # Add user message to context
            user_message = ConversationMessage(
                role="user",
                content=request.message,
                metadata={"user_id": request.user_id},
            )
            context.messages.append(user_message)

            # Interpret user intent
            yield f"data: {json.dumps({'type': 'thinking', 'data': 'Analyzing your request...'})}\n\n"

            intent_result = await orchestrator.interpret_intent(
                user_message=request.message,
                context=context,
                enable_mlflow=False,
            )

            intent_type = intent_result.get("intent_type", "unknown")
            response_text = ""

            if intent_type == "create_skill":
                yield f"data: {json.dumps({'type': 'thinking', 'data': 'Understanding your skill requirements...'})}\n\n"

                understanding_result = await orchestrator.deep_understanding(
                    context=context,
                    enable_mlflow=False,
                )
                context.current_understanding = understanding_result.get("enhanced_understanding", "")

                confirmation_result = await orchestrator.confirm_understanding(
                    context=context,
                    enable_mlflow=False,
                )
                response_text = confirmation_result.get("confirmation_summary", "")
                context.state = ConversationState.CONFIRMING_UNDERSTANDING

            elif intent_type == "clarify":
                question_result = await orchestrator.generate_clarifying_question(
                    context=context,
                    enable_mlflow=False,
                )
                response_text = question_result.get("question", "Could you please provide more details?")

            elif intent_type == "refine":
                response_text = (
                    "I understand you want to refine the skill. "
                    "Please provide the skill content and your feedback."
                )
                context.state = ConversationState.COLLECTING_FEEDBACK

            elif intent_type == "multi_skill":
                response_text = (
                    "I see you want to create multiple skills. "
                    "Let's work on them one at a time. Which would you like to start with?"
                )
            else:
                response_text = "I understand. How can I help you create or improve a skill today?"

            # Add assistant response to context
            context.messages.append(ConversationMessage(
                role="assistant",
                content=response_text,
                metadata={"intent_type": intent_type},
            ))

            # Yield the response
            yield f"data: {json.dumps({'type': 'message', 'data': response_text})}\n\n"

            # Update database with new context
            updates = _context_to_db_updates(context)
            for key, value in updates.items():
                setattr(db_session, key, value)
            repo.update(db_session)
            db.commit()

            # Send completion event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.exception("Error in stream_chat")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
