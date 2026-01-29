"""
Centralized DSPy configuration for skill-fleet.

This module provides DSPy LM configuration and management.
All DSPy setup should go through this module.

Usage:
    from skill_fleet.dspy import configure_dspy, get_task_lm

    # Configure at startup
    configure_dspy()

    # Get LM for specific task
    lm = get_task_lm("understanding")
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import dspy
import yaml


def load_fleet_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load fleet configuration from YAML file.

    Args:
        config_path: Path to config file (default: config/config.yaml)

    Returns:
        Configuration dictionary

    """
    if config_path is None:
        # Try to find config in standard locations
        candidates = [
            Path.cwd() / "config" / "config.yaml",
            Path(__file__).parent.parent.parent / "config" / "config.yaml",
        ]
        for candidate in candidates:
            if candidate.exists():
                config_path = candidate
                break

    if config_path and config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    return {}


def build_lm_for_task(task: str, config: dict[str, Any] | None = None) -> dspy.LM:
    """
    Build LM optimized for specific task.

    Args:
        task: Task type (understanding, generation, validation, hitl)
        config: Optional configuration override

    Returns:
        Configured LM instance

    """
    cfg = config or load_fleet_config()

    # Task-specific defaults
    task_configs = {
        "understanding": {"model": "google/gemini-3-flash", "temperature": 0.5},
        "generation": {"model": "google/gemini-3-pro", "temperature": 0.7},
        "validation": {"model": "google/gemini-3-flash", "temperature": 0.3},
        "hitl": {"model": "google/gemini-3-flash", "temperature": 0.5},
    }

    task_config = task_configs.get(task, task_configs["understanding"])

    # Override from config if present
    if cfg and "llm" in cfg:
        llm_cfg = cfg["llm"]
        if "default_model" in llm_cfg:
            task_config["model"] = llm_cfg["default_model"]
        if "temperature" in llm_cfg:
            task_config["temperature"] = llm_cfg["temperature"]

    # Override from environment
    if model := os.getenv("DSPY_MODEL"):
        task_config["model"] = model
    if temp := os.getenv("DSPY_TEMPERATURE"):
        task_config["temperature"] = float(temp)

    return dspy.LM(**task_config)


def configure_dspy(
    config_path: Path | None = None,
    default_model: str | None = None,
    temperature: float | None = None,
) -> dspy.LM:
    """
    Configure DSPy with fleet settings.

    Call this once at application startup.

    Args:
        config_path: Path to config file
        default_model: Override default model
        temperature: Override temperature

    Returns:
        Configured default LM

    """
    cfg = load_fleet_config(config_path)

    # Build default LM
    lm_config = {"model": "google/gemini-3-flash", "temperature": 0.7}

    if cfg and "llm" in cfg:
        lm_cfg = cfg["llm"]
        if "default_model" in lm_cfg:
            lm_config["model"] = lm_cfg["default_model"]
        if "temperature" in lm_cfg:
            lm_config["temperature"] = lm_cfg["temperature"]

    # Apply overrides
    if default_model:
        lm_config["model"] = default_model
    if temperature is not None:
        lm_config["temperature"] = temperature

    # Environment overrides
    if model := os.getenv("DSPY_MODEL"):
        lm_config["model"] = model
    if temp := os.getenv("DSPY_TEMPERATURE"):
        lm_config["temperature"] = float(temp)

    lm = dspy.LM(**lm_config)
    dspy.configure(lm=lm)

    return lm


def get_task_lm(task: str) -> dspy.LM:
    """
    Get LM optimized for specific task.

    Args:
        task: Task type (understanding, generation, validation, hitl)

    Returns:
        Task-optimized LM

    """
    return build_lm_for_task(task)


# Export main functions
__all__ = ["configure_dspy", "get_task_lm", "build_lm_for_task", "load_fleet_config"]
