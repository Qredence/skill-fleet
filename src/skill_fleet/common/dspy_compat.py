from __future__ import annotations

from typing import Any

import dspy


def coerce_reasoning_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dspy.Reasoning):
        return str(value.content or "").strip()
    return str(value).strip()
