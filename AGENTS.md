# skill-fleet – Agent Working Guide

## Build, Lint, Test Commands

**Prerequisites:** uv package manager (pre-installed), Python 3.12+

```bash
# Install dependencies (run after pyproject.toml changes)
uv sync --group dev

# Linting (run before commits)
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .

# Testing
uv run pytest
uv run pytest -v
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest --cov=src/skill_fleet
uv run pytest tests/unit/test_skill_validator.py
uv run pytest tests/unit/test_skill_validator.py::test_validate_directory_skill
uv run pytest -m "not slow"
```

**Always use `uv run` prefix** for Python commands.

## Code Style Guidelines

### Python & Formatting

- Python 3.12+ required, use ruff (replaces flake8, black, isort)
- Line length: 100 chars, double quotes, 4-space indentation

### Import Ordering

```python
from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi import APIRouter
from pydantic import BaseModel

from skill_fleet.common.utils import safe_json_loads
```

### Type Hints

Use modern hints: `list[str]`, `dict[str, int]`, `str | None`, `Annotated` for FastAPI

### Naming

- Functions/variables: snake_case
- Classes: PascalCase
- Constants: UPPER_SNAKE_CASE
- Private: _prefix
- Exceptions: suffix with Error/Exception
- Dataclasses: `@dataclass(frozen=True, slots=True)`

### Docstrings

Google-style required for public modules, classes, functions:
```python
def validate_skill(skill_path: Path) -> ValidationResult:
    """Validate a skill directory.

    Args:
        skill_path: Path to the skill directory.

    Returns:
        ValidationResult with validation status and errors.
    """
```

### Error Handling

- Use specific exceptions, not bare `except:`
- Raise custom exceptions from `skill_fleet.api.exceptions` for API errors
- Use logging (not `print`): `logger = logging.getLogger(__name__)`
- Use `HTTPException(status_code=404, detail="Not found")` for FastAPI

### Testing

- pytest with `asyncio_mode = "auto"`
- Mock external dependencies (LLMs, file I/O) in unit tests
- Use `@pytest.mark.integration` for tests requiring API keys
- Place tests in `tests/unit/` (fast) or `tests/integration/` (slow)

### Path Security

For all file operations:
```python
from skill_fleet.common.security import (
    resolve_path_within_root,
    sanitize_relative_file_path
)
```

### DSPy Integration

```python
from skill_fleet.infrastructure.llm.dspy_config import configure_dspy, get_task_lm

lm = configure_dspy(default_task="skill_understand")
edit_lm = get_task_lm("skill_edit")
```

### FastAPI Patterns

- Use dependency injection: `Depends(get_skill_service)`
- Return Pydantic models from endpoints
- Use `BackgroundTasks` for async work
- Handle errors with `skill_fleet.api.exceptions`

### agentskills.io Compliance

Every `SKILL.md` must have YAML frontmatter at top:
```markdown
---
name: skill-name-in-kebab-case
description: A concise description (1-2 sentences)
---

# Skill Title
```

Frontmatter MUST be first, name must be kebab-case, description required.

### Common Utilities

Import from `skill_fleet.common.utils`: `safe_json_loads()`, `safe_float()`

### Forbidden Patterns

- No `import *`
- No mutable default arguments (use `None` and initialize)
- No `print` statements (use logging)
- No `assert` for runtime checks
- Avoid manual `isinstance` type checks (prefer `typing`)

## Pre-Commit Checklist

1. `uv run ruff check --fix .`
2. `uv run ruff format .`
3. `uv run pytest`
4. `uv run skill-fleet validate` (if skills modified)
5. Check `git status` for .venv/, .dspy_cache/, __pycache__/

## Project Structure

### Source Code (`src/skill_fleet/`)

- **`api/`** - FastAPI application (restructured from `app/`)
  - `v1/` - API version 1 routers (flattened structure)
  - `schemas/` - Pydantic request/response models
  - `services/` - Business logic layer
  - `middleware/` - FastAPI middleware
  - `dependencies.py` - Dependency injection
  - `factory.py` - App factory
  - `main.py` - Application entry point
  
- **`cli/`** - CLI commands (Typer)

- **`common/`** - Shared utilities (top-level)
  - `utils.py` - General utilities
  - `security.py` - Path security functions
  - `exceptions.py` - Shared exceptions
  - `paths.py` - Path utilities
  
- **`core/`** - Domain logic + DSPy integration
  - `dspy/` - DSPy modules, signatures, workflows
  - `models.py` - Domain models
  - `services/` - Domain services

- **`infrastructure/`** - Technical infrastructure
  - `db/` - Database layer (models, repositories)
  - `llm/` - LLM configuration (DSPy, LiteLLM)
  - `monitoring/` - MLflow setup
  - `tracing/` - Distributed tracing

- **`taxonomy/`** - Taxonomy management

- **`validators/`** - agentskills.io compliance

### Other Directories

- `skills/` - Skills taxonomy (excluded from linting)
- `tests/` - Unit and integration tests
  - `api/` - API-specific tests (v1, schemas, services)
  - `common/` - Common utilities tests
  - `unit/` - Unit tests
  - `integration/` - Integration tests

## Environment Variables

Required: `GOOGLE_API_KEY`

Optional: `DSPY_CACHEDIR`, `DSPY_TEMPERATURE`, `LOG_LEVEL`

## Important Files

- `pyproject.toml` - Dependencies, pytest config, ruff rules
- `config/config.yaml` - LLM model settings
- `.github/copilot-instructions.md` - Detailed project info

## Key Gotchas

1. `skills/` directory excluded from ruff linting
2. CLI wraps API logic - implement in `core`/`api` first
3. DSPy requires explicit configuration when used as library
4. Use migration tools (`uv run skill-fleet migrate`) instead of manual skill edits
5. Job state is in-memory - restart clears pending jobs
6. Some integration tests fail without `GOOGLE_API_KEY` (expected: 2 failures)
