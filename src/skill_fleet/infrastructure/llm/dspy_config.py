"""
DSPy configuration for skill_fleet.

.. deprecated::
    This module is deprecated. Import from `skill_fleet.core.dspy` instead.

This module now re-exports from `skill_fleet.core.dspy.lm_config` for backward compatibility.
"""

from __future__ import annotations

import warnings

from skill_fleet.core.dspy.fleet_config import build_lm_for_task, load_fleet_config

# Re-export from new location
from skill_fleet.core.dspy.lm_config import configure_dspy, get_task_lm

warnings.warn(
    "skill_fleet.llm.dspy_config is deprecated, use skill_fleet.core.dspy instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["configure_dspy", "get_task_lm", "build_lm_for_task", "load_fleet_config"]
