# LLM Providers Reference

**Last Updated**: 2026-01-12

## Overview

Skills Fleet supports multiple LLM providers through a unified configuration system. All providers are accessible via the same API using LiteLLM-compatible model strings.

Default model: gemini/gemini-3-flash-preview (see config/config.yaml)

`★ Insight ─────────────────────────────────────`
The provider abstraction allows you to switch between models without changing code. A task that uses `skill_understand` can be reconfigured to use Gemini, Claude, or Llama simply by changing the config file.
`─────────────────────────────────────────────────`

## Supported Providers

| Provider      | Models             | Best For             |
| ------------- | ------------------ | -------------------- |
| **Gemini**    | 2.0 Flash, 2.5 Pro | Fast, cost-effective |
| **DeepInfra** | Llama 3.1, Mixtral | Open-source options  |
| **ZAI**       | Claude Sonnet 4    | High-quality outputs |

```markdown
# Moved: LLM Providers (archived)

The detailed providers reference has been consolidated into the canonical reference: `docs/reference/llm-config.md`.

An archived copy of the original detailed providers file is available at `docs/archive/legacy_llm/providers.md`.

For quick guidance and recommended provider settings, see `docs/reference/llm-config.md`.
```

        max_tokens: 8192

````

### Setup

```bash
# Get API key from ZAI
export ZAI_API_KEY="zai-..."

# Optional: Custom base URL
export ZAI_BASE_URL="https://api.zai.ai"
````

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

| Model                 | Provider  | Context     | Features   |
| --------------------- | --------- | ----------- | ---------- |
| **Claude 3.5 Sonnet** | Anthropic | 200K tokens | Via Vertex |
| **Gemini Pro**        | Google    | 2M tokens   | Via Vertex |

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

| Provider      | Cost   | Speed  | Quality   | Open Source | Enterprise |
| ------------- | ------ | ------ | --------- | ----------- | ---------- |
| **Gemini**    | Low    | Fast   | High      | No          | Yes        |
| **DeepInfra** | Low    | Fast   | Medium    | Yes         | No         |
| **ZAI**       | High   | Medium | Very High | No          | No         |
| **Vertex AI** | Medium | Medium | High      | No          | Yes        |

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
    model: "gemini:gemini-2.5-pro" # Change to "zai:claude-sonnet-4" to use Claude
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
