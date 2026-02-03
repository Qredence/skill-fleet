"""
Optimization utilities for DSPy programs.

This module provides:
- Approved model configuration and LM factory
- Constants for default models

NOTE: The full optimizer workflow (MIPROv2, GEPA, etc.) was removed
because LegacySkillCreationProgram has been deprecated. This module
retains only the model configuration utilities.

TODO(2026-03): Re-implement optimization using the new workflow architecture.
"""

from __future__ import annotations

import logging

import dspy

logger = logging.getLogger(__name__)


# =============================================================================
# Approved Models Configuration
# =============================================================================

APPROVED_MODELS = {
    "gemini-3-flash-preview": "gemini/gemini-3-flash-preview",
    "gemini-3-pro-preview": "gemini/gemini-3-pro-preview",
    "deepseek-v3.2": "deepinfra/deepseek-v3.2",
    "Nemotron-3-Nano-30B-A3B": "nvidia/Nemotron-3-Nano-30B-A3B",
}

DEFAULT_MODEL = "gemini-3-flash-preview"
REFLECTION_MODEL = "gemini-3-pro-preview"


def get_lm(
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    **kwargs,
) -> dspy.LM:
    """
    Get a DSPy LM instance for an approved model.

    Args:
        model_name: Name of approved model (without provider prefix)
        temperature: LLM temperature
        **kwargs: Additional LM configuration

    Returns:
        Configured dspy.LM instance

    Raises:
        ValueError: If model is not in approved list

    """
    if model_name not in APPROVED_MODELS:
        raise ValueError(
            f"Model '{model_name}' is not approved. Use one of: {list(APPROVED_MODELS.keys())}"
        )

    model_path = APPROVED_MODELS[model_name]
    return dspy.LM(model_path, temperature=temperature, **kwargs)


__all__ = [
    "APPROVED_MODELS",
    "DEFAULT_MODEL",
    "REFLECTION_MODEL",
    "get_lm",
]
