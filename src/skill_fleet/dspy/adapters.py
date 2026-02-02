"""
DSPy adapter utilities for skill-fleet.

Provides factory functions and utilities for creating and configuring
DSPy adapters with skill-fleet defaults.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dspy.adapters import ChatAdapter, JSONAdapter

if TYPE_CHECKING:
    from dspy.adapters.base import Adapter


class AdapterFactory:
    """Factory for creating DSPy adapters with skill-fleet defaults."""

    @staticmethod
    def create_chat_adapter(
        use_native_function_calling: bool = False,
        **kwargs,
    ) -> ChatAdapter:
        """
        Create ChatAdapter with skill-fleet configuration.

        Args:
            use_native_function_calling: Enable native function calling
            **kwargs: Additional adapter arguments

        Returns:
            Configured ChatAdapter

        """
        return ChatAdapter(
            use_native_function_calling=use_native_function_calling,
            **kwargs,
        )

    @staticmethod
    def create_json_adapter(
        use_native_function_calling: bool = True,
        **kwargs,
    ) -> JSONAdapter:
        """
        Create JSONAdapter with skill-fleet configuration.

        Args:
            use_native_function_calling: Enable native function calling
            **kwargs: Additional adapter arguments

        Returns:
            Configured JSONAdapter

        """
        return JSONAdapter(
            use_native_function_calling=use_native_function_calling,
            **kwargs,
        )


def get_adapter_for_task(task_type: str) -> Adapter:
    """
    Get appropriate adapter for a task type.

    Args:
        task_type: Type of task ('chat', 'structured', 'code', etc.)

    Returns:
        Best adapter for the task

    """
    adapter_map = {
        "chat": lambda: ChatAdapter(),
        "structured": lambda: JSONAdapter(use_native_function_calling=True),
        "code": lambda: ChatAdapter(),
        "extraction": lambda: JSONAdapter(use_native_function_calling=False),
    }

    factory = adapter_map.get(task_type, lambda: ChatAdapter())
    return factory()
