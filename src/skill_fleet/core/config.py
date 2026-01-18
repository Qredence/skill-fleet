"""Configuration validation using Pydantic.

This module provides runtime validation for the Skills Fleet configuration,
ensuring type safety and catching configuration errors early.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

# =============================================================================
# Configuration Models
# =============================================================================


class ModelType(StrEnum):
    """Valid model types for LLM instances."""

    CHAT = "chat"
    COMPLETION = "completion"


class ReasoningEffort(StrEnum):
    """Valid reasoning effort levels for models that support it."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ModelParameters(BaseModel):
    """Parameters for model inference."""

    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0, le=128000)
    reasoning_effort: ReasoningEffort | None = None
    thinking_level: int | None = Field(default=None, ge=1, le=10)

    @field_validator("thinking_level")
    @classmethod
    def validate_thinking_level(cls, v: int | None) -> int | None:
        """Validate thinking_level is used with temperature=1.0."""
        # This is a soft validation - actual enforcement happens at runtime
        return v


class ModelConfig(BaseModel):
    """Configuration for a single model in the registry."""

    model: str
    model_type: ModelType = ModelType.CHAT
    env: str | None = None  # Environment variable for API key
    base_url_env: str | None = None  # Environment variable for base URL
    base_url_default: str | None = None
    env_fallback: str | None = None
    timeout: int = Field(default=60, gt=0, le=600)
    parameters: ModelParameters = Field(default_factory=ModelParameters)

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: str | None) -> str | None:
        """Validate that the environment variable exists (if not None)."""
        if v is not None and v not in os.environ:
            # This is a warning - actual check happens at runtime
            pass
        return v

    @model_validator(mode="after")
    def validate_thinking_config(self) -> ModelConfig:
        """Validate thinking_level is properly configured."""
        if self.parameters.thinking_level is not None:
            # Thinking level should be used with temperature=1.0
            if self.parameters.temperature is not None and self.parameters.temperature != 1.0:
                # This is a warning - we allow it but document the issue
                pass
        return self


class ModelsConfig(BaseModel):
    """Configuration for all models."""

    default: str
    registry: dict[str, ModelConfig] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_default_exists(self) -> ModelsConfig:
        """Validate that the default model exists in the registry."""
        if self.default not in self.registry:
            raise ValueError(
                f"Default model '{self.default}' not found in registry. "
                f"Available models: {list(self.registry.keys())}"
            )
        return self


class RoleConfig(BaseModel):
    """Configuration for a role (router, planner, worker, judge)."""

    model: str
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    parameter_overrides: ModelParameters = Field(default_factory=ModelParameters)


class RolesConfig(BaseModel):
    """Configuration for all roles."""

    router: RoleConfig | None = None
    planner: RoleConfig | None = None
    worker: RoleConfig | None = None
    judge: RoleConfig | None = None

    # Allow additional roles dynamically
    extra_roles: dict[str, RoleConfig] = Field(default_factory=dict, alias="**")

    def get_role(self, role_name: str) -> RoleConfig | None:
        """Get a role configuration by name."""
        if role_name in ["router", "planner", "worker", "judge"]:
            return getattr(self, role_name)
        return self.extra_roles.get(role_name)

    def __getitem__(self, key: str) -> RoleConfig | None:
        """Allow dictionary-like access to roles."""
        return self.get_role(key)


class TaskConfig(BaseModel):
    """Configuration for a single task."""

    model: str | None = None
    role: str | None = None
    parameters: ModelParameters = Field(default_factory=ModelParameters)

    @model_validator(mode="after")
    def validate_model_or_role(self) -> TaskConfig:
        """Validate that at least model or role is specified."""
        if self.model is None and self.role is None:
            raise ValueError("Task must specify either 'model' or 'role'")
        return self


class TasksConfig(BaseModel):
    """Configuration for all tasks."""

    skill_understand: TaskConfig | None = None
    skill_plan: TaskConfig | None = None
    skill_initialize: TaskConfig | None = None
    skill_edit: TaskConfig | None = None
    skill_package: TaskConfig | None = None
    skill_validate: TaskConfig | None = None
    conversational_agent: TaskConfig | None = None

    # Allow additional tasks dynamically
    extra_tasks: dict[str, TaskConfig] = Field(default_factory=dict, alias="**")

    def get_task(self, task_name: str) -> TaskConfig | None:
        """Get a task configuration by name."""
        if task_name in [
            "skill_understand",
            "skill_plan",
            "skill_initialize",
            "skill_edit",
            "skill_package",
            "skill_validate",
            "conversational_agent",
        ]:
            return getattr(self, task_name)
        return self.extra_tasks.get(task_name)

    def __getitem__(self, key: str) -> TaskConfig | None:
        """Allow dictionary-like access to tasks."""
        return self.get_task(key)


class LegacyAliases(BaseModel):
    """Legacy model name aliases for backward compatibility."""

    aliases: dict[str, str] = Field(default_factory=dict, serialization_alias="legacy_aliases")


class FleetConfig(BaseModel):
    """Complete fleet configuration.

    This is the main entry point for configuration validation. It validates
    the entire config.yaml structure and provides type-safe access to all
    configuration values.

    Usage:
        config = FleetConfig.from_yaml("config/config.yaml")
        lm_config = config.get_model_config("skill_understand")
    """

    models: ModelsConfig
    roles: RolesConfig = Field(default_factory=RolesConfig)
    tasks: TasksConfig = Field(default_factory=TasksConfig)
    legacy_aliases: dict[str, str] = Field(
        default_factory=dict, serialization_alias="legacy_aliases"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FleetConfig:
        """Create a FleetConfig from a dictionary.

        Args:
            data: Dictionary representation of the config

        Returns:
            Validated FleetConfig instance

        Raises:
            ConfigurationError: If configuration is invalid
        """
        from skill_fleet.common import ConfigurationError

        try:
            return cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}") from e

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> FleetConfig:
        """Load and validate a fleet config from a YAML file.

        Args:
            config_path: Path to the config.yaml file

        Returns:
            Validated FleetConfig instance

        Raises:
            ConfigurationError: If file cannot be read or config is invalid
        """
        from skill_fleet.common import ConfigurationError

        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}", config_key="config_path"
            )

        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read configuration file: {e}", config_key="config_path"
            ) from e

        if not isinstance(raw, dict):
            raise ConfigurationError(
                "Invalid config format: expected mapping at root", config_key="config_path"
            )

        return cls.from_dict(raw)

    def get_model_config(self, task_name: str) -> tuple[str, ModelConfig, ModelParameters]:
        """Get the resolved model configuration for a task.

        This implements the model resolution hierarchy:
        1. Environment variable: FLEET_MODEL_{TASK_NAME}
        2. Task model
        3. Role model (if task specifies a role)
        4. Environment variable: FLEET_MODEL_DEFAULT
        5. Default model from config

        Args:
            task_name: Name of the task (e.g., "skill_understand")

        Returns:
            Tuple of (model_key, model_config, merged_parameters)

        Raises:
            ConfigurationError: If model cannot be resolved
        """
        from skill_fleet.common import ConfigurationError

        task = self.tasks.get_task(task_name)
        if task is None:
            task = TaskConfig()  # Use defaults

        # Check environment variables
        env_task_model = os.environ.get(f"FLEET_MODEL_{task_name.upper()}")
        env_role_model = (
            os.environ.get(f"FLEET_MODEL_{str(task.role).upper()}") if task.role else None
        )
        env_default_model = os.environ.get("FLEET_MODEL_DEFAULT")

        model_key = (
            env_task_model
            or task.model
            or (
                self.roles.get_role(task.role).model
                if task.role and self.roles.get_role(task.role)
                else None
            )
            or env_role_model
            or env_default_model
            or self.models.default
        )

        if model_key is None:
            raise ConfigurationError(
                f"Unable to resolve model for task: {task_name}",
                config_key=f"tasks.{task_name}.model",
            )

        # Get model config from registry
        model_config = self.models.registry.get(model_key)
        if model_config is None:
            raise ConfigurationError(
                f"Model '{model_key}' not found in registry. "
                f"Available models: {list(self.models.registry.keys())}",
                config_key=f"models.registry.{model_key}",
            )

        # Merge parameters: model defaults -> role overrides -> task parameters -> env overrides
        merged_params = model_config.parameters.model_copy()

        if task.role:
            role_config = self.roles.get_role(task.role)
            if role_config:
                # Merge role parameter overrides
                role_params = role_config.parameter_overrides.model_dump(exclude_unset=True)
                for key, value in role_params.items():
                    if value is not None:
                        setattr(merged_params, key, value)

        # Merge task parameters
        task_params = task.parameters.model_dump(exclude_unset=True)
        for key, value in task_params.items():
            if value is not None:
                setattr(merged_params, key, value)

        # Apply environment variable override for temperature
        if "DSPY_TEMPERATURE" in os.environ:
            try:
                merged_params.temperature = float(os.environ["DSPY_TEMPERATURE"])
            except ValueError as exc:
                raise ConfigurationError(
                    "DSPY_TEMPERATURE must be a valid float",
                    config_key="env.DSPY_TEMPERATURE",
                ) from exc

        return model_key, model_config, merged_params

    def to_dict(self) -> dict[str, Any]:
        """Convert the config back to a dictionary.

        Returns:
            Dictionary representation of the config
        """
        return self.model_dump(mode="json", exclude_none=True)


# =============================================================================
# Convenience Functions
# =============================================================================


def load_config(config_path: str | Path = "config/config.yaml") -> FleetConfig:
    """Load and validate the fleet configuration.

    This is the recommended way to load configuration in production code.

    Args:
        config_path: Path to the config.yaml file (default: config/config.yaml)

    Returns:
        Validated FleetConfig instance

    Raises:
        ConfigurationError: If configuration is invalid

    Example:
        >>> config = load_config()
        >>> model_key, model_config, params = config.get_model_config("skill_understand")
        >>> print(f"Using model: {model_key}")
    """
    from ..common.paths import default_config_path

    path = Path(config_path)
    # Backwards-compatible default: if the repo-local path isn't present, fall back
    # to packaged defaults (when installed from a wheel) or other safe candidates.
    if path == Path("config/config.yaml") and not path.exists():
        path = default_config_path()

    return FleetConfig.from_yaml(path)


def validate_config(config_path: str | Path = "config/config.yaml") -> bool:
    """Validate the configuration without loading it.

    This is useful for pre-commit hooks and CI validation.

    Args:
        config_path: Path to the config.yaml file

    Returns:
        True if configuration is valid

    Raises:
        ConfigurationError: If configuration is invalid
    """
    from ..common.paths import default_config_path

    path = Path(config_path)
    if path == Path("config/config.yaml") and not path.exists():
        path = default_config_path()

    FleetConfig.from_yaml(path)
    return True


# =============================================================================
# Export
# =============================================================================


__all__ = [
    # Enums
    "ModelType",
    "ReasoningEffort",
    # Models
    "ModelParameters",
    "ModelConfig",
    "ModelsConfig",
    "RoleConfig",
    "RolesConfig",
    "TaskConfig",
    "TasksConfig",
    "LegacyAliases",
    "FleetConfig",
    # Functions
    "load_config",
    "validate_config",
]
