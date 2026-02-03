# Getting Started with Skill Fleet

**Last Updated**: 2026-01-31

Welcome to Skill Fleet! This guide will walk you through installing, configuring, and creating your first skill.

## What is Skill Fleet?

Skill Fleet is a system for creating, managing, and validating AI agent skills. It uses a 3-phase workflow powered by DSPy:

1. **Understanding** - Analyzes your requirements and creates a plan
2. **Generation** - Generates complete skill content
3. **Validation** - Validates quality and compliance

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) for Python package management
- An LLM API key (OpenAI, Anthropic, or Gemini)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd skill-fleet
```

### 2. Install Dependencies

```bash
# Sync dependencies with uv
uv sync
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
# Required: API key for your LLM provider
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
GOOGLE_API_KEY=...

# Optional: Database URL (defaults to SQLite)
SKILL_FLEET_DB_URL=sqlite:///skill_fleet.db

# Optional: Default user ID
SKILL_FLEET_USER_ID=default
```

### 4. Initialize Database

```bash
uv run skill-fleet db init
```

This creates the necessary tables for job tracking and HITL interactions.

## Your First Skill

### Start the API Server

In one terminal, start the API server:

```bash
uv run skill-fleet serve
```

The server will start on `http://localhost:8000`. You'll see interactive prompts for configuration (or use `--auto-accept` to skip).

### Create a Skill Interactively

In another terminal, use the chat command for an interactive experience:

```bash
uv run skill-fleet chat "Create a Python async/await programming skill"
```

You'll see:

- Real-time progress updates
- Live reasoning/thinking display
- Interactive prompts if clarification is needed

### What Happens Behind the Scenes

1. **Understanding Phase** (10-30 seconds)
   - Analyzes your task description
   - Determines the best taxonomy path
   - Identifies prerequisites
   - Creates a detailed plan

2. **Generation Phase** (20-60 seconds)
   - Generates complete SKILL.md content
   - Includes code examples
   - Structures according to best practices

3. **Validation Phase** (10-20 seconds)
   - Checks compliance with agentskills.io standards
   - Validates quality metrics
   - Generates test cases

### View the Result

After completion, you'll see:

```
✨ Skill Creation Completed!
📁 Skill saved to: .skills/python-async-await
```

The skill includes:

- `SKILL.md` - The main skill file with instructions
- Generated test cases
- Validation report

### Promote to Taxonomy

If the skill looks good, promote it to the main taxonomy:

```bash
uv run skill-fleet promote <job_id>
```

Get the job ID from the output of the create command.

## Quick Commands

### Create a Skill (Non-Interactive)

For automation or CI/CD:

```bash
uv run skill-fleet create "Create a React hooks skill" --auto-approve
```

### Validate a Skill

```bash
uv run skill-fleet validate .skills/python-async-await
```

### List All Skills

```bash
uv run skill-fleet list
```

### Export to XML

```bash
uv run skill-fleet generate-xml -o my_skills.xml
```

## Understanding the Workflow

### HITL (Human-in-the-Loop)

The system may pause for your input at key points:

1. **Clarifying Questions** - If the task is ambiguous
2. **Structure Fixes** - If name/description needs adjustment
3. **Preview** - To review content before finalizing (optional)

Respond via the interactive prompts in the chat interface.

### Job-Based Architecture

All skill creation happens asynchronously:

1. You submit a task
2. The system creates a job and returns a `job_id`
3. The job runs in the background
4. You poll for status (automatic in chat mode)

Check job status:

```bash
curl http://localhost:8000/api/v1/jobs/<job_id>
```

## Next Steps

### Learn More

- [CLI Usage Guide](../how-to-guides/cli-usage.md) - Detailed CLI workflows
- [API Reference](../reference/api/endpoints.md) - REST API documentation
- [Workflow Engine](../explanation/architecture/workflow-engine.md) - How it works

### Create More Skills

Try creating skills for:

- Framework documentation (React, Django, FastAPI)
- Best practices (testing, security, performance)
- Workflow guides (CI/CD, deployment, debugging)

### Customize Templates

Edit `src/skill_fleet/core/modules/generation/templates.py` to customize:

- Section structure
- Required elements
- Example patterns

## Troubleshooting

### "Could not connect to API server"

Make sure the server is running:

```bash
uv run skill-fleet serve
```

### "Validation failed"

Check the validation output for specific issues:

```bash
uv run skill-fleet validate <path> --json
```

Common issues:

- Missing trigger phrases in description
- Invalid kebab-case name
- Missing required sections

### "Database error"

Reinitialize the database:

```bash
uv run skill-fleet db init --force
```

⚠️ Warning: `--force` deletes all data.

## Configuration Options

### LLM Provider

Edit `src/skill_fleet/config/config.yaml`:

```yaml
llm:
  default_model: openai/gpt-4o-mini
  fallback_model: anthropic/claude-3-haiku-20240307
```

### Skills Root

Set where skills are stored:

```bash
export SKILL_FLEET_SKILLS_ROOT=/path/to/skills
```

### API URL

If running the server on a different host/port:

```bash
export SKILL_FLEET_API_URL=http://localhost:8080
```

## Best Practices

1. **Start with clear task descriptions**
   - Include the domain (technical, creative, etc.)
   - Mention specific technologies
   - Describe the target audience

2. **Use interactive mode for new skills**
   - The chat interface provides better feedback
   - HITL helps catch issues early

3. **Validate before promoting**

   ```bash
   uv run skill-fleet validate <path> && uv run skill-fleet promote <job_id>
   ```

4. **Organize with taxonomy paths**
   - Use descriptive paths like `technical/python/async`
   - Keep related skills together

5. **Review test cases**
   - Generated test cases help verify triggering
   - Edge cases highlight potential issues

## Getting Help

- **Documentation**: See `docs/` directory
- **CLI Help**: `uv run skill-fleet --help`
- **API Docs**: `http://localhost:8000/docs` (when server is running)

---

Welcome to Skill Fleet! Start creating skills that help AI agents work better.
