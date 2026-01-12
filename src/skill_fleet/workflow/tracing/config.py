"""Reasoning model configuration for skill creation workflow.

Uses the existing model registry from config.yaml:
- Default: gemini:gemini-3-flash-preview (with thinking_level parameter support)
- Role: planner (for Phase 1 and Phase 2 decision modules)
- Tasks: skill_understand, skill_plan with their own thinking_level settings

The existing config already provides reasoning support via the 'thinking_level' parameter.
This module provides a ConfigModelLoader class that loads models from config.yaml
and creates DSPy LM instances with proper configuration.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

import dspy
import yaml

from ...common.paths import default_config_path

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class ConfigModelLoader:
    """Load and configure models from existing config.yaml.

    This class reads the skill-fleet config.yaml file and provides
    task-specific model configurations with role-based parameter overrides.

    The config.yaml structure:
    - models.default: Default model reference (e.g., "gemini:gemini-3-flash-preview")
    - models.registry: Model configurations keyed by model reference
    - roles: Role-based parameter overrides (router, planner, worker, judge)
    - tasks: Task-specific model and role assignments

    Example config.yaml:
        models:
          default: gemini:gemini-3-flash-preview
          registry:
            gemini:gemini-3-flash-preview:
              model: gemini-3-flash-preview
              model_type: chat
              env: GOOGLE_API_KEY
              parameters:
                temperature: 1.0
                max_tokens: 8192
        roles:
          planner:
            parameter_overrides:
              thinking_level: medium
        tasks:
          skill_understand:
            model: gemini:gemini-3-flash-preview
            role: planner
            parameters:
              thinking_level: medium
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize ConfigModelLoader.

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = config_path or default_config_path()
        self.config = self._load_config()

    def _load_config(self) -> Mapping:
        """Load config.yaml file.

        Returns:
            Parsed YAML configuration as a dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def get_model_for_task(self, task_name: str) -> dspy.LM:
        """Get DSPy LM instance for a specific task from config.yaml.

        This method:
        1. Looks up the task configuration in config.yaml
        2. Resolves the model reference (e.g., "gemini:gemini-3-flash-preview")
        3. Applies role-based parameter overrides if specified
        4. Creates a configured DSPy LM instance

        Args:
            task_name: Task name (e.g., 'skill_understand', 'skill_plan')

        Returns:
            Configured dspy.LM instance

        Raises:
            ValueError: If task or model is not found in config
        """
        task_config = self.config.get("tasks", {}).get(task_name, {})

        if not task_config:
            logger.warning(f"Task '{task_name}' not found in config, using default model")
            model_ref = self.config.get("models", {}).get("default", "")
            model_config = self._resolve_model_ref(model_ref)
        else:
            model_ref = task_config.get("model", "")
            role = task_config.get("role")
            model_config = self._resolve_model_ref(model_ref, role)

        # Merge task-specific parameters if present
        task_params = task_config.get("parameters", {})
        if task_params:
            base_params = model_config.get("parameters", {})
            model_config = model_config.copy()
            model_config["parameters"] = {**base_params, **task_params}

        # Create DSPy LM from model config
        return dspy.LM(
            model=model_config.get("model", model_ref),
            api_key=self._get_api_key(model_config),
            **model_config.get("parameters", {}),
        )

    def _resolve_model_ref(self, model_ref: str, role: str | None = None) -> dict:
        """Resolve model reference (e.g., 'gemini:gemini-3-flash-preview').

        Args:
            model_ref: Model reference string (provider:model format)
            role: Optional role name for parameter overrides

        Returns:
            Model configuration dictionary

        Raises:
            ValueError: If model reference is not found in registry
        """
        model_config = self.config.get("models", {}).get("registry", {}).get(model_ref)

        if not model_config:
            raise ValueError(f"Model '{model_ref}' not found in config registry")

        # Apply role parameter overrides if specified
        if role and role in self.config.get("roles", {}):
            role_config = self.config["roles"][role]
            overrides = role_config.get("parameter_overrides", {})
            if overrides:
                # Merge overrides with base parameters
                base_params = model_config.get("parameters", {})
                model_config = model_config.copy()
                model_config["parameters"] = {**base_params, **overrides}
                logger.debug(f"Applied role '{role}' parameter overrides: {overrides}")

        return model_config

    def _get_api_key(self, model_config: dict) -> str:
        """Get API key from environment variable specified in config.

        Args:
            model_config: Model configuration dictionary

        Returns:
            API key string (empty if not configured)
        """
        # Prefer LITELLM proxy credentials when available
        from ...common.env_utils import resolve_api_credentials

        # If the model config explicitly points to an env var, honor that first
        env_var = model_config.get("env")
        if env_var:
            api_key = os.environ.get(env_var, "")
            if api_key:
                return api_key
            logger.debug(
                f"Configured env var '{env_var}' not set, falling back to resolution logic"
            )

        creds = resolve_api_credentials(prefer_litellm=True)
        api_key = creds.get("api_key", "")
        if not api_key:
            logger.warning(
                "No API key found in environment (LITELLM_API_KEY or GOOGLE_API_KEY/GEMINI_API_KEY)"
            )
        return api_key


# Singleton instance
_config_loader: ConfigModelLoader | None = None


def get_reasoning_lm(task_name: str = "skill_understand") -> dspy.LM:
    """Get reasoning LM for a specific task.

    Uses the existing config.yaml model registry and role-based configuration.
    Phase 1 and Phase 2 will use the 'planner' role with thinking_level overrides.

    Args:
        task_name: Task name from config.yaml (default: 'skill_understand' for Phase 1)

    Returns:
        Configured dspy.LM instance with reasoning parameters

    Examples:
        Get Phase 1 LM (understand task with planner role, thinking_level: medium):
        >>> lm = get_reasoning_lm("skill_understand")

        Get Phase 2 LM (plan task with planner role, thinking_level: high):
        >>> lm = get_reasoning_lm("skill_plan")
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigModelLoader()
    return _config_loader.get_model_for_task(task_name)


def get_phase1_lm() -> dspy.LM:
    """Get LM for Phase 1: Understand task.

    Uses the 'skill_understand' task configuration which includes:
    - Model: gemini:gemini-3-flash-preview
    - Role: planner
    - Parameters: thinking_level: medium

    Returns:
        Configured dspy.LM instance for Phase 1

    Examples:
        >>> lm = get_phase1_lm()
        >>> dspy.configure(lm=lm)
    """
    return get_reasoning_lm("skill_understand")


def get_phase2_lm() -> dspy.LM:
    """Get LM for Phase 2: Plan task.

    Uses the 'skill_plan' task configuration which includes:
    - Model: gemini:gemini-3-flash-preview
    - Role: planner
    - Parameters: thinking_level: high

    Returns:
        Configured dspy.LM instance for Phase 2

    Examples:
        >>> lm = get_phase2_lm()
        >>> dspy.configure(lm=lm)
    """
    return get_reasoning_lm("skill_plan")


# Convenience functions for other phases
def get_phase3_lm() -> dspy.LM:
    """Get LM for Phase 3: Initialize task (worker role, thinking_level: minimal)."""
    return get_reasoning_lm("skill_initialize")


def get_phase4_lm() -> dspy.LM:
    """Get LM for Phase 4: Edit task (worker role, thinking_level: high)."""
    return get_reasoning_lm("skill_edit")


def get_phase5_lm() -> dspy.LM:
    """Get LM for Phase 5: Package task (worker role, thinking_level: medium)."""
    return get_reasoning_lm("skill_package")


__all__ = [
    "ConfigModelLoader",
    "get_reasoning_lm",
    "get_phase1_lm",
    "get_phase2_lm",
    "get_phase3_lm",
    "get_phase4_lm",
    "get_phase5_lm",
]
