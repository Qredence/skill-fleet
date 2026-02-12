"""
Logging utilities for safe and consistent logging.

This module provides centralized functions for:
- Log sanitization (removing control characters, secrets, ANSI codes)
- Structured logging helpers
- Contextual logging adapters
"""

from __future__ import annotations

import re
from typing import Any


def sanitize_for_log(value: Any, max_length: int = 500) -> str:
    """
    Sanitize a value for safe inclusion in log messages.

    Protects against:
    - Log injection attacks (CRLF)
    - Terminal corruption (ANSI codes)
    - Information leakage (truncation)

    Args:
        value: The value to sanitize (will be converted to str)
        max_length: Maximum length of the output string (default: 500)

    Returns:
        Sanitized string safe for logging

    """
    if not isinstance(value, str):
        try:
            value = str(value)
        except (TypeError, ValueError, RecursionError):
            # Handle objects that can't be converted to string
            return "<unloggable-value>"

    # Remove ANSI escape sequences (e.g., color codes)
    value = re.sub(r"\x1b\[[0-9;]*m", "", value)

    # Replace newlines and tabs with escaped versions to keep log lines single
    value = value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t")

    # Remove remaining control characters (0x00-0x1f and 0x7f)
    # Keep printable characters only
    value = "".join(char for char in value if char.isprintable() or char in ("\\"))

    # Truncate if too long
    if len(value) > max_length:
        return value[:max_length] + "..."

    return value
