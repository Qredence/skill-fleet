"""
Common utility functions for skill_fleet modules.

This module provides shared utilities used across the skill_fleet codebase,
including safe JSON parsing and type conversion functions that handle
the variety of input types encountered when working with LLM outputs.
"""

from __future__ import annotations

import asyncio
import functools
import json
import logging
import time
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def _extract_json_candidate(text: str) -> str | None:
    """
    Best-effort extraction of a JSON object/array from an LLM string.

    DSPy and upstream adapters can change how strictly they enforce structured
    outputs. This helper keeps our parsing resilient when the model wraps JSON
    in code fences or light prose.
    """
    if not isinstance(text, str):
        return None

    s = text.strip()
    if not s:
        return None

    # Strip ```json ... ``` or ``` ... ``` fences if present.
    if s.startswith("```"):
        first_newline = s.find("\n")
        if first_newline != -1:
            inner = s[first_newline + 1 :]
            fence_end = inner.rfind("```")
            if fence_end != -1:
                inner = inner[:fence_end]
            s = inner.strip()

    if not s:
        return None

    if s[0] in "[{":
        return s

    # Try to extract the first {...} or [...] region.
    first_obj = s.find("{")
    first_arr = s.find("[")
    if first_obj == -1 and first_arr == -1:
        return None

    if first_obj == -1:
        start = first_arr
        end = s.rfind("]")
    elif first_arr == -1:
        start = first_obj
        end = s.rfind("}")
    else:
        start = min(first_obj, first_arr)
        end = s.rfind("}" if start == first_obj else "]")

    if end == -1 or end <= start:
        return None
    return s[start : end + 1].strip()


def safe_json_loads(
    value: str | Any,
    default: dict | list | None = None,
    field_name: str = "unknown",
) -> dict | list:
    """
    Safely parse JSON string with fallback to default.

    Handles:
    - Already parsed objects (returns as-is)
    - Valid JSON strings (parses and returns)
    - Invalid JSON (returns default with warning)
    - Pydantic models (extracts via model_dump())

    This is essential when working with DSPy module outputs, as LLMs may
    return structured data as JSON strings, pre-parsed objects, or Pydantic
    models depending on the DSPy version and configuration.

    Args:
        value: String to parse or already-parsed object
        default: Default value if parsing fails (dict or list)
        field_name: Field name for logging

    Returns:
        Parsed JSON or default value (never None)

    """
    if default is None:
        default = {}

    # Already parsed (dict, list, or Pydantic model)
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        # Handle list of Pydantic models
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
    if hasattr(value, "model_dump"):  # Pydantic model
        method = getattr(value, "model_dump", None)
        if callable(method):
            return method()
        return value.model_dump()  # type: ignore[call-non-callable]

    # Empty or None
    if not value:
        return default

    # Try to parse JSON string
    if isinstance(value, str):
        candidate = _extract_json_candidate(value) or value.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse JSON for field '{field_name}': {e}. "
                f"Value preview: {value[:100]}..."
            )
            return default

    # Unknown type
    logger.warning(f"Unexpected type for field '{field_name}': {type(value)}")
    return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Useful for parsing confidence scores, thresholds, and other numeric
    values from LLM outputs that may be returned as strings, ints, or floats.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Float value

    """
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def json_serialize(
    value: Any,
    *,
    indent: int = 2,
    default: Any = "",
    ensure_list: bool = False,
) -> str | list | dict:
    """
    Serialize value to JSON string if it's a list or dict, otherwise return as-is.

    This helper reduces code duplication across DSPy modules that need to pass
    structured data to LLMs as JSON strings while also accepting pre-serialized
    string values.

    Args:
        value: The value to serialize (list, dict, or already-serialized string)
        indent: JSON indentation level (default: 2)
        default: Value to return if input is None or empty (default: "")
        ensure_list: If True, ensure result is a list (for Pydantic model lists)

    Returns:
        JSON string if value is a list/dict, otherwise the original value

    Examples:
        >>> json_serialize([{"a": 1}])
        '[\\n  {\\n    "a": 1\\n  }\\n]'
        >>> json_serialize("already json")
        'already json'
        >>> json_serialize(None)
        ''

    """
    if value is None:
        return default

    if ensure_list and isinstance(value, list):
        # Handle lists of Pydantic models
        return [item.model_dump() if hasattr(item, "model_dump") else item for item in value]

    if isinstance(value, list | dict):
        return json.dumps(value, indent=indent)

    return value


def timed_execution(metric_name: str | None = None) -> Callable[..., Any]:
    """
    Time function execution and log performance.

    Automatically calculate duration_ms and log it.
    If the instance has a `_log_execution` method (like BaseModule), call it.
    Otherwise log to standard logger.

    Args:
        metric_name: Optional custom metric name (default: method name)

    Returns:
        Decorated function (async or sync)

    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(self, *args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _log_metric(self, func, args, kwargs, duration_ms, metric_name)

        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(self, *args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                _log_metric(self, func, args, kwargs, duration_ms, metric_name)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _log_metric(
    instance: Any,
    func: Callable[..., Any],
    args: Any,
    kwargs: Any,
    duration_ms: float,
    metric_name: str | None,
) -> None:
    """Log metrics using available instance methods or fallback."""
    name = metric_name or getattr(func, "__name__", "unknown")

    # Prefer instance._log_execution (BaseModule pattern)
    if hasattr(instance, "_log_execution") and callable(instance._log_execution):
        # We try to construct inputs from args/kwargs if possible
        inputs = kwargs.copy()
        # Add positional args if we can guess names (hard without introspection, so we skip)
        instance._log_execution(
            inputs=inputs,
            outputs={"_metric": name},  # Placeholder as we don't have result in finally
            duration_ms=duration_ms,
        )
    else:
        logger.debug(f"Executed {name} in {duration_ms:.2f}ms")
