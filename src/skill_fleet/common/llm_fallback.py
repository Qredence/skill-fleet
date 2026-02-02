"""
LLM Fallback utilities.

Provides decorators and context managers for handling LLM failures gracefully.
Controls whether LLM-dependent modules may fall back to deterministic behavior.

Best practice in production is to fail loudly when the LLM is misconfigured (e.g.,
missing API key/provider), but for tests/offline usage we allow explicit fallback.
"""

from __future__ import annotations

import functools
import logging
import os
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def llm_fallback_enabled() -> bool:
    """Return True if deterministic fallbacks are allowed."""
    value = os.getenv("SKILL_FLEET_ALLOW_LLM_FALLBACK", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def with_llm_fallback(
    default_return: Any = None,
    log_message: str = "Module failed (using fallback)",
) -> Callable[..., Any]:
    """
    Wrap DSPy module methods to handle LLM failures gracefully.

    If the wrapped method raises an exception and fallback is enabled,
    log a warning and return the default value. Otherwise, re-raise.

    Args:
        default_return: Value to return on failure (default: None)
        log_message: Message to log on failure

    Returns:
        Decorated function

    Example:
        >>> @with_llm_fallback(default_return={"status": "failed"})
        ... async def aforward(self, **kwargs):
        ...     return await self.module(**kwargs)

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                if not llm_fallback_enabled():
                    raise

                logger.warning(f"{log_message}: {e}")
                return default_return

        return wrapper

    return decorator
