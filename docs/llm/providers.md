# LLM Providers Reference

**Last Updated**: 2026-01-12

## Overview

Skills Fleet supports multiple LLM providers through a unified configuration system. All providers are accessible via the same API using LiteLLM-compatible model strings.

Default model: gemini/gemini-3-flash-preview (see config/config.yaml)

`★ Insight ─────────────────────────────────────`
The provider abstraction allows you to switch between models without changing code. A task that uses `skill_understand` can be reconfigured to use Gemini, Claude, or Llama simply by changing the config file.
`─────────────────────────────────────────────────`

## Supported Providers

| Provider | Models | Best For |
|----------|--------|----------|
| **Gemini** | 2.0 Flash, 2.5 Pro | Fast, cost-effective |
| **DeepInfra** | Llama 3.1, Mixtral | Open-source options |
| **ZAI** | Claude Sonnet 4 | High-quality outputs |
| **Vertex AI** | Gemini, Claude | Enterprise deployments |

---

## Gemini (Google)

### Overview

Google's Gemini models provide fast, cost-effective inference with native DSPy support.

### Models

| Model | Context | Features |
|-------|---------|----------|
| **gemini-3-flash-preview** | 1M tokens | Fast, experimental |
| **gemini-2.5-pro** | 2M tokens | High quality |

### Configuration

```yaml
models:
  registry:
    gemini/gemini-3-flash-preview:
      model: "gemini/gemini-3-flash-preview"
      model_type: "chat"
      env: "LITELLM_API_KEY"           # Uses LiteLLM to access Gemini 3 Flash
      timeout: 60
      parameters:
        temperature: 1.0  # Intentionally higher than the common default (0.7) to favor creative/diverse outputs
        max_tokens: 8192
        thinking_level: "high"  # Gemini 3+ only
```

Note: The example above uses temperature=1.0 intentionally to encourage more creative and varied responses from Gemini 3. For more deterministic or focused outputs, lower the temperature (common default is around 0.7; values near 0.0 produce very deterministic responses).

### Setup

```bash
# Uses LiteLLM API key to access Gemini 3 Flash
export LITELLM_API_KEY="your-litelm-api-key"

# Optional: Google API key fallback if you use direct Google Cloud integrations
export GOOGLE_API_KEY="your-google-api-key"
```

### Features

- **Thinking Levels**: For Gemini 3+ models, control reasoning depth
  - `low` - Minimal thinking
  - `medium` - Balanced thinking
  - `high` - Deep thinking

- **Native DSPy**: Direct integration without LiteLLM wrapper

- **Large Context**: Up to 1M tokens for some models

### Usage Example

```python
from skill_fleet.llm.dspy_config import configure_dspy, get_task_lm

# Use Gemini as default
lm = configure_dspy()

# Or use specific Gemini model
import dspy
gemini_lm = dspy.LM("gemini/gemini-3-flash-preview", api_key="<LITELLM_API_KEY>")
```

---

## DeepInfra

### Overview

DeepInfra provides access to open-source models with an OpenAI-compatible API.

### Models

| Model | Context | Features |
|-------|---------|----------|
| **Llama 3.1 70B** | 128K tokens | Open-source, fast |
| **Mixtral 8x7B** | 32K tokens | Mixture of experts |
| **Qwen 2.5 72B** | 128K tokens | High quality |

### Configuration

```yaml
models:
  registry:
    deepinfra:nvidia/Nemotron-3-Nano-30B-A3B:
      model: "nvidia/Nemotron-3-Nano-30B-A3B"
      model_type: "chat"
      env: "DEEPINFRA_API_KEY"
      base_url_env: "DEEPINFRA_BASE_URL"
      base_url_default: "https://api.deepinfra.com/v1/openai"
      parameters:
        temperature: 0.7
        max_tokens: 4096
```

### Setup

```bash
# Get API key from: https://deepinfra.com/login
export DEEPINFRA_API_KEY="deepinfra-..."

# Optional: Custom base URL
export DEEPINFRA_BASE_URL="https://api.deepinfra.com/v1/openai"
```

### Features

- **Open-Source**: Access to Llama, Mixtral, Qwen, and more
- **Cost-Effective**: Often cheaper than proprietary models
- **OpenAI-Compatible**: Drop-in replacement

### Usage Example

```python
import dspy

llama_lm = dspy.LM(
    "openai/nvidia/Nemotron-3-Nano-30B-A3B",
    api_base="https://api.deepinfra.com/v1/openai",
    api_key="...",
)
```

---

## ZAI (Claude)

### Overview

ZAI provides access to Anthropic's Claude models with high-quality outputs.

### Models

| Model | Context | Features |
|-------|---------|----------|
| **Claude Sonnet 4** | 200K tokens | High quality |
| **Claude Opus** | 200K tokens | Highest quality |

### Configuration

```yaml
models:
  registry:
    zai:glm-4.7:
      model: "glm-4.7"
      model_type: "chat"
      env: "ZAI_API_KEY"
      base_url_env: "ZAI_BASE_URL"
      parameters:
        temperature: 0.7
        max_tokens: 8192
```

### Setup

```bash
# Get API key from ZAI
export ZAI_API_KEY="zai-..."

# Optional: Custom base URL
export ZAI_BASE_URL="https://api.zai.ai"
```

### Features

- **High Quality**: Claude models are known for nuanced outputs
- **Long Context**: Up to 200K tokens
- **Anthropic-style**: Follows Anthropic's AI principles

### Usage Example

```python
import dspy

claude_lm = dspy.LM(
    "anthropic/glm-4.7",
    api_key="...",
    api_base="https://api.zai.ai",
)
```

---

## Vertex AI

### Overview

Google Cloud's Vertex AI provides enterprise access to various models including Gemini and Claude.

### Models

| Model | Provider | Context | Features |
|-------|----------|---------|----------|
| **Claude 3.5 Sonnet** | Anthropic | 200K tokens | Via Vertex |
| **Gemini Pro** | Google | 2M tokens | Via Vertex |

### Configuration

```yaml
models:
  registry:
    vertex:deepseek/deepseek-v3.2:
      model: "deepseek-v3.2"
      model_type: "chat"
      parameters:
        temperature: 0.7
        max_tokens: 4096
        vertex_project: "your-project-id"
        vertex_location: "us-central1"
```

### Setup

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set project
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### Features

- **Enterprise**: Private deployments, VPC-SC
- **Monitoring**: Cloud Logging integration
- **Security**: IAM-based access control

### Usage Example

```python
import dspy
from google.cloud import aiplatform

# Uses Application Default Credentials
vertex_lm = dspy.LM(
    "vertex_ai_deepseek_v3_2",
    project="your-project-id",
    location="us-central1",
)
```

---

## Provider Comparison

| Provider | Cost | Speed | Quality | Open Source | Enterprise |
|----------|------|-------|--------|-------------|------------|
| **Gemini** | Low | Fast | High | No | Yes |
| **DeepInfra** | Low | Fast | Medium | Yes | No |
| **ZAI** | High | Medium | Very High | No | No |
| **Vertex AI** | Medium | Medium | High | No | Yes |

---

## Choosing a Provider

### Use Gemini When:
- You want fast, cost-effective inference
- You need large context windows
- You're just getting started

### Use DeepInfra When:
- You prefer open-source models
- You want to minimize costs
- You need specific model architectures

### Use ZAI When:
- You need highest quality outputs
- You value nuanced language
- Cost is less important

### Use Vertex AI When:
- You're an enterprise Google Cloud customer
- You need private deployments
- You want centralized billing

---

## Switching Providers

To switch providers for a task:

```yaml
tasks:
  skill_edit:
    model: "gemini:gemini-2.5-pro"  # Change to "zai:claude-sonnet-4" to use Claude
```

Or via environment variable:

```bash
export FLEET_MODEL_SKILL_EDIT="zai:claude-sonnet-4"
```

---

## See Also

- **[LLM Configuration Overview](index.md)** - Configuration system
- **[DSPy Config Documentation](dspy-config.md)** - Programmatic usage
- **[Task Models Documentation](task-models.md)** - Task-specific mapping
