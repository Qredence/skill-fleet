# DSPy Configuration

**Last Updated**: 2026-01-12
**Location**: `src/skill_fleet/llm/dspy_config.py`

## Overview

The `dspy_config` module provides centralized DSPy configuration for Skills Fleet. It handles loading config files, building LLM instances, and setting up DSPy's global settings.

`★ Insight ─────────────────────────────────────`
This module is the **single source of truth** for DSPy configuration. All parts of the application should use `configure_dspy()` or `get_task_lm()` rather than instantiating LLMs directly. This ensures consistent configuration and makes model selection easy.
`─────────────────────────────────────────────────`

## API Reference

### configure_dspy()

Configure DSPy with fleet config and return default LM.

`````python
def configure_dspy(
    config_path: Path | None = None,
    default_task: str = "skill_understand",
) -> dspy.LM:
    """Configure DSPy with fleet config and return default LM.

    Args:
        config_path: Path to config/config.yaml (default: project root)
        default_task: Default task to use for dspy.settings.lm

    Returns:
        The configured LM instance (also set as dspy.settings.lm)

    Example:
        >>> from skill_fleet.llm.dspy_config import configure_dspy
        >>> lm = configure_dspy()
        >>> # Now all DSPy modules use this LM by default
    """
````markdown
# Moved: DSPy configuration (archived)

This content has been consolidated into the canonical LLM reference: `docs/reference/llm-config.md`.

An archived copy of the original detailed page is available at `docs/archive/legacy_llm/dspy-config.md`.

If you are looking for programmatic usage (configure_dspy, get_task_lm) or the original deep-dive, see the archived file above or the consolidated reference.

`````

result = await module.aforward(...)
