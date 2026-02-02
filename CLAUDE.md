# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Skill Fleet is a local-first platform for creating, validating, and curating AI agent skills as standards-compliant artifacts. It transforms natural language descriptions into production-ready agent skills using a three-phase workflow: Understanding → Generation → Validation. Built on DSPy for reliable, optimizable LLM programs.

- **Language**: Python 3.12+
- **Package Manager**: uv
- **Web Framework**: FastAPI
- **CLI Framework**: Typer
- **LLM Framework**: DSPy

## Common Commands

### Development

```bash
# Install dependencies
uv sync --group dev

# Start API server (development with auto-reload)
uv run skill-fleet serve --reload
# OR directly with uvicorn
uvicorn skill_fleet.api.main:app --reload

# Interactive skill creation
uv run skill-fleet chat

# Non-interactive skill creation
uv run skill-fleet create "Create a React hooks skill" --auto-approve
```

### Testing

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run specific test
uv run pytest tests/unit/test_file.py::test_function -v

# Skip slow tests
uv run pytest -m "not slow"

# With coverage
uv run pytest --cov=skill_fleet
```

### Code Quality

```bash
# Lint and auto-fix
uv run ruff check --fix .

# Format code
uv run ruff format .

# Type check
uv run ty check

# Security scan
uv run bandit -c pyproject.toml -r src/

# Run pre-commit hooks
uv run pre-commit run --all-files
```

### CLI Operations

```bash
# Validate a skill directory
uv run skill-fleet validate ./skills/_drafts/<job_id>

# Promote draft to taxonomy
uv run skill-fleet promote <job_id>

# List all skills
uv run skill-fleet list
```

## Architecture

### Three-Phase Workflow

The core skill creation flow follows three phases:

1. **Understanding** (`src/skill_fleet/core/modules/understanding/`)
   - `ExtractRequirementsModule`: Extracts structured requirements from natural language
   - `AnalyzeIntentModule`: Analyzes user intent and problem statement
   - `CreatePlanModule`: Builds execution plan for skill generation
   - `ParallelAnalysisModule`: Runs analyses in parallel for efficiency

2. **Generation** (`src/skill_fleet/core/modules/generation/`)
   - `ContentGenerationModule`: Creates SKILL.md with YAML frontmatter
   - `RefinedContentModule`: Applies category-specific templates and refinements
   - Generates code examples and references

3. **Validation** (`src/skill_fleet/core/modules/validation/`)
   - `StructureValidator`: Validates directory structure and required files
   - `ComplianceChecker`: Checks agentskills.io compliance
   - `BestOfNValidator`: Quality assessment using best-of-N sampling
   - `TestCaseGenerator`: Generates validation test cases

### Draft-First Workflow

Skills are always generated as drafts first:

1. **Draft Phase**: Skills written to `skills/_drafts/<job_id>/`
2. **Review Phase**: Human-in-the-loop (HITL) feedback via API or CLI
3. **Promotion Phase**: Validated skills moved to stable taxonomy paths via `POST /api/v1/drafts/{job_id}/promote` or `uv run skill-fleet promote <job_id>`

### Key Abstractions

**DSPy Module Pattern** (`src/skill_fleet/core/modules/base.py`):
- All modules extend `BaseModule` which wraps `dspy.Module`
- Async-first with `aforward()` method, automatic sync wrapper via `forward()`
- Use `dspy_context(lm=...)` for scoped configuration in async code

**Configuration** (`src/skill_fleet/dspy/config.py`):
- `DSPyConfig` singleton for centralized DSPy configuration
- `configure_dspy()` loads from `src/skill_fleet/config/config.yaml`
- Environment variable overrides for models: `FLEET_MODEL_*`

**API Structure** (`src/skill_fleet/api/`):
- Factory pattern in `factory.py` for app creation with CORS/middleware
- Routes mounted at `/api/v1/*` via `router.py`
- Background tasks for long operations (skill creation returns job ID immediately)
- Dual-layer persistence: memory cache + PostgreSQL

**Path Security** (`src/skill_fleet/common/security.py`):
- Always use `resolve_path_within_root(base_path, user_input)` for filesystem access
- Prevents path traversal attacks
- Symlink validation included

## Code Patterns

### DSPy Signatures

```python
import dspy

class AnalyzeSkill(dspy.Signature):
    """Analyze a skill description and extract requirements."""
    task_description: str = dspy.InputField()
    context: str | None = dspy.InputField(default=None)

    requirements: list[str] = dspy.OutputField()
    domain: str = dspy.OutputField()
    reasoning: dspy.Reasoning = dspy.OutputField()
```

### FastAPI Endpoints

```python
from fastapi import APIRouter, Depends, BackgroundTasks

router = APIRouter()

@router.post("/skills/")
async def create_skill(
    request: CreateSkillRequest,
    background_tasks: BackgroundTasks,
    service: SkillService = Depends(get_skill_service),
) -> CreateSkillResponse:
    job_id = create_job(...)
    background_tasks.add_task(run_workflow, job_id, request)
    return CreateSkillResponse(job_id=job_id, status="pending")
```

### Type Hints (Python 3.12+)

```python
# Use modern syntax
list[str]          # not List[str]
dict[str, Any]     # not Dict[str, Any]
str | None         # not Optional[str]
int | str          # not Union[int, str]
```

## Environment Variables

**Required:**
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` - LLM credentials
- `DATABASE_URL` - PostgreSQL connection string (production)

**API Configuration:**
- `SKILL_FLEET_ENV` - `development` (default) or `production`
- `SKILL_FLEET_CORS_ORIGINS` - Comma-separated allowed origins
- `SKILL_FLEET_SKILLS_ROOT` - Skills directory (default: `./skills`)

**Testing:**
- `SKILL_FLEET_ALLOW_LLM_FALLBACK` - Enable deterministic fallbacks for tests

## agentskills.io Compliance

Every `SKILL.md` must have:

1. YAML frontmatter at the top:
   ```yaml
   ---
   name: skill-name-in-kebab-case
   description: A concise description (1-2 sentences)
   ---
   ```

2. Required section: `## When to Use`
3. Valid subdirectories: `references/`, `guides/`, `templates/`, `scripts/`, `examples/`

Validator: `src/skill_fleet/validators/skill_validator.py`

## Important Notes

- **Skills directory excluded from ruff**: `skills/**` and `.skills/**` are excluded from linting (see `pyproject.toml`)
- **No print statements**: Use `logging.getLogger(__name__)` for all logging
- **Async-first**: All DSPy modules implement `aforward()`; use `async_utils.py` for helpers
- **CLI wraps API**: Implement core logic in `api`/`core`, expose via CLI commands
- **Job tracking**: Long operations return job IDs; poll `/api/v1/jobs/{job_id}` for status
- **Streaming support**: SSE endpoints available at `/api/v1/skills/stream`
