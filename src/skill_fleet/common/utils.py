"""Common utility functions for skill_fleet modules.

This module provides shared utilities used across the skill_fleet codebase,
including safe JSON parsing and type conversion functions that handle
the variety of input types encountered when working with LLM outputs.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def safe_json_loads(
    value: str | Any,
    default: dict | list | None = None,
    field_name: str = "unknown",
) -> dict | list:
    """Safely parse JSON string with fallback to default.

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
        return value.model_dump()

    # Empty or None
    if not value:
        return default

    # Try to parse JSON string
    if isinstance(value, str):
        try:
            return json.loads(value)
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
    """Safely convert value to float.

    Useful for parsing confidence scores, thresholds, and other numeric
    values from LLM outputs that may be returned as strings, ints, or floats.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Float value
    """
    if isinstance(value, (int, float)):
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
    """Serialize value to JSON string if it's a list or dict, otherwise return as-is.

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

    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=indent)

    return value
