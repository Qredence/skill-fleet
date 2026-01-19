"""Chat streaming endpoints for real-time assistant responses.

Provides Server-Sent Events (SSE) endpoints for streaming thinking
content, reasoning, and responses in real-time.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...core.dspy.streaming import StreamingAssistant, stream_events_to_sse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    """Request for chat message processing."""

    message: str = Field(..., description="User message to process")
    context: dict[str, Any] | None = Field(
        default=None, description="Optional context (previous skills, jobs, etc.)"
    )


class ChatStreamEvent(BaseModel):
    """Event sent during streaming."""

    type: str = Field(..., description="Event type: thinking, response, error, complete")
    data: str = Field(..., description="Event data (JSON)")
    step: int | None = Field(default=None, description="Step number for thinking")


@router.post("/stream")
async def chat_stream(request: ChatMessageRequest):
    """Stream real-time chat response with thinking process.

    This endpoint streams Server-Sent Events (SSE) that include:
    - **thinking**: Intermediate reasoning steps
    - **response**: Generated response chunks
    - **error**: Any errors that occur
    - **complete**: Signal that streaming is finished

    Example usage (JavaScript):
    ```javascript
    const eventSource = new EventSource("/api/v1/chat/stream");
    eventSource.addEventListener("thinking", (e) => {
      console.log("Thinking:", JSON.parse(e.data));
    });
    eventSource.addEventListener("response", (e) => {
      console.log("Response:", JSON.parse(e.data));
    });
    eventSource.addEventListener("complete", () => {
      eventSource.close();
    });
    ```

    Args:
        request: ChatMessageRequest with message and optional context

    Returns:
        Server-Sent Events stream
    """
    try:
        assistant = StreamingAssistant()

        async def event_generator():
            """Generate streaming events."""
            try:
                async for event in assistant.forward_streaming(
                    user_message=request.message, context=request.context
                ):
                    yield event
            except Exception as e:
                logger.exception("Error in streaming")
                yield {"type": "error", "data": str(e)}

        # Convert to SSE format and return as StreamingResponse
        return StreamingResponse(
            stream_events_to_sse(event_generator()),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.exception("Error in chat stream endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def chat_sync(request: ChatMessageRequest) -> dict[str, Any]:
    """Non-streaming chat response (for compatibility).

    Collects all streaming events and returns as complete response.

    Args:
        request: ChatMessageRequest with message and optional context

    Returns:
        Complete response with thinking summary and response
    """
    try:
        assistant = StreamingAssistant()

        thinking_steps: list[str] = []
        responses: list[str] = []
        error: str | None = None

        async for event in assistant.forward_streaming(
            user_message=request.message, context=request.context
        ):
            if event["type"] == "thinking":
                try:
                    data = json.loads(event["data"])
                    thinking_steps.append(data["content"])
                except Exception:
                    pass
            elif event["type"] == "response":
                try:
                    data = json.loads(event["data"])
                    responses.append(data["content"])
                except Exception:
                    pass
            elif event["type"] == "error":
                error = event["data"]

        if error:
            raise HTTPException(status_code=500, detail=error)

        return {
            "message": request.message,
            "thinking": thinking_steps,
            "response": "".join(responses),
            "thinking_summary": assistant.get_thinking_summary(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in sync chat")
        raise HTTPException(status_code=500, detail=str(e))
