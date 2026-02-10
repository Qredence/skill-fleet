"""
Modernized DSPy integration for skill-fleet.

This package provides DSPy utilities for building robust LLM-powered workflows.

Configuration is now handled in the API lifespan (see api/lifespan.py) via
ConfigModelLoader from infrastructure.tracing.config.

Usage:
    from skill_fleet.dspy import dspy_context

    # Use context for scoped configuration
    with dspy_context(lm=custom_lm):
        result = await module.aforward(...)

Deprecated (removed):
    - DSPyConfig (singleton) - use ConfigModelLoader instead
    - configure_dspy() - configuration now in api/lifespan.py
    - get_task_lm() - use ConfigModelLoader.get_lm() instead
"""

from __future__ import annotations

from skill_fleet.dspy.config import (
    create_adapter,
    dspy_context,
    get_default_adapter,
)

__all__ = [
    "create_adapter",
    "dspy_context",
    "get_default_adapter",
]
