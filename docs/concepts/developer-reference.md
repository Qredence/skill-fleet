# Skill Fleet — Developer Guide

## 1. Purpose & Architecture

Skill Fleet combines:
- **FastAPI** for API endpoints that orchestrate DSPy workflows (`/api/v1/skills`, `/api/v1/quality`, `/api/v1/taxonomy`).
- **DSPy workflows** (`src/skill_fleet/core/workflows/`) implementing the three-phase skill creation pipeline with HITL support.
- **Typer CLI** wrapping the API (`src/skill_fleet/cli/`).
- **Taxonomy manager** (`src/skill_fleet/taxonomy/manager.py`) that enforces agentskills.io compliance and writes `metadata.json` + `SKILL.md`.
- **Templates** (`config/templates/SKILL_md_template.md`, `config/templates/metadata_template.json`) guide generated output.

## 2. Repository Layout

```
skill-fleet/
├── src/skill_fleet/
│   ├── api/              # FastAPI server, routes, schemas, services
│   ├── cli/              # Typer commands, shared HITL runner
│   ├── core/             # Domain logic + DSPy workflows
│   │   ├── modules/      # DSPy modules (understanding, generation, validation)
│   │   ├── signatures/   # DSPy signature definitions
│   │   ├── workflows/    # Workflow orchestration
│   │   ├── models.py     # Domain models
│   │   └── hitl/         # HITL handlers
│   ├── dspy/             # Centralized DSPy configuration ⭐
│   ├── taxonomy/         # Skill registration + metadata handling
│   ├── validators/       # agentskills.io validation rules
│   ├── infrastructure/   # Database, monitoring, tracing
│   └── common/           # Utilities (paths, async helpers, security)
├── config/               # Templates, config YAML, profile bootstrappers
├── docs/                 # Documentation
├── skills/               # Taxonomy content + metadata
├── tests/                # Pytest suites
├── .env.example
├── pyproject.toml
└── uv.lock
```

## 3. Core Development Workflows

### 3.1 Configure DSPy

Call `configure_dspy()` once during startup (API server does this by default).

```python
from skill_fleet.dspy import configure_dspy, get_task_lm

# Configure globally
configure_dspy()

# Get task-specific LMs when needed
lm = get_task_lm("skill_understand")
```

Keep `DSPY_CACHEDIR` and `DSPY_TEMPERATURE` in sync with environment.

### 3.2 Build + Run

Use `uv` for all Python commands:

```bash
uv sync --group dev
uv run skill-fleet serve
uv run pytest -q tests/unit
uv run ruff check src/skill_fleet
```

### 3.3 Developer CLI Commands

- `uv run skill-fleet create "..."` uses the API `POST /api/v1/skills/`.
- `uv run skill-fleet validate` and `migrate` operate directly on `skills/` and call `TaxonomyManager`.

**Note**: Some CLI commands are temporarily unavailable due to migration:
- `evaluate`, `evaluate-batch` - Use API directly
- `optimize` - Feature removed
- `onboard` - Feature removed

## 4. DSPy Workflow Architecture

### Layer 1: Signatures

Type definitions using `dspy.Signature`:

```python
# src/skill_fleet/core/signatures/understanding/requirements.py
import dspy

class GatherRequirements(dspy.Signature):
    """Gather requirements from task description."""
    task_description = dspy.InputField()
    user_context = dspy.InputField()
    
    domain = dspy.OutputField()
    category = dspy.OutputField()
    topics = dspy.OutputField()
```

### Layer 2: Modules

Reusable business logic with async support:

```python
# src/skill_fleet/core/modules/understanding/requirements.py
from skill_fleet.core.modules.base import BaseModule

class GatherRequirementsModule(BaseModule):
    def forward(self, task_description: str, user_context: str) -> dict:
        result = self.gather(
            task_description=task_description,
            user_context=user_context,
        )
        return self._parse_result(result)
    
    async def aforward(self, task_description: str, user_context: str) -> dict:
        # Async version
        return await asyncio.to_thread(self.forward, task_description, user_context)
```

### Layer 3: Workflows

High-level orchestration with HITL:

```python
# src/skill_fleet/core/workflows/skill_creation/understanding.py
class UnderstandingWorkflow:
    async def execute(self, task_description, user_context, ...) -> dict:
        # Run modules in parallel
        results = await asyncio.gather(
            self._run_requirements(task_description, user_context),
            self._run_intent(task_description, ...),
        )
        
        # Check for HITL checkpoint
        if needs_clarification(results):
            return {"status": "pending_user_input", ...}
        
        return self._synthesize(results)
```

### Using Workflows

```python
from skill_fleet.core.workflows.skill_creation import (
    UnderstandingWorkflow,
    GenerationWorkflow,
    ValidationWorkflow,
)

# Phase 1: Understanding
understanding = UnderstandingWorkflow()
phase1_result = await understanding.execute(
    task_description="Build a REST API",
    user_context={},
    taxonomy_structure={},
    existing_skills=[],
)

# Phase 2: Generation
generation = GenerationWorkflow()
phase2_result = await generation.execute(
    plan=phase1_result["plan"],
    understanding=phase1_result,
)

# Phase 3: Validation
validation = ValidationWorkflow()
phase3_result = await validation.execute(
    skill_content=phase2_result["skill_content"],
    plan=phase1_result["plan"],
)
```

## 5. Templates & Metadata

- `config/templates/SKILL_md_template.md` is trimmed and injected into generation instructions to steer the LLM's output.
- `config/templates/metadata_template.json` defines the `metadata.json` fields (version, type, load priority, dependencies, capabilities, evolution).
- `TaxonomyManager.register_skill()` enforces kebab-case names, descriptions, and metadata lists.

## 6. Testing & Quality Assurance

1. **Linting**: `uv run ruff check src/skill_fleet`
2. **Unit tests**: `uv run pytest -q tests/unit`
3. **Integration tests**: `uv run pytest tests/integration`
4. **Documentation**: Keep AGENTS.md and docs/ in sync with tooling changes.
5. **Interactive behavior**: Manual smoke tests via `skill-fleet create`, `skill-fleet serve`.

### Test Organization

```
tests/
├── unit/           # Fast unit tests
├── integration/    # Slow integration tests  
├── api/           # API-specific tests
├── cli/           # CLI tests
└── common/        # Common utility tests
```

## 7. Key Changes from Previous Architecture

### Deleted Components
- ❌ `core/dspy/` - Legacy DSPy structure (50+ files)
- ❌ `infrastructure/llm/` - Deprecated LLM config
- ❌ `onboarding/` - Deprecated onboarding module
- ❌ Old orchestrators (TaskAnalysisOrchestrator, etc.)

### New Components
- ✅ `core/modules/` - Clean module structure
- ✅ `core/signatures/` - Signature definitions
- ✅ `core/workflows/` - Workflow orchestration
- ✅ `dspy/` - Centralized DSPy configuration

### Updated Patterns

**Before:**
```python
from skill_fleet.core.dspy import configure_dspy
from skill_fleet.core.dspy.modules.workflows import TaskAnalysisOrchestrator
```

**After:**
```python
from skill_fleet.dspy import configure_dspy
from skill_fleet.core.workflows.skill_creation import UnderstandingWorkflow
```

## 8. Contributions & Planning

- Keep `AGENTS.md` updated when workflows or tooling change; this is the canonical "agent working guide".
- Record multi-step work in `plans/` as ExecPlans or feature plans (see `plans/README.md`).
- For major features, abide by the multi-agent workflow guidance.

## 9. References

### Documentation

- **[Architecture Status](../architecture/restructuring-status.md)** - Current architecture overview
- **[Import Path Guide](../development/IMPORT_PATH_GUIDE.md)** - Canonical import paths
- **[CLI Reference](../cli/)** - Command documentation and interactive chat
- **[API Reference](../api/)** - REST API endpoints and schemas
- **[HITL System](../hitl/)** - Human-in-the-Loop interactions

### Legacy References

- `docs/cli-reference.md`, `docs/skill-creator-guide.md`, `docs/api-reference.md`
- `skills/` directory for live examples
- `docs/plans/` for ongoing experiments
