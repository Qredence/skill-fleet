"""DSPy backward compatibility utilities."""

from typing import Any

import dspy

if hasattr(dspy, "Reasoning"):
    Reasoning = dspy.Reasoning
else:

    class Reasoning(str):
        """Compatibility wrapper for reasoning."""

        content: str | None = None

        def __new__(cls, content: str | None = None, **kwargs):
            """Create a new Reasoning instance."""
            return super().__new__(cls, content or "")

        def __init__(self, content: str | None = None, **kwargs):
            self.content = content


def coerce_reasoning_text(value: Any) -> str:
    """Coerce reasoning text to string safely."""
    if value is None:
        return ""
    if isinstance(value, Reasoning):
        return str(value.content or "").strip()
    return str(value).strip()
