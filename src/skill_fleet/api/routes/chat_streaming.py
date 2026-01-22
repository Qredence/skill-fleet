"""
Chat streaming endpoints for real-time assistant responses.

Provides Server-Sent Events (SSE) endpoints for streaming thinking
content, reasoning, and responses in real-time, using the core ConversationService.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...core.dspy.streaming import stream_events_to_sse, StreamEvent
from ...core.services.conversation import ConversationService, ConversationSession
from ..dependencies import TaxonomyManagerDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# In-memory session store (replace with Redis/DB in production)
SESSIONS: dict[str, ConversationSession] = {}


class ChatMessageRequest(BaseModel):
    """Request for chat message processing."""

    message: str = Field(..., description="User message to process")
    session_id: str | None = Field(
        default=None, description="Session ID for persistent conversation"
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Optional context (previous skills, jobs, etc.)"
    )


class ChatStreamEvent(BaseModel):
    """Event sent during streaming."""

    type: str = Field(..., description="Event type: thinking, response, error, complete")
    data: str = Field(..., description="Event data (JSON)")
    step: int | None = Field(default=None, description="Step number for thinking")


@router.post("/stream")
async def chat_stream(request: ChatMessageRequest, taxonomy: TaxonomyManagerDep):
    """
    Stream real-time chat response with thinking process.

    This endpoint streams Server-Sent Events (SSE) that include:
    - **thinking**: Intermediate reasoning steps
    - **response**: Generated response chunks (or full response updates)
    - **error**: Any errors that occur
    - **complete**: Signal that streaming is finished

    Args:
        request: ChatMessageRequest with message and optional session_id
        taxonomy: TaxonomyManager dependency

    Returns:
        Server-Sent Events stream

    """
    logger.info(f"Chat stream request received: message='{request.message}'")

    try:
        # Check DSPy configuration
        import dspy

        if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
            logger.error("DSPy not configured - no LM available")
            raise HTTPException(
                status_code=503,
                detail="DSPy not configured. Please ensure GOOGLE_API_KEY is set and server was restarted.",
            )

        # Initialize or retrieve session
        session_id = request.session_id or "default"
        if session_id not in SESSIONS:
            SESSIONS[session_id] = ConversationSession()
        session = SESSIONS[session_id]

        # Initialize service
        service = ConversationService(taxonomy_manager=taxonomy)

        # Queue for collecting events from callback
        queue: asyncio.Queue[StreamEvent] = asyncio.Queue()

        def thinking_callback(chunk: str):
            """Callback to push thinking chunks to queue."""
            event: StreamEvent = {
                "type": "thinking",
                "data": json.dumps({"content": chunk}),
                "step": None,
            }
            queue.put_nowait(event)

        async def event_generator() -> Any:
            """Generate streaming events."""
            try:
                # Start the service response task
                task = asyncio.create_task(
                    service.respond(
                        user_message=request.message,
                        session=session,
                        thinking_callback=thinking_callback,
                    )
                )

                # Consume queue while task is running
                while not task.done():
                    try:
                        # Wait for new item or task completion
                        # timeout allows checking task status periodically
                        event = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield event
                        queue.task_done()
                    except asyncio.TimeoutError:
                        continue

                # Task is done, check for result or exception
                if task.exception():
                    raise task.exception()  # type: ignore

                response = task.result()

                # Process any remaining items in queue
                while not queue.empty():
                    event = queue.get_nowait()
                    yield event
                    queue.task_done()

                # Yield final response
                response_event: StreamEvent = {
                    "type": "response",
                    "data": json.dumps(response.to_dict()),
                    "step": None,
                }
                yield response_event

                complete_event: StreamEvent = {
                    "type": "complete",
                    "data": json.dumps({"session_id": session_id}),
                    "step": None,
                }
                yield complete_event

            except Exception as e:
                logger.exception("Error during streaming generation")
                error_event: StreamEvent = {
                    "type": "error",
                    "data": json.dumps({"error": str(e), "type": type(e).__name__}),
                    "step": None,
                }
                yield error_event

        # Convert to SSE format and return as StreamingResponse

        return StreamingResponse(
            stream_events_to_sse(event_generator()),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in chat stream endpoint")
        raise HTTPException(
            status_code=500, detail=f"Internal error: {type(e).__name__}: {str(e)}"
        ) from e


@router.post("/sync")
async def chat_sync(request: ChatMessageRequest, taxonomy: TaxonomyManagerDep) -> dict[str, Any]:
    """
    Non-streaming chat response (for compatibility).

    Args:
        request: ChatMessageRequest with message and optional session_id
        taxonomy: TaxonomyManager dependency

    Returns:
        Complete response
    """
    try:
        # Check DSPy configuration
        import dspy

        if not hasattr(dspy.settings, "lm") or dspy.settings.lm is None:
            raise HTTPException(status_code=503, detail="DSPy not configured")

        # Initialize or retrieve session
        session_id = request.session_id or "default"
        if session_id not in SESSIONS:
            SESSIONS[session_id] = ConversationSession()
        session = SESSIONS[session_id]

        service = ConversationService(taxonomy_manager=taxonomy)

        # Collect thinking
        thinking_chunks = []

        def thinking_callback(chunk: str):
            thinking_chunks.append(chunk)

        response = await service.respond(
            user_message=request.message,
            session=session,
            thinking_callback=thinking_callback,
        )

        return response.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in sync chat")
        raise HTTPException(status_code=500, detail=str(e)) from e
