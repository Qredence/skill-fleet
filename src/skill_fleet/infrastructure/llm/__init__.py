"""
LLM configuration helpers for `skill_fleet`.

.. deprecated::
    This module is deprecated. Import from `skill_fleet.core.dspy` instead.

This module now re-exports from `skill_fleet.core.dspy` for backward compatibility.
"""

from __future__ import annotations

import warnings

# Re-export from new location
from skill_fleet.core.dspy.fleet_config import (
    FleetConfigError,
    build_lm_for_task,
    load_fleet_config,
)

warnings.warn(
    "skill_fleet.llm is deprecated, use skill_fleet.core.dspy instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "FleetConfigError",
    "build_lm_for_task",
    "load_fleet_config",
]
