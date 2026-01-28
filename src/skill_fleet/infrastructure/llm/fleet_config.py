"""
Fleet LLM configuration loader and DSPy LM factory.

.. deprecated::
    This module is deprecated. Import from `skill_fleet.core.dspy` instead.

This module now re-exports from `skill_fleet.core.dspy.fleet_config` for backward compatibility.
"""

from __future__ import annotations

import warnings

# Re-export from new location (all public symbols)
from skill_fleet.core.dspy.fleet_config import (
    FleetConfigError,
    TaskLMResolution,
    _get_env_value,
    _get_registry_entry,
    _model_provider,
    _resolve_task_lm,
    build_lm_for_task,
    load_fleet_config,
    resolve_model_key,
)

warnings.warn(
    "skill_fleet.llm.fleet_config is deprecated, use skill_fleet.core.dspy.fleet_config instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "FleetConfigError",
    "TaskLMResolution",
    "build_lm_for_task",
    "load_fleet_config",
    "resolve_model_key",
    "_get_env_value",
    "_get_registry_entry",
    "_model_provider",
    "_resolve_task_lm",
]
