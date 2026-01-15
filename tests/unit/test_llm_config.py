"""Tests for LLM configuration and DSPy setup."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch  # noqa: F401

import pytest

from skill_fleet.llm.fleet_config import (
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


class TestLoadFleetConfig:
    """Tests for load_fleet_config function."""

    def test_loads_valid_yaml_config(self, tmp_path: Path):
        """Test loading a valid YAML configuration file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
models:
  default: gemini:gemini-2.0-flash
  registry:
    gemini:gemini-2.0-flash:
      model_type: gemini
tasks:
  skill_understand:
    role: analyst
""",
            encoding="utf-8",
        )

        result = load_fleet_config(config_file)

        assert isinstance(result, dict)
        assert "models" in result
        assert "tasks" in result
        assert result["models"]["default"] == "gemini:gemini-2.0-flash"

    def test_raises_error_for_non_dict_root(self, tmp_path: Path):
        """Test that non-dict root raises FleetConfigError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("- item1\n- item2", encoding="utf-8")

        with pytest.raises(FleetConfigError, match="expected mapping at root"):
            load_fleet_config(config_file)

    def test_raises_error_for_missing_file(self, tmp_path: Path):
        """Test that missing file raises appropriate error."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_fleet_config(config_file)


class TestResolveModelKey:
    """Tests for resolve_model_key function."""

    def test_resolves_legacy_alias(self):
        """Test resolving a legacy model alias."""
        config = {
            "legacy_aliases": {
                "gpt4": "openai:gpt-4-turbo",
                "claude": "anthropic:claude-3-opus",
            }
        }

        result = resolve_model_key(config, "gpt4")
        assert result == "openai:gpt-4-turbo"

    def test_returns_original_if_no_alias(self):
        """Test that original key is returned if no alias exists."""
        config = {"legacy_aliases": {"gpt4": "openai:gpt-4-turbo"}}

        result = resolve_model_key(config, "gemini:gemini-2.0-flash")
        assert result == "gemini:gemini-2.0-flash"

    def test_handles_missing_legacy_aliases(self):
        """Test handling config without legacy_aliases section."""
        config = {"models": {"default": "gemini:gemini-2.0-flash"}}

        result = resolve_model_key(config, "some-model")
        assert result == "some-model"

    def test_handles_non_dict_legacy_aliases(self):
        """Test handling non-dict legacy_aliases value."""
        config = {"legacy_aliases": "not-a-dict"}

        result = resolve_model_key(config, "some-model")
        assert result == "some-model"


class TestGetEnvValue:
    """Tests for _get_env_value function."""

    def test_returns_primary_env_value(self):
        """Test returning primary environment variable value."""
        with patch.dict(os.environ, {"PRIMARY_VAR": "primary_value"}):
            result = _get_env_value("PRIMARY_VAR", "FALLBACK_VAR")
            assert result == "primary_value"

    def test_returns_fallback_when_primary_missing(self):
        """Test returning fallback when primary is not set."""
        with patch.dict(os.environ, {"FALLBACK_VAR": "fallback_value"}, clear=False):
            # Ensure PRIMARY_VAR is not set
            env = os.environ.copy()
            env.pop("PRIMARY_VAR", None)
            env["FALLBACK_VAR"] = "fallback_value"
            with patch.dict(os.environ, env, clear=True):
                result = _get_env_value("PRIMARY_VAR", "FALLBACK_VAR")
                assert result == "fallback_value"

    def test_returns_none_when_both_missing(self):
        """Test returning None when both vars are missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = _get_env_value("MISSING_VAR", "ALSO_MISSING")
            assert result is None

    def test_returns_none_for_none_inputs(self):
        """Test returning None when inputs are None."""
        result = _get_env_value(None, None)
        assert result is None


class TestModelProvider:
    """Tests for _model_provider function."""

    def test_extracts_provider_from_model_key(self):
        """Test extracting provider from provider:model format."""
        assert _model_provider("gemini:gemini-2.0-flash") == "gemini"
        assert _model_provider("openai:gpt-4-turbo") == "openai"
        assert _model_provider("anthropic:claude-3-opus") == "anthropic"

    def test_extracts_provider_from_litellm_model_key(self):
        """Test extracting provider from provider/model (LiteLLM) format."""
        assert _model_provider("gemini/gemini-3-flash-preview") == "gemini"
        assert _model_provider("openai/gpt-4o-mini") == "openai"

    def test_returns_key_if_no_colon(self):
        """Test returning full key if no colon separator."""
        assert _model_provider("gpt-4-turbo") == "gpt-4-turbo"
        assert _model_provider("claude") == "claude"


class TestGetRegistryEntry:
    """Tests for _get_registry_entry function."""

    def test_returns_registry_entry(self):
        """Test returning a valid registry entry."""
        config = {
            "models": {
                "registry": {
                    "gemini:gemini-2.0-flash": {
                        "model_type": "gemini",
                        "api_key_env": "GOOGLE_API_KEY",
                    }
                }
            }
        }

        result = _get_registry_entry(config, "gemini:gemini-2.0-flash")
        assert result["model_type"] == "gemini"
        assert result["api_key_env"] == "GOOGLE_API_KEY"

    def test_raises_error_for_missing_model(self):
        """Test raising error for missing model key."""
        config = {"models": {"registry": {}}}

        with pytest.raises(FleetConfigError, match="Model key not found"):
            _get_registry_entry(config, "nonexistent:model")

    def test_raises_error_for_non_dict_entry(self):
        """Test raising error for non-dict registry entry."""
        config = {"models": {"registry": {"bad:model": "not-a-dict"}}}

        with pytest.raises(FleetConfigError, match="expected mapping"):
            _get_registry_entry(config, "bad:model")

    def test_handles_missing_models_section(self):
        """Test handling config without models section."""
        config = {"tasks": {}}

        with pytest.raises(FleetConfigError, match="Model key not found"):
            _get_registry_entry(config, "any:model")


class TestResolveTaskLm:
    """Tests for _resolve_task_lm function."""

    def test_resolves_task_with_direct_model(self):
        """Test resolving task with directly specified model."""
        config = {
            "models": {
                "default": "gemini:gemini-2.0-flash",
                "registry": {
                    "openai:gpt-4": {
                        "model_type": "openai",
                        "parameters": {"temperature": 0.7},
                    }
                },
            },
            "tasks": {
                "skill_understand": {
                    "model": "openai:gpt-4",
                }
            },
            "roles": {},
        }

        result = _resolve_task_lm(config, "skill_understand")

        assert isinstance(result, TaskLMResolution)
        assert result.model_key == "openai:gpt-4"
        assert result.model_type == "openai"

    def test_resolves_task_via_role(self):
        """Test resolving task model via role configuration."""
        config = {
            "models": {
                "default": "gemini:gemini-2.0-flash",
                "registry": {
                    "anthropic:claude-3": {
                        "model_type": "anthropic",
                        "parameters": {},
                    }
                },
            },
            "tasks": {
                "skill_edit": {
                    "role": "editor",
                }
            },
            "roles": {
                "editor": {
                    "model": "anthropic:claude-3",
                }
            },
        }

        result = _resolve_task_lm(config, "skill_edit")

        assert result.model_key == "anthropic:claude-3"

    def test_falls_back_to_default_model(self):
        """Test falling back to default model when task has no model."""
        config = {
            "models": {
                "default": "gemini:gemini-2.0-flash",
                "registry": {
                    "gemini:gemini-2.0-flash": {
                        "model_type": "gemini",
                        "parameters": {},
                    }
                },
            },
            "tasks": {"some_task": {}},
            "roles": {},
        }

        result = _resolve_task_lm(config, "some_task")

        assert result.model_key == "gemini:gemini-2.0-flash"

    def test_env_var_overrides_config(self):
        """Test that environment variable overrides config."""
        config = {
            "models": {
                "default": "gemini:gemini-2.0-flash",
                "registry": {
                    "gemini:gemini-2.0-flash": {
                        "model_type": "gemini",
                        "parameters": {},
                    },
                    "openai:gpt-4": {
                        "model_type": "openai",
                        "parameters": {},
                    },
                },
            },
            "tasks": {
                "skill_understand": {
                    "model": "gemini:gemini-2.0-flash",
                }
            },
            "roles": {},
        }

        with patch.dict(os.environ, {"FLEET_MODEL_SKILL_UNDERSTAND": "openai:gpt-4"}):
            result = _resolve_task_lm(config, "skill_understand")

        assert result.model_key == "openai:gpt-4"

    def test_raises_error_when_no_model_found(self):
        """Test raising error when no model can be resolved."""
        config = {
            "models": {},
            "tasks": {},
            "roles": {},
        }

        with pytest.raises(FleetConfigError, match="Unable to resolve model"):
            _resolve_task_lm(config, "unknown_task")


class TestTaskLMResolution:
    """Tests for TaskLMResolution dataclass."""

    def test_creates_resolution_with_all_fields(self):
        """Test creating a TaskLMResolution with all fields."""
        resolution = TaskLMResolution(
            model_key="gemini:gemini-2.0-flash",
            model_type="gemini",
            parameters={"temperature": 0.5},
            timeout=30,
        )

        assert resolution.model_key == "gemini:gemini-2.0-flash"
        assert resolution.model_type == "gemini"
        assert resolution.parameters == {"temperature": 0.5}
        assert resolution.timeout == 30

    def test_resolution_is_frozen(self):
        """Test that TaskLMResolution is immutable."""
        resolution = TaskLMResolution(
            model_key="test",
            model_type="test",
            parameters={},
            timeout=None,
        )

        with pytest.raises(AttributeError):
            resolution.model_key = "new_value"  # ty:ignore[invalid-assignment]


class TestBuildLmForTask:
    """Tests for build_lm_for_task function."""

    def test_builds_valid_gemini_model_from_litellm_registry_key(self):
        """Ensure provider/model keys don't produce triple-segment model strings."""
        config = {
            "models": {
                "default": "gemini/gemini-3-flash-preview",
                "registry": {
                    "gemini/gemini-3-flash-preview": {
                        "model": "gemini-3-flash-preview",
                        "model_type": "chat",
                        "env": "GOOGLE_API_KEY",
                        "env_fallback": "LITELLM_API_KEY",
                        "timeout": 60,
                        "parameters": {"temperature": 1.0, "max_tokens": 8192},
                    },
                },
            },
            "roles": {},
            "tasks": {"skill_understand": {"model": "gemini/gemini-3-flash-preview"}},
        }

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test"}, clear=True):
            with patch("skill_fleet.llm.fleet_config.dspy.LM") as mock_lm:
                mock_lm.return_value = MagicMock()
                build_lm_for_task(config, "skill_understand")

                assert mock_lm.called
                dspy_model = mock_lm.call_args.args[0]
                assert dspy_model == "gemini/gemini-3-flash-preview"
                assert dspy_model != "gemini/gemini-3-flash-preview/gemini-3-flash-preview"
                assert mock_lm.call_args.kwargs["api_key"] == "test"
