"""LLM configuration helpers for `skill_fleet`.

This package loads `config/config.yaml` and produces `dspy.LM` instances
for tasks/roles, using the config as the single source of truth.
"""

from __future__ import annotations

from .fleet_config import FleetConfigError, build_lm_for_task, load_fleet_config

__all__ = [
    "FleetConfigError",
    "build_lm_for_task",
    "load_fleet_config",
]
