"""
Fleet LLM configuration loader and DSPy LM factory.

.. deprecated::
    This module is deprecated. Import from `skill_fleet.dspy` instead.

This module now re-exports from `skill_fleet.dspy` for backward compatibility.
"""

from __future__ import annotations

import warnings

# Re-export from new location (all public symbols)
from skill_fleet.dspy import build_lm_for_task, load_fleet_config

warnings.warn(
    "skill_fleet.infrastructure.llm.fleet_config is deprecated, use skill_fleet.dspy instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "build_lm_for_task",
    "load_fleet_config",
]
