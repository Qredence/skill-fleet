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

```yaml
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
    parameters:
      temperature: 1.0

  skill_edit:
    role: creative_generation
    model: "gemini:gemini-3-pro-preview"
    parameters:
      temperature: 1.0

  skill_package:
    role: validation
    model: "gemini:gemini-3-flash-preview"
    parameters:
      temperature: 1

  skill_validate:
    role: strict_validation
    model: "gemini:gemini-3-flash-preview"
    parameters:
      temperature: 1

# Roles (reusable configuration)
roles:
  understanding:
    description: "Deep understanding and analysis"
    parameters:
      temperature: 1
      max_tokens: 4096

  planning:
    description: "Structured planning and organization"
    parameters:
      temperature: 0.5
      max_tokens: 4096

  fast_operation:
    description: "Quick operations with deterministic output"
    parameters:
      temperature: 0.1
      max_tokens: 2048

  creative_generation:
    description: "Creative content generation"
    parameters:
      temperature: 0.6
      max_tokens: 8192

  validation:
    description: "Precise validation and checking"
    parameters:
      temperature: 0.1
      max_tokens: 2048

  strict_validation:
    description: "Strict validation with minimal variance"
    parameters:
      temperature: 0.0
      max_tokens: 2048

# Legacy aliases
legacy_aliases:
  "gpt-4": "gemini:gemini-3-flash-preview"
  "glm-4.7": "zai:glm-4.7"
```

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | `AIza...` |
| `GOOGLE_API_KEY` | Fallback Google API key | `AIza...` |
| `DEEPINFRA_API_KEY` | DeepInfra API key | `deepinfra-...` |
| `DEEPINFRA_BASE_URL` | DeepInfra base URL | `https://api.deepinfra.com/v1/openai` |
| `ZAI_API_KEY` | ZAI API key | `zai-...` |
| `ZAI_BASE_URL` | ZAI base URL | `https://api.zai.ai` |
| `DSPY_CACHEDIR` | DSPy cache directory | `/var/cache/dspy` |
| `DSPY_TEMPERATURE` | Global temperature override | `0.7` |
| `FLEET_MODEL_<TASK>` | Override model for specific task | `gemini:gemini-2.5-pro` |

## Task-Specific Model Mapping

| Task | Purpose | Recommended Model | Temperature | Reasoning |
|------|---------|-------------------|-------------|-----------|
| `skill_understand` | Task analysis | High reasoning | 0.7 | Complex analysis needs creativity |
| `skill_plan` | Structure planning | Medium reasoning | 0.5 | Structured planning needs precision |
| `skill_initialize` | Directory setup | Fast model | 0.1 | Simple operation, deterministic |
| `skill_edit` | Content generation | Creative model | 0.6 | Content creation needs creativity |
| `skill_package` | Validation | Precise model | 0.1 | Validation needs consistency |
| `skill_validate` | Compliance check | Precise model | 0.0 | Strict checking, no variance |

`★ Insight ─────────────────────────────────────`
Temperature is tuned per task based on the desired output variance. Higher temperatures (0.6-0.7) for creative tasks like understanding and editing, lower temperatures (0.0-0.1) for validation and packaging where consistency is critical.
`─────────────────────────────────────────────────`

## Configuration Hierarchy

Models are selected in this order:

1. **Environment variable**: `FLEET_MODEL_<TASK_NAME>`
2. **Task config**: `tasks.<task_name>.model`
3. **Role config**: `tasks.<task_name>.role → roles.<role>.model`
4. **Task parameter override**: `tasks.<task_name>.parameters.temperature`
5. **Role parameter override**: `roles.<role>.parameter_overrides`
6. **Environment override**: `DSPY_TEMPERATURE`
7. **Model defaults**: `models.registry.<model_key>.parameters`

### Example: Getting `skill_edit` Model

```yaml
# 1. Check env var
$ env | grep FLEET_MODEL_SKILL_EDIT
# (none)

# 2. Check task config
tasks.skill_edit.model = "gemini:gemini-3-pro-preview"  ✓ FOUND

# Would then merge parameters from:
# - tasks.skill_edit.parameters
# - roles.creative_generation.parameter_overrides
# - models.registry.*.parameters
# - env var DSPY_TEMPERATURE (if set)
```

## Provider Configuration

### Gemini (Google)

**Required**: `GEMINI_API_KEY` or `GOOGLE_API_KEY`

```yaml
gemini:gemini-3-pro-preview:
  model: "gemini-3-pro-preview"
  model_type: "chat
  env: "GEMINI_API_KEY"
  env_fallback: "GOOGLE_API_KEY"
  parameters:
    temperature: 1.0
    max_tokens: 4096
    thinking_level: "high"  # For Gemini 3+ models
```

**Setup:**
```bash
export GEMINI_API_KEY="your-api-key"
```

**Features:**
- Native DSPy support via LiteLLM
- Thinking levels for Gemini 3+
- Fast and cost-effective

### DeepInfra

**Required**: `DEEPINFRA_API_KEY`

```yaml
deepinfra:meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo:
  model: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
  env: "DEEPINFRA_API_KEY"
  base_url_env: "DEEPINFRA_BASE_URL"
  base_url_default: "https://api.deepinfra.com/v1/openai"
  parameters:
    temperature: 0.7
    max_tokens: 4096
```

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
