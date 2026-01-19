"""Streaming DSPy modules for real-time reasoning and response generation.

Enables streaming of thinking content, intermediate steps, and final responses
via Server-Sent Events (SSE) and chunked responses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Callable, TypedDict

import dspy

logger = logging.getLogger(__name__)


class ThinkingChunk(TypedDict):
    """Chunk of thinking/reasoning content."""

    type: str  # 'thinking', 'reasoning', 'thought', 'internal', 'step'
    content: str
    step: int | None


class ResponseChunk(TypedDict):
    """Chunk of assistant response."""

    type: str  # 'response', 'complete'
    content: str


class StreamEvent(TypedDict, total=False):
    """Event sent via Server-Sent Events."""

    type: str  # 'thinking', 'response', 'error', 'complete'
    data: str
    step: int | None


class StreamingModule(dspy.Module):
    """Base class for streaming DSPy modules.

    Provides methods for yielding thinking content and responses incrementally.
    """

    def __init__(self):
        super().__init__()
        self._thinking_buffer: list[str] = []
        self._step_counter = 0

    def yield_thinking(self, content: str, thinking_type: str = "thinking") -> ThinkingChunk:
        """Yield a thinking/reasoning chunk.

        Args:
            content: The thinking content to yield
            thinking_type: Type of thinking ('thinking', 'reasoning', 'thought', etc.)

        Returns:
            ThinkingChunk for streaming to client
        """
        self._thinking_buffer.append(content)
        self._step_counter += 1
        return {
            "type": thinking_type,
            "content": content,
            "step": self._step_counter,
        }

    def get_thinking_summary(self) -> str:
        """Get full thinking summary."""
        return "\n".join(self._thinking_buffer)

    def clear_thinking(self) -> None:
        """Clear thinking buffer for next turn."""
        self._thinking_buffer.clear()
        self._step_counter = 0


class StreamingIntentParser(StreamingModule):
    """Parse user intent with streaming thinking process.

    Yields:
        - Thinking chunks as it analyzes the user message
        - Final intent classification
        - Suggested actions
    """

    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(
            "user_message -> intent: str, confidence: float, parameters: str"
        )

    async def forward_streaming(
        self, user_message: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """Parse intent with streaming thinking output.

        Yields stream events as thinking progresses.
        """
        self.clear_thinking()

        # Yield thinking steps
        yield {
            "type": "thinking",
            "data": json.dumps({
                "type": "thought",
                "content": f"Analyzing user message: {user_message[:50]}...",
                "step": 1,
            }),
        }

        yield {
            "type": "thinking",
            "data": json.dumps({
                "type": "reasoning",
                "content": "Looking for keywords: 'optimize', 'create', 'list', 'validate'...",
                "step": 2,
            }),
        }

        # Run classification
        yield {
            "type": "thinking",
            "data": json.dumps({
                "type": "reasoning",
                "content": "Running LM-based intent classification...",
                "step": 3,
            }),
        }

        try:
            result = self.classify(user_message=user_message)

            yield {
                "type": "thinking",
                "data": json.dumps({
                    "type": "internal",
                    "content": f"Intent: {result.intent} (confidence: {result.confidence})",
                    "step": 4,
                }),
            }

            # Yield final response
            yield {
                "type": "response",
                "data": json.dumps({
                    "type": "response",
                    "content": f"**Intent:** {result.intent}\n**Confidence:** {result.confidence}\n**Parameters:** {result.parameters}",
                }),
            }

            yield {"type": "complete", "data": ""}

        except Exception as e:
            logger.exception("Error in streaming intent parsing")
            yield {"type": "error", "data": str(e)}


class StreamingAssistant(StreamingModule):
    """Assistant that streams thinking and responses.

    Used for conversational skill creation and optimization.
    """

    def __init__(self):
        super().__init__()
        self.intent_parser = StreamingIntentParser()
        self.responder = dspy.ChainOfThought(
            "intent, context -> response: str, suggested_actions: str"
        )

    async def forward_streaming(
        self, user_message: str, context: dict[str, Any] | None = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """Generate streaming response with full thinking process.

        Yields stream events as thinking progresses and response is generated.
        """
        self.clear_thinking()
        context = context or {}

        # Step 1: Parse intent with streaming
        yield {
            "type": "thinking",
            "data": json.dumps({
                "type": "thought",
                "content": "Step 1: Understanding user intent...",
                "step": 1,
            }),
        }

        # Get intent through streaming
        intent_data = None
        async for event in self.intent_parser.forward_streaming(user_message):
            yield event
            if event["type"] == "response":
                try:
                    chunk = json.loads(event["data"])
                    intent_data = chunk["content"]
                except Exception:
                    pass

        # Step 2: Generate response
        yield {
            "type": "thinking",
            "data": json.dumps({
                "type": "thought",
                "content": "Step 2: Generating response with suggested actions...",
                "step": 5,
            }),
        }

        try:
            result = self.responder(intent=intent_data or "", context=json.dumps(context))

            yield {
                "type": "thinking",
                "data": json.dumps({
                    "type": "internal",
                    "content": f"Response ready. Suggested actions: {result.suggested_actions}",
                    "step": 6,
                }),
            }

            # Yield streamed response (simulating chunked generation)
            response = result.response
            chunk_size = 50
            for i in range(0, len(response), chunk_size):
                chunk = response[i : i + chunk_size]
                yield {
                    "type": "response",
                    "data": json.dumps({"type": "response", "content": chunk}),
                }

            # Yield suggested actions
            yield {
                "type": "response",
                "data": json.dumps({
                    "type": "response",
                    "content": f"\n\n**Suggested Actions:**\n{result.suggested_actions}",
                }),
            }

            yield {"type": "complete", "data": ""}

        except Exception as e:
            logger.exception("Error in streaming assistant")
            yield {"type": "error", "data": str(e)}


async def stream_events_to_sse(
    event_generator: AsyncGenerator[StreamEvent, None],
) -> AsyncGenerator[str, None]:
    """Convert stream events to Server-Sent Events format.

    Args:
        event_generator: Async generator yielding StreamEvent objects

    Yields:
        Server-Sent Events formatted strings
    """
    async for event in event_generator:
        event_type = event.get("type", "unknown")
        data = event.get("data", "")

        # Format as SSE
        sse_line = f"event: {event_type}\n"
        sse_line += f"data: {data}\n\n"
        yield sse_line
