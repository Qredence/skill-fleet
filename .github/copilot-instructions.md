# Copilot Instructions: Skill Fleet

## Project Overview

- **Name**: skill-fleet
- **Language**: Python 3.12+
- **Core Frameworks**: FastAPI (API), Typer (CLI), DSPy (LLM orchestration)
- **PackageManager**: `uv` (Universal Package Manager)
- **Purpose**: Draft-first skill generation platform. Creates "skills" (directories with `SKILL.md`) via a 3-phase workflow: Understanding -> Generation -> Validation.

## Development Standards

- **Dependency Management**: ALWAYS use `uv`.
  - Install: `uv sync --group dev`
  - Add package: `uv add <package>`
- **Linting & Formatting**:
  - Run: `uv run ruff check --fix .` && `uv run ruff format .`
  - Configuration: `pyproject.toml` (strict rules, 2026 best practices).
  - Note: `skills/` directory is excluded from linting.
- **Testing**:
  - Run: `uv run pytest`
  - Markers: `@pytest.mark.integration` for LLM tests (require keys), `@pytest.mark.slow`.

## Architectural Patterns

### 1. DSPy & LLM Orchestration

- **Thread Safety**: NEVER modify global DSPy settings in async code.
  - **CORRECT**: Use `with dspy_context():` context manager for per-request configuration.
  - **INCORRECT**: `dspy.settings.configure(...)` at module level or inside async functions.
- **Configuration**: Centralized in `src/skill_fleet/dspy/config.py`.

### 2. File System Security

- **Untrusted Input**: Treat ALL file paths from users or LLMs as untrusted.
- **Safe Access**: MUST use `skill_fleet.common.security.resolve_path_within_root(path)` before reading/writing.
- **Root Directory**: `skills/` is the sandbox.

### 3. API & CLI Boundaries

- **API**: `src/skill_fleet/api`
  - Maintainer of state and coordination.
  - Entry: `uvicorn skill_fleet.api.main:app` via `uv run skill-fleet serve`.
  - Pattern: Architecture separates Routers (`api/v1`) from Use Cases/Workflows (`core/workflows`).
- **CLI**: `src/skill_fleet/cli`
  - Entry: `skill-fleet` command.
  - Pattern: CLI is a thin client; calls the API via `SkillFleetClient` for logic.

## Core Workflows (The "Brain")

### 1. Draft-First Lifecycle

1.  **Create**: Job initialized via `POST /api/v1/skills`.
2.  **Draft**: Workflow writes to `skills/_drafts/<job_id>/` (isolated).
3.  **Promote**: User explicitly calls `promote`. Only then is the skill moved to the main taxonomy.

### 2. Job Status Machine

- **Models**: `src/skill_fleet/infrastructure/db/models.py`
- **States**: `PENDING` → `RUNNING` → `PENDING_HITL` (Human-in-the-Loop) → `COMPLETED`.
- **HITL**: Conversations can suspend execution for user input (`clarify`, `confirm`, `review`).

## Key Files & Locations

- **Routes**: `src/skill_fleet/api/v1/`
- **Validators**: `src/skill_fleet/validators/`
- **Memory/Context**: `skills/memory_blocks/`
  - Files here (`interaction_history.json`, `project_context.json`) are **ALWAYS LOADED** context.
  - Must have `"load_priority": "always"`.
- **Env Config**: `.env` (managed by `python-dotenv`).

## Skill Validation Rules

- **Structure**: Every skill must have a `SKILL.md`.
- **Content**: Must include YAML frontmatter and `## When to Use` section.
- **Allowed Subdirs**: `references/`, `guides/`, `templates/`, `scripts/`, `examples/` (+ `assets/`, `images/`, `static/`).
