"""
Modernized DSPy integration for skill-fleet.

This package provides centralized DSPy configuration, adapters, streaming,
and utilities for building robust LLM-powered workflows.

Usage:
    from skill_fleet.dspy import configure_dspy, get_task_lm
    from skill_fleet.dspy.config import dspy_context

    # Configure once at startup
    configure_dspy()

    # Use context for scoped configuration
    with dspy_context(lm=custom_lm):
        result = await module.aforward(...)
"""

from __future__ import annotations

from skill_fleet.dspy.config import (
    DSPyConfig,
    configure_dspy,
    create_adapter,
    dspy_context,
    get_default_adapter,
    get_task_lm,
)

__all__ = [
    "DSPyConfig",
    "configure_dspy",
    "create_adapter",
    "dspy_context",
    "get_default_adapter",
    "get_task_lm",
]
