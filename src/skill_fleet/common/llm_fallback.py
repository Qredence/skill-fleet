"""
Controls whether LLM-dependent modules may fall back to deterministic behavior.

Best practice in production is to fail loudly when the LLM is misconfigured (e.g.,
missing API key/provider), but for tests/offline usage we allow explicit fallback.
"""

from __future__ import annotations

import os


def llm_fallback_enabled() -> bool:
    """Return True if deterministic fallbacks are allowed."""
    value = os.getenv("SKILL_FLEET_ALLOW_LLM_FALLBACK", "0").strip().lower()
    return value in {"1", "true", "yes", "on"}
