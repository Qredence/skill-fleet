"""Centralized DSPy configuration for skill_fleet.

This module provides a single entry point for configuring DSPy settings
across all skill_fleet modules, ensuring consistent LM usage and settings.

Usage:
    from skill_fleet.llm.dspy_config import configure_dspy

    # Call once at application startup
    configure_dspy()

    # Or with custom config path
    configure_dspy(config_path=Path("custom/config.yaml"))
"""

from __future__ import annotations

import os
from pathlib import Path

import dspy

from ..common.paths import default_config_path
from .fleet_config import build_lm_for_task, load_fleet_config


def configure_dspy(
    config_path: Path | None = None,
    default_task: str = "skill_understand",
) -> dspy.LM:
    """Configure DSPy with fleet config and return default LM.

    This should be called once at application startup to set up
    DSPy's global settings. After calling this function, all DSPy
    modules will use the configured LM by default.

    Args:
        config_path: Path to config/config.yaml (default: project root)
        default_task: Default task to use for dspy.settings.lm
                      (e.g., "skill_understand", "skill_edit", "skill_plan")

    Returns:
        The configured LM instance (also set as dspy.settings.lm)

    Example:
        >>> from skill_fleet.llm.dspy_config import configure_dspy
        >>> lm = configure_dspy()
        >>> # Now all DSPy modules use this LM by default
    """
    if config_path is None:
        config_path = default_config_path()

    config = load_fleet_config(config_path)
    lm = build_lm_for_task(config, default_task)

    # Set DSPy global settings
    dspy.configure(lm=lm)

    # Optional: Set cache directory from environment if specified
    if cache_dir := os.environ.get("DSPY_CACHEDIR"):
        dspy.settings.configure(cache_dir=Path(cache_dir))

    # Optional: Set temperature override if specified
    if temp_str := os.environ.get("DSPY_TEMPERATURE"):
        try:
            temp = float(temp_str)
            lm.kwargs["temperature"] = temp
        except ValueError:
            pass

    return lm


def get_task_lm(task_name: str, config_path: Path | None = None) -> dspy.LM:
    """Get an LM for a specific task without changing global settings.

    Use this when you need a task-specific LM temporarily.
    For persistent task-specific LMs, use dspy.context() instead.

    Args:
        task_name: Task name from config (e.g., "skill_understand", "skill_edit")
        config_path: Path to config/config.yaml (default: project root)

    Returns:
        Configured LM for the specified task

    Example:
        >>> from skill_fleet.llm.dspy_config import get_task_lm
        >>> lm = get_task_lm("skill_edit")
        >>> with dspy.context(lm=lm):
        ...     result = my_module(**inputs)
    """
    if config_path is None:
        config_path = default_config_path()

    config = load_fleet_config(config_path)
    return build_lm_for_task(config, task_name)


__all__ = ["configure_dspy", "get_task_lm"]
