# Skill Fleet Documentation

**Version**: 0.3.6
**Last Updated**: 2026-02-03

Welcome to Skill Fleet - a system for creating, managing, and validating AI agent skills using a 3-phase DSPy-powered workflow.

## Quick Start

```bash
# Install dependencies
uv sync --group dev

# Configure environment
cp .env.example .env
# Set GOOGLE_API_KEY or LITELLM_API_KEY (+ optional LITELLM_BASE_URL)

# Initialize database
uv run skill-fleet db init

# Start API server
uv run skill-fleet serve

# Create your first skill (in another terminal)
uv run skill-fleet chat "Create a Python async/await skill"
```

---

## Documentation Structure

This documentation follows the [Diátaxis framework](https://diataxis.fr/) - organized by purpose, not by feature:

| Section           | Purpose                                  | Example            |
| ----------------- | ---------------------------------------- | ------------------ |
| **Tutorials**     | Learning-oriented - step by step lessons | "Getting Started"  |
| **How-To Guides** | Task-oriented - solve specific problems  | "Validate a Skill" |
| **Reference**     | Information-oriented - lookup details    | "API Endpoints"    |
| **Explanation**   | Understanding-oriented - deep knowledge  | "Architecture"     |

---

## Tutorials

Learning-oriented lessons for newcomers.

- **[Getting Started](tutorials/getting-started.md)** - Installation, setup, and your first skill

---

## How-To Guides

Task-oriented guides for specific goals.

- **[Create a Skill](how-to-guides/create-a-skill.md)** - Complete skill creation workflow
- **[Validate a Skill](how-to-guides/validate-a-skill.md)** - Validation workflows and troubleshooting
- **[CLI Usage](how-to-guides/cli-usage.md)** - Practical CLI workflows and best practices

---

## Reference

Detailed technical information for lookup.

### API Reference

- **[Endpoints](reference/api/endpoints.md)** - Complete REST API endpoint documentation
- **[Schemas](reference/api/schemas.md)** - Request/response models and types

### CLI Reference

- **[Commands](reference/cli/commands.md)** - All CLI commands, arguments, and options

### Core Reference

- **[Workflows](reference/core/workflows.md)** - Understanding, Generation, Validation workflows
- **[Modules](reference/core/modules.md)** - DSPy module implementations
- **[Signatures](reference/core/signatures.md)** - DSPy signature definitions

---

## Explanation

Deep understanding of concepts and architecture.

### Architecture

- **[System Overview](explanation/architecture/system-overview.md)** - High-level architecture and data flow
- **[Workflow Engine](explanation/architecture/workflow-engine.md)** - 3-phase workflow details and HITL

### Development

- **[Contributing](explanation/development/contributing.md)** - Development setup, workflows, and guidelines

---

## Common Workflows

### Create and Promote a Skill

```bash
# 1. Create skill interactively
uv run skill-fleet chat "Create a React hooks skill"

# 2. Check validation
uv run skill-fleet validate skills/_drafts/<job_id>/<skill-name> --json

# 3. Promote to taxonomy
uv run skill-fleet promote <job-id>
```

### Non-Interactive Mode

```bash
# Create with auto-approval
uv run skill-fleet create "Python decorators skill" --auto-approve

# Validate all drafts
for draft in skills/_drafts/*/*/; do
    uv run skill-fleet validate "$draft"
done
```

### API Integration

```bash
# Create job
curl -X POST http://localhost:8000/api/v1/skills/ \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Create Python skill"}'

# Poll for status
curl http://localhost:8000/api/v1/jobs/<job-id>

# Respond to HITL
curl -X POST http://localhost:8000/api/v1/hitl/responses \
  -H "Content-Type: application/json" \
  -d '{"job_id":"<job-id>","response":"Python 3.12"}'
```

---

## Project Structure

```
skill_fleet/
├── src/skill_fleet/
│   ├── api/                 # FastAPI layer
│   ├── core/                # DSPy workflows and modules
│   ├── infrastructure/      # Database, monitoring
│   └── cli/                 # Command-line interface
├── tests/                   # Test suite
├── docs/                    # Documentation (this folder)
├── config/                  # Configuration files
└── pyproject.toml           # Project configuration
```

---

## Key Concepts

### 3-Phase Workflow

1. **Understanding** - Analyze requirements, find taxonomy, create plan
2. **Generation** - Generate SKILL.md content with templates
3. **Validation** - Check compliance, quality, trigger coverage

### Human-in-the-Loop (HITL)

Workflows can pause for human input at key points:

- **Clarifying Questions** - When requirements are ambiguous
- **Structure Fix** - When name/description needs adjustment
- **Preview** - Review content before finalizing
- **Review** - Final approval before promotion

### Skill Categories

| Category              | Use Case                  | Required Sections                |
| --------------------- | ------------------------- | -------------------------------- |
| `document_creation`   | Creating documents/assets | Output Format, Examples          |
| `workflow_automation` | Multi-step processes      | Workflow Steps, Input/Output     |
| `mcp_enhancement`     | MCP-guided workflows      | MCP Tools, Tool Sequences        |
| `analysis`            | Data/code analysis        | Analysis Approach, Output Format |

---

## Configuration

### Environment Variables

| Variable                  | Description       | Default                    |
| ------------------------- | ----------------- | -------------------------- |
| `LITELLM_API_KEY`         | LiteLLM proxy key | Preferred when set         |
| `LITELLM_BASE_URL`        | LiteLLM base URL  | Optional (`http://localhost:4000`) |
| `GOOGLE_API_KEY`          | Gemini API key    | Fallback when LiteLLM not set |
| `DATABASE_URL`            | Database URL      | `sqlite:///skill_fleet.db` |
| `SKILL_FLEET_USER_ID`     | Default user ID   | `default`                  |
| `SKILL_FLEET_SKILLS_ROOT` | Skills directory  | `skills`                   |

### Config File (`src/skill_fleet/config/config.yaml`)

```yaml
models:
  default: gemini/gemini-3-flash-preview
  registry:
    gemini/gemini-3-flash-preview:
      env: LITELLM_API_KEY
      env_fallback: GOOGLE_API_KEY
```

---

## Getting Help

- **Documentation**: You're reading it! Start with [Getting Started](tutorials/getting-started.md)
- **CLI Help**: `uv run skill-fleet --help`
- **API Docs**: `http://localhost:8000/docs` (when server is running)
- **Troubleshooting**: Check [Validate a Skill](how-to-guides/validate-a-skill.md) for common issues

---

## Contributing

See [Contributing Guide](explanation/development/contributing.md) for:

- Development setup
- Code style and testing
- Adding new modules
- Documentation guidelines
