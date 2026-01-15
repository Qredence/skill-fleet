"""Unit tests for core.config module.

This module tests configuration loading from YAML, validation of invalid
configurations, model resolution hierarchy, parameter merging logic,
environment variable overrides, and error handling paths.
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from skill_fleet.common.exceptions import ConfigurationError
from skill_fleet.core.config import (
    FleetConfig,
    ModelConfig,
    ModelParameters,
    ModelsConfig,
    ModelType,
    ReasoningEffort,
    RoleConfig,
    RolesConfig,
    TaskConfig,
    TasksConfig,
    load_config,
    validate_config,
)


class TestModelType:
    """Test ModelType enum."""

    def test_model_type_values(self):
        """Test that ModelType has expected values."""
        assert ModelType.CHAT == "chat"
        assert ModelType.COMPLETION == "completion"


class TestReasoningEffort:
    """Test ReasoningEffort enum."""

    def test_reasoning_effort_values(self):
        """Test that ReasoningEffort has expected values."""
        assert ReasoningEffort.LOW == "low"
        assert ReasoningEffort.MEDIUM == "medium"
        assert ReasoningEffort.HIGH == "high"


class TestModelParameters:
    """Test ModelParameters validation."""

    def test_default_initialization(self):
        """Test ModelParameters with default values."""
        params = ModelParameters()
        assert params.temperature is None
        assert params.max_tokens is None
        assert params.reasoning_effort is None
        assert params.thinking_level is None

    def test_valid_temperature_range(self):
        """Test valid temperature values."""
        params = ModelParameters(temperature=0.0)
        assert params.temperature == 0.0

        params = ModelParameters(temperature=1.0)
        assert params.temperature == 1.0

        params = ModelParameters(temperature=2.0)
        assert params.temperature == 2.0

    def test_invalid_temperature_range(self):
        """Test that invalid temperature raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModelParameters(temperature=-0.1)

        with pytest.raises(ValidationError):
            ModelParameters(temperature=2.1)

    def test_valid_max_tokens(self):
        """Test valid max_tokens values."""
        params = ModelParameters(max_tokens=1000)
        assert params.max_tokens == 1000

        params = ModelParameters(max_tokens=128000)
        assert params.max_tokens == 128000

    def test_invalid_max_tokens(self):
        """Test that invalid max_tokens raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModelParameters(max_tokens=0)

        with pytest.raises(ValidationError):
            ModelParameters(max_tokens=-1)

        with pytest.raises(ValidationError):
            ModelParameters(max_tokens=128001)

    def test_thinking_level_range(self):
        """Test valid thinking_level values."""
        params = ModelParameters(thinking_level=1)
        assert params.thinking_level == 1

        params = ModelParameters(thinking_level=10)
        assert params.thinking_level == 10

    def test_invalid_thinking_level(self):
        """Test that invalid thinking_level raises ValidationError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModelParameters(thinking_level=0)

        with pytest.raises(ValidationError):
            ModelParameters(thinking_level=11)


class TestModelConfig:
    """Test ModelConfig validation."""

    def test_minimal_model_config(self):
        """Test ModelConfig with minimal required fields."""
        config = ModelConfig(model="gpt-4")
        assert config.model == "gpt-4"
        assert config.model_type == ModelType.CHAT
        assert config.timeout == 60
        assert config.parameters.temperature is None

    def test_complete_model_config(self):
        """Test ModelConfig with all fields."""
        params = ModelParameters(temperature=0.7, max_tokens=2000)
        config = ModelConfig(
            model="gemini/gemini-3-flash",
            model_type=ModelType.CHAT,
            env="GOOGLE_API_KEY",
            base_url_env="GOOGLE_BASE_URL",
            base_url_default="https://api.google.com",
            env_fallback="OPENAI_API_KEY",
            timeout=120,
            parameters=params,
        )
        assert config.model == "gemini/gemini-3-flash"
        assert config.env == "GOOGLE_API_KEY"
        assert config.timeout == 120
        assert config.parameters.temperature == 0.7

    def test_env_validator_with_missing_env(self):
        """Test that env validator warns about missing environment variable."""
        # This should work but may emit a warning
        with pytest.warns(UserWarning, match="Environment variable .* is not set"):
            config = ModelConfig(model="gpt-4", env="NONEXISTENT_API_KEY")
            assert config.env == "NONEXISTENT_API_KEY"

    def test_thinking_level_with_wrong_temperature(self):
        """Test thinking_level validator with non-1.0 temperature."""
        params = ModelParameters(thinking_level=5, temperature=0.5)
        with pytest.warns(UserWarning, match="thinking_level.*temperature"):
            config = ModelConfig(model="test-model", parameters=params)
            assert config.parameters.thinking_level == 5
            assert config.parameters.temperature == 0.5


class TestModelsConfig:
    """Test ModelsConfig validation."""

    def test_minimal_models_config(self):
        """Test ModelsConfig with minimal configuration."""
        model = ModelConfig(model="gpt-4")
        config = ModelsConfig(default="gpt-4", registry={"gpt-4": model})
        assert config.default == "gpt-4"
        assert "gpt-4" in config.registry

    def test_default_model_must_exist_in_registry(self):
        """Test that default model must exist in registry."""
        model = ModelConfig(model="gpt-4")
        with pytest.raises(ValueError, match="Default model.*not found in registry"):
            ModelsConfig(default="nonexistent-model", registry={"gpt-4": model})

    def test_multiple_models_in_registry(self):
        """Test ModelsConfig with multiple models."""
        models = {
            "gpt-4": ModelConfig(model="gpt-4"),
            "gemini": ModelConfig(model="gemini/gemini-3-flash"),
        }
        config = ModelsConfig(default="gpt-4", registry=models)
        assert len(config.registry) == 2
        assert "gpt-4" in config.registry
        assert "gemini" in config.registry


class TestRoleConfig:
    """Test RoleConfig validation."""

    def test_minimal_role_config(self):
        """Test RoleConfig with minimal fields."""
        role = RoleConfig(model="gpt-4")
        assert role.model == "gpt-4"
        assert role.description == ""
        assert role.capabilities == []

    def test_complete_role_config(self):
        """Test RoleConfig with all fields."""
        params = ModelParameters(temperature=0.9)
        role = RoleConfig(
            model="gpt-4",
            description="Router role",
            capabilities=["routing", "decision-making"],
            parameter_overrides=params,
        )
        assert role.model == "gpt-4"
        assert role.description == "Router role"
        assert len(role.capabilities) == 2
        assert role.parameter_overrides.temperature == 0.9


class TestRolesConfig:
    """Test RolesConfig validation."""

    def test_empty_roles_config(self):
        """Test RolesConfig with no roles defined."""
        config = RolesConfig()
        assert config.router is None
        assert config.planner is None
        assert config.worker is None
        assert config.judge is None

    def test_known_roles(self):
        """Test RolesConfig with known roles."""
        config = RolesConfig(
            router=RoleConfig(model="gpt-4"),
            planner=RoleConfig(model="gemini"),
        )
        assert config.router is not None
        assert config.router.model == "gpt-4"
        assert config.planner is not None
        assert config.planner.model == "gemini"

    def test_get_role_method(self):
        """Test get_role method for known roles."""
        config = RolesConfig(router=RoleConfig(model="gpt-4"))
        role = config.get_role("router")
        assert role is not None
        assert role.model == "gpt-4"

        role = config.get_role("nonexistent")
        assert role is None

    def test_dictionary_access(self):
        """Test dictionary-like access to roles."""
        config = RolesConfig(worker=RoleConfig(model="claude"))
        assert config["worker"] is not None
        assert config["worker"].model == "claude"
        assert config["nonexistent"] is None

    def test_extra_roles_allowed(self):
        """Test that extra roles can be added dynamically."""
        # With ConfigDict(extra="allow"), we should be able to add custom roles
        data = {
            "router": {"model": "gpt-4"},
            "custom_role": {"model": "custom-model"},
        }
        config = RolesConfig(**data)
        # The custom_role should be accessible
        assert config.get_role("custom_role") is not None


class TestTaskConfig:
    """Test TaskConfig validation."""

    def test_task_with_model(self):
        """Test TaskConfig with model specified."""
        task = TaskConfig(model="gpt-4")
        assert task.model == "gpt-4"
        assert task.role is None

    def test_task_with_role(self):
        """Test TaskConfig with role specified."""
        task = TaskConfig(role="worker")
        assert task.role == "worker"
        assert task.model is None

    def test_task_with_both_model_and_role(self):
        """Test TaskConfig with both model and role."""
        task = TaskConfig(model="gpt-4", role="worker")
        assert task.model == "gpt-4"
        assert task.role == "worker"

    def test_task_with_neither_model_nor_role(self):
        """Test TaskConfig with neither model nor role (allowed for defaults)."""
        # The validator was relaxed to allow empty TaskConfig instances
        # Validation happens at model resolution time
        TaskConfig()  # Should not raise


class TestTasksConfig:
    """Test TasksConfig validation."""

    def test_empty_tasks_config(self):
        """Test TasksConfig with no tasks defined."""
        config = TasksConfig()
        assert config.skill_understand is None
        assert config.skill_plan is None

    def test_known_tasks(self):
        """Test TasksConfig with known tasks."""
        config = TasksConfig(
            skill_understand=TaskConfig(model="gpt-4"),
            skill_plan=TaskConfig(role="planner"),
        )
        assert config.skill_understand is not None
        assert config.skill_plan is not None

    def test_get_task_method(self):
        """Test get_task method for known tasks."""
        config = TasksConfig(skill_understand=TaskConfig(model="gpt-4"))
        task = config.get_task("skill_understand")
        assert task is not None
        assert task.model == "gpt-4"

        task = config.get_task("nonexistent")
        assert task is None

    def test_dictionary_access(self):
        """Test dictionary-like access to tasks."""
        config = TasksConfig(skill_edit=TaskConfig(model="claude"))
        assert config["skill_edit"] is not None
        assert config["skill_edit"].model == "claude"

    def test_extra_tasks_allowed(self):
        """Test that extra tasks can be added dynamically."""
        data = {
            "skill_understand": {"model": "gpt-4"},
            "custom_task": {"model": "custom-model"},
        }
        config = TasksConfig(**data)
        assert config.get_task("custom_task") is not None


class TestFleetConfig:
    """Test FleetConfig validation and loading."""

    def test_minimal_fleet_config(self):
        """Test FleetConfig with minimal configuration."""
        models = ModelsConfig(
            default="gpt-4",
            registry={"gpt-4": ModelConfig(model="gpt-4")},
        )
        config = FleetConfig(models=models)
        assert config.models.default == "gpt-4"
        assert config.roles is not None
        assert config.tasks is not None

    def test_complete_fleet_config(self):
        """Test FleetConfig with all sections."""
        models = ModelsConfig(
            default="gpt-4",
            registry={"gpt-4": ModelConfig(model="gpt-4")},
        )
        roles = RolesConfig(router=RoleConfig(model="gpt-4"))
        tasks = TasksConfig(skill_understand=TaskConfig(model="gpt-4"))
        config = FleetConfig(models=models, roles=roles, tasks=tasks)
        assert config.models.default == "gpt-4"
        assert config.roles.router is not None
        assert config.tasks.skill_understand is not None

    def test_from_dict_valid(self):
        """Test FleetConfig.from_dict with valid data."""
        data = {
            "models": {
                "default": "gpt-4",
                "registry": {"gpt-4": {"model": "gpt-4"}},
            }
        }
        config = FleetConfig.from_dict(data)
        assert config.models.default == "gpt-4"

    def test_from_dict_invalid(self):
        """Test FleetConfig.from_dict with invalid data."""
        data = {"invalid": "data"}
        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            FleetConfig.from_dict(data)

    def test_from_dict_preserves_validation_errors(self):
        """Test that from_dict preserves Pydantic validation errors."""
        data = {
            "models": {
                "default": "nonexistent",
                "registry": {"gpt-4": {"model": "gpt-4"}},
            }
        }
        with pytest.raises(ConfigurationError) as exc_info:
            FleetConfig.from_dict(data)

        error = exc_info.value
        # Check that validation errors are in the error message
        assert "error(s) found" in str(error) or "Default model" in str(error)

    def test_from_yaml_file_not_found(self):
        """Test FleetConfig.from_yaml with nonexistent file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            FleetConfig.from_yaml("/nonexistent/path/config.yaml")

    def test_from_yaml_invalid_yaml(self):
        """Test FleetConfig.from_yaml with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content:\n  - broken")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Failed to read configuration"):
                FleetConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_non_dict_root(self):
        """Test FleetConfig.from_yaml with non-dict root."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- list\n- of\n- items")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="expected mapping at root"):
                FleetConfig.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_valid(self):
        """Test FleetConfig.from_yaml with valid YAML file."""
        config_data = {
            "models": {
                "default": "gpt-4",
                "registry": {
                    "gpt-4": {
                        "model": "gpt-4",
                        "model_type": "chat",
                        "timeout": 60,
                    }
                },
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = FleetConfig.from_yaml(temp_path)
            assert config.models.default == "gpt-4"
            assert "gpt-4" in config.models.registry
        finally:
            os.unlink(temp_path)

    def test_to_dict(self):
        """Test FleetConfig.to_dict method."""
        models = ModelsConfig(
            default="gpt-4",
            registry={"gpt-4": ModelConfig(model="gpt-4")},
        )
        config = FleetConfig(models=models)
        data = config.to_dict()
        assert isinstance(data, dict)
        assert "models" in data
        assert data["models"]["default"] == "gpt-4"


class TestModelResolution:
    """Test get_model_config model resolution hierarchy."""

    def test_model_resolution_from_task(self):
        """Test model resolution when task specifies a model."""
        models = ModelsConfig(
            default="default-model",
            registry={
                "default-model": ModelConfig(model="default-model"),
                "task-model": ModelConfig(model="task-model"),
            },
        )
        tasks = TasksConfig(skill_understand=TaskConfig(model="task-model"))
        config = FleetConfig(models=models, tasks=tasks)

        model_key, model_config, params = config.get_model_config("skill_understand")
        assert model_key == "task-model"
        assert model_config.model == "task-model"

    def test_model_resolution_from_role(self):
        """Test model resolution when task specifies a role."""
        models = ModelsConfig(
            default="default-model",
            registry={
                "default-model": ModelConfig(model="default-model"),
                "role-model": ModelConfig(model="role-model"),
            },
        )
        roles = RolesConfig(worker=RoleConfig(model="role-model"))
        tasks = TasksConfig(skill_understand=TaskConfig(role="worker"))
        config = FleetConfig(models=models, roles=roles, tasks=tasks)

        model_key, model_config, params = config.get_model_config("skill_understand")
        assert model_key == "role-model"

    def test_model_resolution_default(self):
        """Test model resolution falls back to default."""
        models = ModelsConfig(
            default="default-model",
            registry={"default-model": ModelConfig(model="default-model")},
        )
        config = FleetConfig(models=models)

        model_key, model_config, params = config.get_model_config("unknown_task")
        assert model_key == "default-model"

    def test_model_resolution_env_override(self):
        """Test model resolution with environment variable override."""
        os.environ["FLEET_MODEL_SKILL_UNDERSTAND"] = "env-model"

        models = ModelsConfig(
            default="default-model",
            registry={
                "default-model": ModelConfig(model="default-model"),
                "env-model": ModelConfig(model="env-model"),
            },
        )
        config = FleetConfig(models=models)

        try:
            model_key, model_config, params = config.get_model_config("skill_understand")
            assert model_key == "env-model"
        finally:
            del os.environ["FLEET_MODEL_SKILL_UNDERSTAND"]

    def test_model_resolution_model_not_in_registry(self):
        """Test error when resolved model not in registry."""
        models = ModelsConfig(
            default="default-model",
            registry={"default-model": ModelConfig(model="default-model")},
        )
        tasks = TasksConfig(skill_understand=TaskConfig(model="nonexistent"))
        config = FleetConfig(models=models, tasks=tasks)

        with pytest.raises(ConfigurationError, match="Model.*not found in registry"):
            config.get_model_config("skill_understand")


class TestParameterMerging:
    """Test parameter merging logic in get_model_config."""

    def test_parameter_merging_model_defaults(self):
        """Test that model default parameters are used."""
        params = ModelParameters(temperature=0.5, max_tokens=1000)
        models = ModelsConfig(
            default="test-model",
            registry={"test-model": ModelConfig(model="test-model", parameters=params)},
        )
        config = FleetConfig(models=models)

        _, _, merged = config.get_model_config("unknown_task")
        assert merged.temperature == 0.5
        assert merged.max_tokens == 1000

    def test_parameter_merging_role_overrides(self):
        """Test that role parameter overrides are applied."""
        model_params = ModelParameters(temperature=0.5)
        role_params = ModelParameters(temperature=0.9)

        models = ModelsConfig(
            default="test-model",
            registry={"test-model": ModelConfig(model="test-model", parameters=model_params)},
        )
        roles = RolesConfig(worker=RoleConfig(model="test-model", parameter_overrides=role_params))
        tasks = TasksConfig(skill_understand=TaskConfig(role="worker"))
        config = FleetConfig(models=models, roles=roles, tasks=tasks)

        _, _, merged = config.get_model_config("skill_understand")
        assert merged.temperature == 0.9

    def test_parameter_merging_task_overrides(self):
        """Test that task parameters override role and model."""
        model_params = ModelParameters(temperature=0.5)
        role_params = ModelParameters(temperature=0.7)
        task_params = ModelParameters(temperature=0.9)

        models = ModelsConfig(
            default="test-model",
            registry={"test-model": ModelConfig(model="test-model", parameters=model_params)},
        )
        roles = RolesConfig(worker=RoleConfig(model="test-model", parameter_overrides=role_params))
        tasks = TasksConfig(
            skill_understand=TaskConfig(role="worker", parameters=task_params)
        )
        config = FleetConfig(models=models, roles=roles, tasks=tasks)

        _, _, merged = config.get_model_config("skill_understand")
        assert merged.temperature == 0.9

    def test_parameter_merging_env_override(self):
        """Test that DSPY_TEMPERATURE environment variable overrides everything."""
        os.environ["DSPY_TEMPERATURE"] = "1.5"

        params = ModelParameters(temperature=0.5)
        models = ModelsConfig(
            default="test-model",
            registry={"test-model": ModelConfig(model="test-model", parameters=params)},
        )
        config = FleetConfig(models=models)

        try:
            _, _, merged = config.get_model_config("unknown_task")
            assert merged.temperature == 1.5
        finally:
            del os.environ["DSPY_TEMPERATURE"]

    def test_parameter_merging_invalid_env_temperature(self):
        """Test error when DSPY_TEMPERATURE is invalid."""
        os.environ["DSPY_TEMPERATURE"] = "invalid"

        models = ModelsConfig(
            default="test-model",
            registry={"test-model": ModelConfig(model="test-model")},
        )
        config = FleetConfig(models=models)

        try:
            with pytest.raises(ConfigurationError, match="DSPY_TEMPERATURE must be a valid float"):
                config.get_model_config("unknown_task")
        finally:
            del os.environ["DSPY_TEMPERATURE"]


class TestConvenienceFunctions:
    """Test load_config and validate_config convenience functions."""

    def test_load_config_default_path(self):
        """Test load_config with default path (if exists)."""
        # This test will fail if config/config.yaml doesn't exist
        # We'll skip it if the file doesn't exist
        default_path = Path("config/config.yaml")
        if not default_path.exists():
            pytest.skip("Default config file not found")

        config = load_config()
        assert isinstance(config, FleetConfig)

    def test_validate_config_valid(self):
        """Test validate_config with valid config file."""
        config_data = {
            "models": {
                "default": "gpt-4",
                "registry": {"gpt-4": {"model": "gpt-4"}},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            result = validate_config(temp_path)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_validate_config_invalid(self):
        """Test validate_config with invalid config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: data")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError):
                validate_config(temp_path)
        finally:
            os.unlink(temp_path)
