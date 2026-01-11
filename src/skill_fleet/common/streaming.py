"""DSPy streaming integration for CLI and FastAPI deployment.

This module provides utilities for streaming DSPy module outputs:
- Real-time thinking/reasoning display for CLI
- Server-Sent Events (SSE) for FastAPI deployment
- Status messages for workflow progress

Based on: https://dspy.ai/tutorials/streaming/
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import dspy
from dspy.streaming import StatusMessageProvider, StreamListener

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)


class SkillFleetStatusProvider(StatusMessageProvider):
    """Status messages for skill creation workflow.

    Provides human-readable status updates during:
    - LLM calls
    - Module execution
    - Tool calls (research, file operations, etc.)
    """

    def lm_start_status_message(self, instance: Any, inputs: dict[str, Any]) -> str:
        """Status message at the start of calling dspy.LM."""
        return "🤖 Calling LLM..."

    def lm_end_status_message(self, outputs: dspy.Prediction) -> str:
        """Status message at the end of calling dspy.LM."""
        return "✅ LLM call complete"

    def module_start_status_message(self, instance: dspy.Module, inputs: dict[str, Any]) -> str:
        """Status message at the start of calling a dspy.Module."""
        module_name = instance.__class__.__name__
        return f"🔄 Running {module_name}..."

    def module_end_status_message(self, outputs: dspy.Prediction) -> str:
        """Status message at the end of calling a dspy.Module."""
        return "✅ Module complete"

    def tool_start_status_message(self, instance: Any, inputs: dict[str, Any]) -> str:
        """Status message at the start of calling a dspy.Tool."""
        tool_name = getattr(instance, "name", "unknown_tool")
        return f"🔧 Calling tool: {tool_name}..."

    def tool_end_status_message(self, outputs: Any) -> str:
        """Status message at the end of calling a dspy.Tool."""
        return "✅ Tool call complete"


def create_streaming_module(
    module: dspy.Module,
    reasoning_field: str = "reasoning",
    async_mode: bool = False,
) -> dspy.Module:
    """Wrap a DSPy module with streaming for reasoning field.

    Args:
        module: DSPy module to wrap (e.g., ChainOfThought module)
        reasoning_field: Field name to stream (default: "reasoning" from ChainOfThought)
        async_mode: If True, use async streaming; if False, use sync (for CLI)

    Returns:
        Streamified DSPy module that yields StreamResponse, StatusMessage, and Prediction

    Example:
        >>> # For CLI usage (sync)
        >>> stream_module = create_streaming_module(
        ...     dspy.ChainOfThought("question->answer"),
        ...     reasoning_field="reasoning",
        ...     async_mode=False
        ... )
        >>> for chunk in stream_module(question="What is 2+2?"):
        ...     if isinstance(chunk, dspy.streaming.StreamResponse):
        ...         print(chunk.chunk, end="")  # Stream reasoning tokens
        >>> # For FastAPI (async)
        >>> stream_module = create_streaming_module(
        ...     dspy.ChainOfThought("question->answer"),
        ...     reasoning_field="reasoning",
        ...     async_mode=True
        ... )
        >>> async for chunk in stream_module(question="What is 2+2?"):
        ...     # Handle async streaming
    """
    return dspy.streamify(
        module,
        stream_listeners=[
            StreamListener(signature_field_name=reasoning_field),
        ],
        status_message_provider=SkillFleetStatusProvider(),
        async_streaming=async_mode,
    )


def create_async_module(module: dspy.Module, max_workers: int = 4) -> dspy.Module:
    """Convert DSPy module to async mode for FastAPI deployment.

    Uses dspy.asyncify which runs the program in a thread pool.
    Default worker limit is 8, configurable via async_max_workers.

    Args:
        module: DSPy module to convert
        max_workers: Maximum number of async workers (default: 4)

    Returns:
        Asyncified DSPy module

    Example:
        >>> module = dspy.ChainOfThought("question->answer")
        >>> async_module = create_async_module(module, max_workers=4)
        >>> result = await async_module(question="What is 2+2?")
    """
    dspy.configure(async_max_workers=max_workers)
    return dspy.asyncify(module)


async def stream_dspy_response(streaming_program: Any, **kwargs: Any) -> AsyncIterator[str]:
    """Convert DSPy streaming program to FastAPI Server-Sent Events format.

    This is the async generator function that yields SSE-formatted chunks.

    Args:
        streaming_program: Streamified DSPy program (async mode)
        **kwargs: Arguments to pass to the streaming program

    Yields:
        SSE-formatted strings (data: {...}\\n\\n)

    SSE Event Types:
        - "reasoning": Thinking/reasoning tokens from ChainOfThought
        - "status": Status messages (LM calls, tool calls, etc.)
        - "prediction": Final prediction result
        - "[DONE]": Stream complete marker

    Example:
        >>> stream = create_streaming_module(module, async_mode=True)
        >>> from fastapi.responses import StreamingResponse
        >>> return StreamingResponse(
        ...     stream_dspy_response(stream, question="What is 2+2?"),
        ...     media_type="text/event-stream"
        ... )
    """
    async for chunk in streaming_program(**kwargs):
        if isinstance(chunk, dspy.Prediction):
            yield f"data: {json.dumps({'type': 'prediction', 'data': chunk.labels()})}\n\n"
        elif isinstance(chunk, dspy.streaming.StreamResponse):
            yield f"data: {json.dumps({'type': 'reasoning', 'chunk': chunk.chunk})}\n\n"
        elif isinstance(chunk, dspy.streaming.StatusMessage):
            yield f"data: {json.dumps({'type': 'status', 'message': chunk.message})}\n\n"
    yield "data: [DONE]\n\n"


def process_stream_sync(
    streaming_program: Any,
    **kwargs: Any,
) -> Generator[dict[str, Any], None, None]:
    """Process a sync DSPy stream and yield normalized events.

    This is useful for CLI usage where you want to handle all stream types
    uniformly.

    Args:
        streaming_program: Streamified DSPy program (sync mode)
        **kwargs: Arguments to pass to the streaming program

    Yields:
        Normalized event dictionaries with keys:
            - "type": "reasoning" | "status" | "prediction"
            - "content": The actual content (token, message, or prediction)

    Example:
        >>> stream = create_streaming_module(module, async_mode=False)
        >>> for event in process_stream_sync(stream, question="What is 2+2?"):
        ...     if event["type"] == "reasoning":
        ...         print(event["content"], end="", flush=True)
        ...     elif event["type"] == "status":
        ...         print(f"\\n{event['content']}")
    """
    for chunk in streaming_program(**kwargs):
        if isinstance(chunk, dspy.Prediction):
            yield {"type": "prediction", "content": chunk}
        elif isinstance(chunk, dspy.streaming.StreamResponse):
            yield {"type": "reasoning", "content": chunk.chunk}
        elif isinstance(chunk, dspy.streaming.StatusMessage):
            yield {"type": "status", "content": chunk.message}


__all__ = [
    "SkillFleetStatusProvider",
    "create_streaming_module",
    "create_async_module",
    "stream_dspy_response",
    "process_stream_sync",
    # Test stub classes (for unit testing)
    "StubPrediction",
    "StubStreamResponse",
    "StubStatusMessage",
]


# ============================================================================
# Test Stub Classes (for unit testing)
# ============================================================================


class StubPrediction(dspy.Prediction):
    """Stub Prediction class for testing."""

    def __init__(self, labels_dict: dict):
        """Initialize stub prediction with labels dict.

        Args:
            labels_dict: Dictionary of prediction labels
        """
        self._labels = labels_dict

    def labels(self):
        """Return prediction labels."""
        return self._labels


class StubStreamResponse(dspy.streaming.StreamResponse):
    """Stub StreamResponse class for testing."""

    def __init__(self, chunk: str):
        self.chunk = chunk


class StubStatusMessage(dspy.streaming.StatusMessage):
    """Stub StatusMessage class for testing."""

    def __init__(self, message: str):
        self.message = message
