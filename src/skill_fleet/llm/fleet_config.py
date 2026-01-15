"""Fleet LLM configuration loader and DSPy LM factory.

This module interprets `config/config.yaml` and builds `dspy.LM`
instances using LiteLLM-compatible model strings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dspy
import yaml


class FleetConfigError(RuntimeError):
    """Raised when the fleet config is invalid or cannot be satisfied."""


@dataclass(frozen=True, slots=True)
class TaskLMResolution:
    """Resolved model + parameters for a given task."""

    model_key: str
    model_type: str
    parameters: dict[str, Any]
    timeout: int | None


def load_fleet_config(config_path: Path) -> dict[str, Any]:
    """Load a fleet config YAML file."""
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise FleetConfigError(f"Invalid config format: expected mapping at root: {config_path}")
    return raw


def resolve_model_key(config: dict[str, Any], model_key: str) -> str:
    """Resolve legacy model keys to the canonical `provider:model` format."""
    aliases = config.get("legacy_aliases", {})
    if isinstance(aliases, dict) and model_key in aliases:
        resolved = aliases[model_key]
        if isinstance(resolved, str):
            return resolved
    return model_key


def _get_env_value(primary: str | None, fallback: str | None = None) -> str | None:
    if primary:
        value = os.environ.get(primary)
        if value:
            return value
    if fallback:
        value = os.environ.get(fallback)
        if value:
            return value
    return None


def _model_provider(model_key: str) -> str:
    """Extract provider name from a model registry key.

    Supports both:
    - Fleet-style keys: `provider:model`
    - LiteLLM-style keys: `provider/model`
    """

    if ":" in model_key:
        return model_key.split(":", 1)[0]
    if "/" in model_key:
        return model_key.split("/", 1)[0]
    return model_key


def _get_registry_entry(config: dict[str, Any], model_key: str) -> dict[str, Any]:
    models = config.get("models", {})
    registry = models.get("registry", {}) if isinstance(models, dict) else {}
    if not isinstance(registry, dict) or model_key not in registry:
        raise FleetConfigError(f"Model key not found in registry: {model_key}")
    entry = registry[model_key]
    if not isinstance(entry, dict):
        raise FleetConfigError(f"Invalid registry entry for {model_key}: expected mapping")
    return entry


def _resolve_task_lm(config: dict[str, Any], task_name: str) -> TaskLMResolution:
    tasks = config.get("tasks", {})
    roles = config.get("roles", {})
    models = config.get("models", {})

    task_cfg = tasks.get(task_name, {}) if isinstance(tasks, dict) else {}
    if task_cfg and not isinstance(task_cfg, dict):
        raise FleetConfigError(f"Invalid task config for {task_name}: expected mapping")

    role_name = task_cfg.get("role")
    role_cfg: dict[str, Any] = {}
    if role_name and isinstance(roles, dict):
        candidate = roles.get(role_name, {})
        if isinstance(candidate, dict):
            role_cfg = candidate

    # Model selection (minimal implementation of the documented hierarchy)
    env_task_model = os.environ.get(f"FLEET_MODEL_{task_name.upper()}")
    env_role_model = os.environ.get(f"FLEET_MODEL_{str(role_name).upper()}") if role_name else None
    env_default_model = os.environ.get("FLEET_MODEL_DEFAULT")

    model_key = (
        env_task_model
        or env_role_model
        or task_cfg.get("model")
        or role_cfg.get("model")
        or env_default_model
        or (models.get("default") if isinstance(models, dict) else None)
    )
    if not isinstance(model_key, str) or not model_key:
        raise FleetConfigError(f"Unable to resolve model for task: {task_name}")

    model_key = resolve_model_key(config, model_key)
    entry = _get_registry_entry(config, model_key)

    # Parameter merge: model defaults -> role overrides -> task parameters -> env overrides
    merged: dict[str, Any] = {}
    merged.update(entry.get("parameters", {}) if isinstance(entry.get("parameters"), dict) else {})
    merged.update(
        role_cfg.get("parameter_overrides", {})
        if isinstance(role_cfg.get("parameter_overrides"), dict)
        else {}
    )
    merged.update(
        task_cfg.get("parameters", {}) if isinstance(task_cfg.get("parameters"), dict) else {}
    )

    if "DSPY_TEMPERATURE" in os.environ:
        try:
            merged["temperature"] = float(os.environ["DSPY_TEMPERATURE"])
        except ValueError as exc:
            raise FleetConfigError("DSPY_TEMPERATURE must be a float") from exc

    model_type = str(entry.get("model_type", "chat"))
    timeout = entry.get("timeout")
    if timeout is not None and not isinstance(timeout, int):
        raise FleetConfigError(f"Invalid timeout for {model_key}: expected int seconds")

    return TaskLMResolution(
        model_key=model_key,
        model_type=model_type,
        parameters=merged,
        timeout=timeout,
    )


def build_lm_for_task(config: dict[str, Any], task_name: str) -> dspy.LM:
    """Build a `dspy.LM` for a given task name using the fleet config."""
    resolved = _resolve_task_lm(config, task_name)
    entry = _get_registry_entry(config, resolved.model_key)
    provider = _model_provider(resolved.model_key)

    model_name = entry.get("model")
    if not isinstance(model_name, str) or not model_name:
        raise FleetConfigError(f"Invalid registry model name for {resolved.model_key}")

    # Extract common LLM parameters; keep provider-specific keys as kwargs.
    params = {k: v for k, v in resolved.parameters.items() if v is not None}
    temperature = params.pop("temperature", None)
    max_tokens = params.pop("max_tokens", None)

    lm_kwargs: dict[str, Any] = dict(params)
    if resolved.timeout is not None:
        lm_kwargs["timeout"] = resolved.timeout

    # Provider-specific configuration
    if provider == "deepinfra":
        dspy_model, lm_kwargs = _configure_deepinfra(entry, model_name, lm_kwargs)
    elif provider == "gemini":
        dspy_model, lm_kwargs = _configure_gemini(entry, model_name, lm_kwargs)
    elif provider == "zai":
        dspy_model, lm_kwargs = _configure_zai(entry, model_name, lm_kwargs)
    else:
        # Vertex and other providers: treat as already LiteLLM-formatted
        dspy_model = model_name if "/" in model_name else f"{provider}/{model_name}"

    return dspy.LM(
        dspy_model,
        model_type=resolved.model_type,  # type: ignore[arg-type]
        temperature=temperature,
        max_tokens=max_tokens,
        **lm_kwargs,
    )


def _configure_deepinfra(
    entry: dict[str, Any], model_name: str, lm_kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Configure DeepInfra provider settings."""
    api_key_env = entry.get("env")
    api_base_env = entry.get("base_url_env")
    api_base_default = entry.get("base_url_default")

    api_key = _get_env_value(str(api_key_env) if api_key_env else None)
    if not api_key:
        raise FleetConfigError(
            f"Missing API key env var for {entry.get('model_key')}: {api_key_env}"
        )

    api_base = _get_env_value(str(api_base_env) if api_base_env else None) or api_base_default
    if not isinstance(api_base, str) or not api_base:
        raise FleetConfigError(f"Missing API base for {entry.get('model_key')}")

    lm_kwargs.update({"api_key": api_key, "api_base": api_base})
    return f"openai/{model_name}", lm_kwargs


def _configure_gemini(
    entry: dict[str, Any], model_name: str, lm_kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Configure Gemini provider settings."""
    api_key_env = entry.get("env")
    api_key_fallback = entry.get("env_fallback")
    api_key = _get_env_value(
        str(api_key_env) if api_key_env else None,
        str(api_key_fallback) if api_key_fallback else None,
    )
    if not api_key:
        raise FleetConfigError(
            f"Missing API key for {entry.get('model_key')}: set {api_key_env} or {api_key_fallback}"
        )

    # Handle thinking_level for Gemini 3+ models
    thinking_level = lm_kwargs.pop("thinking_level", None)
    if thinking_level:
        if "extra_body" not in lm_kwargs:
            lm_kwargs["extra_body"] = {}
        lm_kwargs["extra_body"]["thinking_config"] = {"thinking_level": thinking_level}

    lm_kwargs["api_key"] = api_key
    return f"gemini/{model_name}", lm_kwargs


def _configure_zai(
    entry: dict[str, Any], model_name: str, lm_kwargs: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    """Configure ZAI provider settings."""
    api_key_env = entry.get("env")
    api_base_env = entry.get("base_url_env")

    api_key = _get_env_value(str(api_key_env) if api_key_env else None)
    if not api_key:
        raise FleetConfigError(
            f"Missing API key env var for {entry.get('model_key')}: {api_key_env}"
        )

    api_base = _get_env_value(str(api_base_env) if api_base_env else None)
    if api_base:
        lm_kwargs["api_base"] = api_base
    lm_kwargs["api_key"] = api_key

    return f"anthropic/{model_name}", lm_kwargs
