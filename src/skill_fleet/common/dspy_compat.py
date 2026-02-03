"""
DSPy backward compatibility utilities.

.. deprecated:: 2026.02
    This module provides compatibility for older DSPy versions.
    Will be removed in 2026.04 when minimum DSPy version is 3.2+.
"""

import warnings
from typing import Any

import dspy

# Emit deprecation warning on import
warnings.warn(
    "skill_fleet.common.dspy_compat is deprecated and will be removed in 2026.04. "
    "Update to DSPy 3.2+ which has native Reasoning support.",
    DeprecationWarning,
    stacklevel=2,
)

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
