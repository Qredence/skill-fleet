"""
DSPy streaming utilities for skill-fleet.

Provides streaming support for DSPy modules with proper async handling,
field-specific listeners, and SSE-compatible output.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dspy
from dspy.streaming import StreamListener, streamify

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

logger = logging.getLogger(__name__)


class StreamingConfig:
    """Configuration for DSPy streaming operations."""

    def __init__(
        self,
        status_message_provider: Any | None = None,
        stream_listeners: list[StreamListener] | None = None,
    ):
        """
        Initialize streaming configuration.

        Args:
            status_message_provider: Optional custom status message provider
            stream_listeners: List of stream listeners for field-specific streaming

        """
        self.status_message_provider = status_message_provider
        self.stream_listeners = stream_listeners or []


def create_streaming_module(
    module: dspy.Module,
    config: StreamingConfig | None = None,
) -> Callable[..., Any]:
    """
    Wrap a DSPy module for streaming output.

    Args:
        module: Module to wrap
        config: Streaming configuration

    Returns:
        Streamified module

    """
    config = config or StreamingConfig()

    return streamify(
        program=module,
        status_message_provider=config.status_message_provider,
        stream_listeners=config.stream_listeners,
    )


async def stream_prediction(
    module: dspy.Module,
    **kwargs: Any,
) -> AsyncIterator[dict[str, Any]]:
    """
    Stream predictions from a module with structured output.

    Args:
        module: DSPy module to execute
        **kwargs: Arguments to pass to module

    Yields:
        Dict with 'type' and 'data' keys:
        - type='prediction': Final prediction result
        - type='stream': Streaming field content
        - type='message': Status/debug messages

    Example:
        >>> async for event in stream_prediction(module, query="test"):
        ...     print(f"{event['type']}: {event['data']}")

    """
    stream_module = create_streaming_module(module)

    try:
        output = stream_module(**kwargs)

        async for value in output:
            if isinstance(value, dspy.Prediction):
                try:
                    fields = dict(value)
                except Exception:
                    fields = {k: getattr(value, k) for k in value.__dict__}
                yield {
                    "type": "prediction",
                    "data": {
                        "fields": fields,
                    },
                }
            elif hasattr(value, "field_name") and hasattr(value, "content"):
                # StreamResponse-like object
                yield {
                    "type": "stream",
                    "data": {
                        "field": value.field_name,
                        "content": value.content,
                    },
                }
            else:
                yield {
                    "type": "message",
                    "data": {"content": str(value)},
                }
    except Exception:
        # Log full error details on the server, including stack trace,
        # but do not expose them to the client.
        logger.error("Streaming error", exc_info=True)
        yield {
            "type": "error",
            "data": {"message": "An internal error occurred during streaming."},
        }


def create_reasoning_listener() -> StreamListener:
    """
    Create a StreamListener for reasoning field.

    Returns:
        Configured StreamListener

    """
    return StreamListener(signature_field_name="reasoning")


def create_answer_listener() -> StreamListener:
    """
    Create a StreamListener for answer field.

    Returns:
        Configured StreamListener

    """
    return StreamListener(signature_field_name="answer")


def create_field_listener(field_name: str) -> StreamListener:
    """
    Create a StreamListener for any field.

    Args:
        field_name: Name of the field to listen to

    Returns:
        Configured StreamListener

    """
    return StreamListener(signature_field_name=field_name)
