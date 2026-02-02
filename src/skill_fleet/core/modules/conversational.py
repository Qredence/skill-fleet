"""
Conversational module for skill-fleet chat interface.

Provides natural language conversation capabilities using modern DSPy
signatures with Reasoning support.
"""

from __future__ import annotations

import logging
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.base import ChatResponse

logger = logging.getLogger(__name__)


class ConversationalModule(BaseModule):
    """
    Module for handling conversational interactions.

    Uses ChainOfThought with Reasoning support for transparent,
    explainable responses.

    Example:
        >>> module = ConversationalModule()
        >>> result = module(message="Hello, how are you?")
        >>> print(result.response)
        >>> print(result.reasoning)  # Shows thinking process

    """

    def __init__(self):
        """Initialize conversational module."""
        super().__init__()
        self.processor = dspy.ChainOfThought(ChatResponse)

    async def aforward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Process conversational message asynchronously.

        Args:
            **kwargs: Must include message and optional context

        Returns:
            Prediction with response, reasoning, and suggested actions

        """
        try:
            message = kwargs.get("message", "")
            context = kwargs.get("context")

            # Sanitize inputs
            safe_message = self._sanitize_input(message, max_length=5000)
            safe_context = self._sanitize_input(str(context) if context else "", max_length=10000)

            result = await self.processor.acall(
                message=safe_message,
                context=safe_context,
            )

            return self._to_prediction(
                response=result.response,
                reasoning=result.reasoning,
                suggested_actions=result.suggested_actions,
                metadata={"module": "ConversationalModule"},
            )

        except Exception as e:
            logger.error(f"Conversation error: {e}")
            return self._to_prediction(
                response="I apologize, but I encountered an error processing your message.",
                reasoning=None,
                suggested_actions=["Try rephrasing your message"],
                metadata={"error": str(e)},
            )
