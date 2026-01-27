# LLM Configuration

**Last Updated**: 2026-01-12
**Location**: `src/skill_fleet/llm/`

## Overview

Skills Fleet supports multiple LLM providers through a centralized configuration system. Task-specific model selection allows different workflows to use optimized models for their specific needs.

`★ Insight ─────────────────────────────────────`
The **task-specific model mapping** is a key differentiator. Different phases of skill creation require different capabilities: understanding requires high reasoning, validation requires precision, and generation requires creativity. Each task uses an optimized model.
`─────────────────────────────────────────────────`

## Configuration File

**Location**: `config/config.yaml`

`````yaml
# Default model
models:
  default: "gemini:gemini-3-flash-preview"

  # Model registry
  registry:
    # Gemini (Google)
    gemini:gemini-3-flash-preview:
      model: "gemini-3-flash-preview"
      model_type: "chat"
      env: "GEMINI_API_KEY"
      env_fallback: "GOOGLE_API_KEY"
      parameters:
        temperature: 1.0
        max_tokens: 4096
        thinking_level: "high"

    gemini:gemini-2.5-pro:
      model: "gemini-2.5-pro"
      model_type: "chat"
      env: "GEMINI_API_KEY"
      parameters:
        temperature: 1.0
        max_tokens: 8192

    # DeepInfra
    deepinfra:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo:
      model: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
      model_type: "chat"
      env: "DEEPINFRA_API_KEY"
      base_url_env: "DEEPINFRA_BASE_URL"
      base_url_default: "https://api.deepinfra.com/v1/openai"
      parameters:
        temperature: 1.0
        max_tokens: 4096

    # ZAI (Claude)
    zai:claude-sonnet-4-20250514:
      model: "claude-sonnet-4-20250514"
      model_type: "chat"
      env: "ZAI_API_KEY"
      base_url_env: "ZAI_BASE_URL"
      parameters:
        temperature: 1.0
        max_tokens: 8192

    # Vertex AI
    vertex:claude-3-5-sonnet@20240620:
      model: "claude-3-5-sonnet@20240620"
      model_type: "chat"
      parameters:
        temperature: 1.0
        max_tokens: 4096
        vertex_project: "your-project-id"
        vertex_location: "us-central1"

# Task-specific models
tasks:
  skill_understand:
    role: understanding
    model: "gemini:gemini-3-flash-preview"
    parameters:
      temperature: 1.0

  skill_plan:
    role: planning
    model: "gemini:gemini-3-flash-preview"
    parameters:
      temperature: 1.0

  skill_initialize:
    role: fast_operation
    model: "gemini:gemini-3-flash-preview"
    ````markdown
    # Moved: LLM Configuration (archived)

    This index was consolidated into the canonical LLM reference: `docs/reference/llm-config.md`.

    An archived copy of the original index and deep-dive pages is available under `docs/archive/legacy_llm/`.

    See: `docs/reference/llm-config.md` for the current, canonical guidance.

    ````
deepinfra:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo:
  model: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
  env: "DEEPINFRA_API_KEY"
  base_url_env: "DEEPINFRA_BASE_URL"
  base_url_default: "https://api.deepinfra.com/v1/openai"
  parameters:
    temperature: 0.7
    max_tokens: 4096
`````

**Setup:**

```bash
export DEEPINFRA_API_KEY="your-api-key"
```

**Features:**

- OpenAI-compatible API
- Open-source models
- Cost-effective

### ZAI (Claude)

**Required**: `ZAI_API_KEY`

```yaml
zai:claude-sonnet-4-20250514:
  model: "claude-sonnet-4-20250514"
  env: "ZAI_API_KEY"
  base_url_env: "ZAI_BASE_URL"
  parameters:
    temperature: 0.7
    max_tokens: 8192
```

**Setup:**

```bash
export ZAI_API_KEY="your-api-key"
```

**Features:**

- Anthropic Claude models
- High-quality outputs
- Long context windows

### Vertex AI

**Required**: Google Cloud credentials (ADC)

```yaml
vertex:claude-3-5-sonnet@20240620:
  model: "claude-3-5-sonnet@20240620"
  parameters:
    temperature: 0.7
    max_tokens: 4096
    vertex_project: "your-project-id"
    vertex_location: "us-central1"
```

**Setup:**

```bash
gcloud auth application-default login
```

**Features:**

- Enterprise Google Cloud integration
- Vertex AI model garden
- Private deployments

## Programmatic Usage

### Configure DSPy

```python
from skill_fleet.llm.dspy_config import configure_dspy

# Configure with default task
lm = configure_dspy()

# Now all DSPy modules use this LM
```

### Get Task-Specific LM

```python
from skill_fleet.llm.dspy_config import get_task_lm
import dspy

# Get LM for specific task
edit_lm = get_task_lm("skill_edit")

# Use temporarily
with dspy.context(lm=edit_lm):
    result = await module.aforward(...)
```

### Custom Config Path

```python
from pathlib import Path

lm = configure_dspy(
    config_path=Path("custom/config.yaml"),
    default_task="skill_edit"
)
```

## Next Steps

- **[Providers Documentation](providers.md)** - Provider-specific setup
- **[DSPy Config Documentation](dspy-config.md)** - Centralized configuration
- **[Task Models Documentation](task-models.md)** - Task-specific mapping

## Related Documentation

- **[DSPy Overview](../dspy/)** - DSPy architecture and usage
- **[API Documentation](../api/)** - REST API reference
