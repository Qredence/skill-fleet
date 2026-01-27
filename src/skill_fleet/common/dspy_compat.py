"""DSPy backward compatibility utilities."""

from typing import Any

import dspy


def coerce_reasoning_text(value: Any) -> str:
    """Coerce reasoning text to string safely."""
    if value is None:
        return ""
    if isinstance(value, dspy.Reasoning):
        return str(value.content or "").strip()
    return str(value).strip()
