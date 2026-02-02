# Skill Fleet – Agent Working Guide

A guide for working with the Skill Fleet codebase.

---

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --group dev` |
| Run linter | `uv run ruff check .` |
| Auto-fix issues | `uv run ruff check --fix .` |
| Format code | `uv run ruff format .` |
| Run pre-commit | `uv run pre-commit run --all-files` |
| Run all tests | `uv run pytest` |
| Run unit tests | `uv run pytest tests/unit/` |
| Run specific test | `uv run pytest tests/unit/test_file.py::test_function` |
| Skip slow tests | `uv run pytest -m "not slow"` |
| Type check | `uv run ty check` |
| Validate skills | `uv run skill-fleet validate` |
| Start dev server | `uv run skill-fleet serve --reload` |
| Run CLI chat | `uv run skill-fleet chat` |

---

## Prerequisites

- **Python 3.12+**
- **uv** package manager
- **Git**
- **Docker** (for PostgreSQL/MLflow, optional)

---

## Project Structure

```
src/skill_fleet/
├── api/                  # FastAPI application layer
│   ├── v1/               # API endpoints (skills, jobs, hitl, optimization, streaming)
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # API service layer (job_manager, skill_service)
│   ├── middleware/       # FastAPI middleware (logging)
│   ├── utils/            # API utilities (draft_save)
│   ├── dependencies.py   # FastAPI dependencies
│   ├── factory.py        # App factory
│   ├── lifespan.py       # Startup/shutdown lifecycle
│   └── main.py           # Application entry point
├── cli/                  # Typer CLI application
│   ├── commands/         # CLI commands (chat, create, validate, migrate, etc.)
│   ├── hitl/             # HITL runner and handlers
│   ├── ui/               # CLI UI utilities
│   └── utils/            # CLI utilities (constants, security)
├── common/               # Shared utilities
│   ├── utils.py          # General utilities
│   ├── security.py       # Path security functions
│   ├── exceptions.py     # Shared exceptions
│   ├── paths.py          # Path utilities
│   ├── async_utils.py    # Async utilities
│   ├── dspy_compat.py    # DSPy compatibility layer
│   ├── llm_fallback.py   # LLM fallback mechanisms
│   ├── serialization.py  # Serialization helpers
│   └── streaming.py      # Streaming utilities
├── config/               # Configuration files
│   ├── config.yaml       # Main configuration
│   ├── profiles/         # LLM profiles
│   ├── templates/        # SKILL.md template, metadata template
│   ├── optimized/        # Optimized prompts/checkpoints
│   └── training/         # Training data (gold_skills_v2.json, trainset_v4.json)
├── core/                 # Core business logic
│   ├── modules/          # DSPy modules
│   │   ├── base.py       # Base module class
│   │   ├── conversational.py
│   │   ├── generation/   # content.py, refined_content.py, templates.py
│   │   ├── hitl/         # questions.py
│   │   ├── understanding/# dependencies.py, intent.py, parallel_analysis.py, plan.py, requirements.py, taxonomy.py
│   │   └── validation/   # best_of_n_validator.py, compliance.py, metrics.py, structure.py, test_cases.py
│   ├── signatures/       # DSPy signatures
│   │   ├── base.py
│   │   ├── generation/
│   │   ├── hitl/
│   │   ├── understanding/
│   │   └── validation/
│   ├── workflows/        # Workflow orchestration
│   │   ├── skill_creation/   # understanding.py, generation.py, validation.py
│   │   └── streaming.py
│   ├── services/         # Core services
│   │   └── conversation/     # engine.py, handlers/, models.py
│   ├── optimization/     # Optimization system
│   │   ├── optimizer.py
│   │   ├── evaluation.py
│   │   ├── cache.py
│   │   └── rewards/      # phase1_rewards.py, phase2_rewards.py, step_rewards.py
│   ├── hitl/             # HITL handlers
│   ├── tools/            # Tool definitions (research.py)
│   ├── models.py         # Domain models
│   ├── config.py         # Core configuration
│   └── dspy_utils.py     # DSPy utilities
├── dspy/                 # DSPy integration layer
│   ├── config.py         # DSPy configuration
│   ├── adapters.py       # LM adapters
│   └── streaming.py      # DSPy streaming support
├── infrastructure/       # Technical infrastructure
│   ├── db/               # Database layer (SQLAlchemy)
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── repositories.py
│   │   └── session.py
│   ├── monitoring/       # MLflow setup
│   └── tracing/          # Distributed tracing
├── taxonomy/             # Taxonomy management
│   ├── manager.py
│   ├── discovery.py
│   ├── skill_loader.py
│   ├── skill_registration.py
│   ├── metadata.py
│   ├── naming.py
│   └── path_resolver.py
├── validators/           # agentskills.io validation
│   └── skill_validator.py
└── services/             # Service layer (orchestration)
```

---

## Code Style

### Python Standards

- Python 3.12+ with modern syntax
- Line length: 100 characters
- Double quotes preferred
- 4-space indentation
- Type checker: `ty` (configured in `pyproject.toml`)

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

Use modern Python 3.12+ syntax:

```python
# Built-in generics
list[str]
dict[str, Any]
set[int]

# Union operator
str | None      # not Optional[str]
int | str       # not Union[int, str]

# Annotated for FastAPI
from typing import Annotated
value: Annotated[str, Depends(get_value)]
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions/variables | snake_case | `get_skill_name()` |
| Classes | PascalCase | `SkillValidator` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| Private | _prefix | `_internal_method()` |
| Exceptions | Error/Exception suffix | `ValidationError` |

---

## DSPy Patterns

### Configuration

```python
from skill_fleet.dspy import configure_dspy, get_task_lm, dspy_context

# Configure at startup
configure_dspy()

# Get task-specific LM
lm = get_task_lm("skill_understand")

# Scoped config for async (recommended)
with dspy_context(lm=custom_lm):
    result = await module.aforward(...)
```

### Signatures

```python
import dspy

class AnalyzeSkill(dspy.Signature):
    """Analyze a skill description and extract requirements."""

    task_description: str = dspy.InputField(desc="User's description")
    context: str | None = dspy.InputField(desc="Additional context", default=None)

    requirements: list[str] = dspy.OutputField(desc="Extracted requirements")
    domain: str = dspy.OutputField(desc="Detected domain")
    reasoning: dspy.Reasoning = dspy.OutputField()
```

### Modules

```python
from typing import Any

class MyModule(dspy.Module):
    def forward(self, **kwargs: Any) -> dspy.Prediction:
        ...

    async def aforward(self, **kwargs: Any) -> dspy.Prediction:
        ...
```

### Best Practices

- Prefer `module(...)` or `await module.acall(...)` over `module.forward(...)`
- Use `dspy_context(lm=...)` for scoped configuration
- LM failures raise by default; fallbacks need `SKILL_FLEET_ALLOW_LLM_FALLBACK=1`

---

## FastAPI Patterns

### Dependency Injection

```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/skills/")
async def list_skills(
    service: SkillService = Depends(get_skill_service)
) -> list[SkillResponse]:
    return await service.list_skills()
```

### Background Tasks

Return immediately with job ID for long operations:

```python
from fastapi import BackgroundTasks

@router.post("/skills/")
async def create_skill(
    request: CreateSkillRequest,
    background_tasks: BackgroundTasks,
) -> CreateSkillResponse:
    job_id = create_job(...)
    background_tasks.add_task(run_workflow, job_id, request)
    return CreateSkillResponse(job_id=job_id, status="pending")
```

Jobs are tracked via `/api/v1/jobs/{job_id}`. Jobs use dual-layer persistence (memory + PostgreSQL).

### Error Handling

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="Not found")
```

---

## Testing

### Organization

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Fast unit tests with mocked dependencies |
| `tests/integration/` | Tests requiring external services |
| `tests/api/` | API-specific tests |
| `tests/cli/` | CLI tests |

### Commands

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# Skip slow/integration tests
uv run pytest -m "not slow and not integration"

# With coverage
uv run pytest --cov=src/skill_fleet
```

### Markers

- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Tests requiring API keys/external services
- `@pytest.mark.asyncio` - Async tests (mode=auto configured)

---

## Environment Variables

### Required

- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - LLM credentials

### API Configuration

- `SKILL_FLEET_ENV` - `production` or `development`
- `SKILL_FLEET_CORS_ORIGINS` - Allowed origins
- `SKILL_FLEET_SKILLS_ROOT` - Skills directory (default: `./skills`)

### LiteLLM Proxy (alternative to direct keys)

- `LITELLM_API_KEY`, `LITELLM_BASE_URL`, `LITELLM_MODEL`

### DSPy / Runtime

- `DSPY_CACHEDIR` - Cache directory (default: `.dspy_cache`)
- `DSPY_TEMPERATURE` - Global temperature override
- `SKILL_FLEET_ALLOW_LLM_FALLBACK` - Enable fallbacks (tests only)

### Model Overrides

- `FLEET_MODEL_DEFAULT` - Override default model
- `FLEET_MODEL_SKILL_UNDERSTAND`, `FLEET_MODEL_SKILL_PLAN`, etc.

See `.env.example` for complete list.

---

## Security

### Path Security

```python
from skill_fleet.common.security import resolve_path_within_root

safe_path = resolve_path_within_root(base_path, user_input)
```

---

## agentskills.io Compliance

Every `SKILL.md` must have YAML frontmatter:

```markdown
---
name: skill-name-in-kebab-case
description: A concise description (1-2 sentences)
---

# Skill Title
```

Requirements:
- Frontmatter must be first in file
- `name` in kebab-case
- `description` required

---

## Pre-Commit Checklist

```bash
uv run ruff check --fix .
uv run ruff format .
uv run pre-commit run --all-files
uv run pytest
uv run skill-fleet validate  # if skills modified
```

Check `git status` for unwanted files (.venv/, .dspy_cache/, __pycache__/). Do not commit the `src/frontend/` directory (in .gitignore).

---

## Key Gotchas

1. **`skills/` directory excluded from ruff linting** - Different conventions apply
2. **CLI wraps API logic** - Implement in `core`/`api` first, expose via CLI
3. **Async-first architecture** - Use `async/await` throughout; use `async_utils.py` for helpers
4. **API endpoints return immediately** - Long operations use `BackgroundTasks`
5. **Job system uses dual-layer persistence** - Memory cache + PostgreSQL
6. **Streaming support** - Multiple streaming modules (API, workflows, DSPy)
7. **HITL system** - Extensive human-in-the-loop support in API and CLI
8. **Use migration tools** - `uv run skill-fleet migrate` instead of manual skill edits
9. **Deterministic LLM fallback** - For tests/offline: `SKILL_FLEET_ALLOW_LLM_FALLBACK=1`

---

## Forbidden Patterns

- No `import *`
- No mutable default arguments
- No `print` statements (use `logging.getLogger(__name__)`)
- No `assert` for runtime checks
- Avoid manual `isinstance` type checks
