# Skill Fleet — Getting Started Guide

## 1. Overview

Skill Fleet is a hierarchical, DSPy-powered capability framework that lets agents load or generate skills on-demand. Instead of bloated monolithic prompts, it keeps skills modular, searchable, and compliant with the [agentskills.io](https://agentskills.io) specification.

This guide shows how to get started with the CLI and API. For detailed documentation on specific topics, see:

- **[DSPy Documentation](../dspy/)** - 3-phase workflow, signatures, modules, programs
- **[API Documentation](../api/)** - REST API endpoints, schemas, jobs
- **[CLI Documentation](../cli/)** - Command reference, interactive chat
- **[LLM Configuration](../llm/)** - Provider setup, task-specific models
- **[HITL System](../hitl/)** - Human-in-the-Loop interactions

## 2. Prerequisites

1. **Python 3.12+** and the [`uv`](https://github.com/astral-sh/uv) package manager.
2. **Bun** (optional but required for the TypeScript/React TUI).
3. Valid API keys exported through `.env` (`GOOGLE_API_KEY`, optional provider keys, DSPy overrides).
4. The `skills/` directory stores the taxonomy—keep it versioned and backed up.

## 3. Installation & Environment

```bash
# Clone
# from repo root
git clone https://github.com/Qredence/skill-fleet.git
cd skill-fleet

# Python deps
uv sync --group dev
# Optional TUI deps
bun install

# Create environment file
cp .env.example .env
# Edit .env to set required API keys:
# GOOGLE_API_KEY, DSPY_CACHEDIR, DSPY_TEMPERATURE, etc.
```

## 4. Core User Workflows

### 4.1 Start the API Server

```bash
uv run skill-fleet serve             # production mode
uv run skill-fleet serve --reload    # dev mode with autoreload
```

The FastAPI server is the single source of truth: all CLI interactions (`create`, `chat`, `list`) call it. It configures DSPy on startup and exposes the job + HITL workflow at `/api/v2/skills/create` and `/api/v2/hitl/{job_id}`.

### 4.2 Create a Skill (CLI)

```bash
uv run skill-fleet create "Describe the capability"
uv run skill-fleet create "..." --auto-approve
```

- Starts a background job that runs `src/skill_fleet/core/programs/skill_creator.py`.
- Respond to HITL prompts (`clarify`, `confirm`, `preview`, `validate`) in the terminal.
- Job auto-saves to `skills/` and writes `metadata.json` + `SKILL.md` (frontmatter + template guidance).

### 4.3 Interactive Chat Experience

```bash
uv run skill-fleet chat
uv run skill-fleet chat "Create a Docker best practices skill"
uv run skill-fleet chat --auto-approve
```

- Runs the same job + HITL endpoints but wraps them in a guided UI.
- Commands: `/help`, `/exit`. After each job, you’re prompted to start another.
- Use `--auto-approve` to skip prompts and let the job run to completion.

### 4.4 Validation & Migration

```bash
uv run skill-fleet validate skills/<path>
uv run skill-fleet migrate --dry-run
uv run skill-fleet migrate
```

- `validate` ensures agentskills.io frontmatter and structure are correct.
- `migrate` converts legacy skills to the current schema in `skills/`, use `--dry-run` first.

### 4.5 Generate XML or Analytics

```bash
uv run skill-fleet generate-xml -o available_skills.xml
uv run skill-fleet analytics --user-id default
```

- XML follows `<available_skills>` from agentskills.io for prompt injection.
- Analytics command summarizes usage and recommendations.

## 5. Templates & Compliance

- `config/templates/SKILL_md_template.md` describes the required YAML frontmatter and body structure (kebab-case `name`, concise `description`).
- `config/templates/metadata_template.json` shows the optional metadata fields (version, type, load priority, dependencies, capabilities).
- New skills should follow the template hints inserted into the DSPy generation instructions.

## 6. Troubleshooting & Tips

| Scenario | Tip |
| --- | --- |
| API unreachable | Ensure `uv run skill-fleet serve` is running and `SKILL_FLEET_API_URL` matches. |
| HITL prompt times out | Restart the job; state is in-memory. |
| Skill description too vague | Use `chat` to walk through clarifying questions (type `/help` to review the command list). |
| Need to see available skills | `uv run skill-fleet list` or inspect `skills/` manually. |

## 7. Quick Commands Cheat Sheet

```bash
# Start API
uv run skill-fleet serve

# Create skill
uv run skill-fleet create "task"

# Guided chat
uv run skill-fleet chat

# Validate/migrate
uv run skill-fleet validate skills/<path>
uv run skill-fleet migrate --dry-run

# Generate XML
uv run skill-fleet generate-xml -o available_skills.xml
```

## 8. Related Resources

- [AGENTS.md](../AGENTS.md) (working guide and tooling expectations)
- `docs/skill-creator-guide.md`, `docs/agentskills-compliance.md`
- `skills/` taxonomy for existing skill examples
