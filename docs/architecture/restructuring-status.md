# Skills Fleet Architecture Status

**Last Updated**: 2026-01-29
**Status**: ✅ DSPy Workflow Architecture Migration Complete

## Overview

The Skills Fleet codebase has been migrated to a clean DSPy workflow architecture following the pattern: **Signatures → Modules → Workflows**. This document describes the current architecture and completed work.

## What's New (Current Architecture)

### Clean DSPy Architecture

1. **Signatures Layer** (`core/signatures/`)
   - Pure type definitions using `dspy.Signature`
   - Organized by workflow phase: understanding, generation, validation, hitl
   - No business logic, just input/output field definitions

2. **Modules Layer** (`core/modules/`)
   - Reusable DSPy modules with `forward()` and `aforward()` methods
   - Extends `BaseModule` for consistent async support
   - Organized by workflow phase

3. **Workflows Layer** (`core/workflows/`)
   - High-level orchestration of multiple modules
   - Manages HITL checkpoints and state
   - Async-first design with proper error handling

4. **Centralized DSPy Config** (`dspy/`)
   - Single source of truth: `skill_fleet.dspy`
   - `configure_dspy()` and `get_task_lm()` functions
   - Replaces deprecated `infrastructure/llm/` and `core/dspy/`

### API Layer (FastAPI)

- **v1 API**: Main stable API for skill operations
- Clean service layer (`api/services/`)
- Pydantic schemas (`api/schemas/`)
- Proper dependency injection

### Removed Components

- ❌ `core/dspy/` - Legacy DSPy structure (50+ files deleted)
- ❌ `infrastructure/llm/` - Deprecated LLM configuration
- ❌ `onboarding/` - Deprecated onboarding module
- ❌ Old orchestrators (TaskAnalysisOrchestrator, etc.)

## Directory Structure

### Current Structure (Post-Migration)

```
src/skill_fleet/
├── api/                    # FastAPI application
│   ├── v1/                # API version 1 routers
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # Business logic layer
│   ├── middleware/        # FastAPI middleware
│   ├── factory.py         # App factory
│   └── main.py            # Application entry point
│
├── cli/                   # CLI commands (Typer)
│   ├── commands/          # Individual command implementations
│   ├── hitl/             # HITL CLI handlers
│   ├── ui/               # CLI UI components
│   └── app.py            # Main Typer application
│
├── common/                # Shared utilities
│   ├── utils.py          # General utilities
│   ├── security.py       # Path security functions
│   ├── exceptions.py     # Shared exceptions
│   └── paths.py          # Path utilities
│
├── core/                  # Domain logic + DSPy workflows
│   ├── modules/          # DSPy modules (understanding, generation, validation, hitl)
│   ├── signatures/       # DSPy signature definitions
│   ├── workflows/        # Workflow orchestration layer
│   ├── models.py         # Domain models
│   ├── config.py         # Configuration validation
│   └── hitl/             # Human-in-the-loop handlers
│
├── dspy/                  # Centralized DSPy configuration ⭐ NEW
│   └── __init__.py       # configure_dspy(), get_task_lm()
│
├── infrastructure/        # Technical infrastructure
│   ├── db/               # Database layer (models, repositories)
│   ├── monitoring/       # MLflow setup
│   └── tracing/          # Distributed tracing
│
├── taxonomy/             # Taxonomy management
│   └── manager.py        # Taxonomy operations
│
└── validators/           # agentskills.io compliance
    └── skill_validator.py
```

### Key Architectural Changes

| Before | After |
|--------|-------|
| `core/dspy/modules/workflows/` | `core/workflows/skill_creation/` |
| `core/dspy/signatures/` | `core/signatures/` |
| `core/dspy/modules/` | `core/modules/` |
| `infrastructure/llm/dspy_config.py` | `dspy/__init__.py` |
| Orchestrator classes | Workflow classes with HITL support |
| Sync-only modules | Async-first with `aforward()` |

## Import Guidelines

### Current Recommended Patterns

```python
# DSPy configuration (NEW location)
from skill_fleet.dspy import configure_dspy, get_task_lm

# Workflows
from skill_fleet.core.workflows.skill_creation import (
    UnderstandingWorkflow,
    GenerationWorkflow,
    ValidationWorkflow,
)

# Modules (if needed directly)
from skill_fleet.core.modules.understanding import GatherRequirementsModule

# API layer
from skill_fleet.api.services.skill_service import SkillService

# Domain models
from skill_fleet.core.models import SkillCreationResult
```

### Deprecated Patterns (Do Not Use)

```python
# ❌ These no longer work:
from skill_fleet.core.dspy import ...              # Deleted
from skill_fleet.infrastructure.llm import ...     # Deleted
from skill_fleet.core.dspy.modules.workflows import TaskAnalysisOrchestrator  # Deleted
```

## Migration Summary

### Phase 1: Architecture Migration ✅ Complete

**Deleted:**
- `src/skill_fleet/core/dspy/` (entire directory, 50+ files)
- `src/skill_fleet/infrastructure/llm/` (3 deprecated files)
- `src/skill_fleet/onboarding/` (deprecated module)
- `src/skill_fleet/core/creator.py` (legacy creator)
- Old orchestrator test files (17 files)

**Created:**
- `src/skill_fleet/dspy/` - Centralized DSPy configuration
- `src/skill_fleet/core/modules/` - Clean module structure
- `src/skill_fleet/core/signatures/` - Signature definitions
- `src/skill_fleet/core/workflows/` - Workflow orchestration

**Updated:**
- API layer to use new workflows
- CLI commands (evaluate, optimize, onboard return 503)
- All imports from old to new locations
- AGENTS.md documentation

### Phase 2: Structural Cleanup ✅ Complete

**Added:**
- Missing `__init__.py` files in 5 directories

**Removed:**
- Empty directories (6 total)
- Deprecated infrastructure/llm/
- Onboarding module
- Wildcard imports

**Fixed:**
- Import issues
- Linting errors
- Test organization

## Current Status

### What Works ✅

- **Understanding Workflow**: Requirements gathering, intent analysis, taxonomy path, dependencies
- **Generation Workflow**: Skill content generation with optional HITL
- **Validation Workflow**: Compliance checking with auto-refinement
- **API Endpoints**: Create, validate, refine skills
- **CLI**: Core commands functional
- **Tests**: 101 passing, 5 skipped
- **Linting**: All checks pass

### Temporarily Unavailable ⚠️

The following return HTTP 503 (Service Unavailable):

- `/api/v1/optimization/*` - Signature optimization
- `/api/v1/conversational/*` - Chat endpoints
- CLI: `evaluate`, `evaluate-batch`, `optimize`, `onboard` commands

These features need to be rebuilt using the new workflow pattern.

## Key Design Decisions

### Why Signatures → Modules → Workflows?

1. **Separation of Concerns**: Each layer has a single responsibility
2. **Testability**: Signatures can be tested independently
3. **Reusability**: Modules can be composed into different workflows
4. **Async-First**: All modules support async/await
5. **HITL Support**: Workflows manage human-in-the-loop checkpoints

### Why Centralized DSPy Config?

1. **Single Source of Truth**: One place for LM configuration
2. **Simplified Imports**: `from skill_fleet.dspy import ...`
3. **No Circular Dependencies**: Clean separation from core logic
4. **Easy Testing**: Can mock at single point

### Why Delete Onboarding?

The onboarding module depended on deleted legacy code (`TaxonomySkillCreator`, `SkillBootstrapper`). It can be rebuilt using the new workflow architecture if needed.

## Testing

### Test Coverage
- **Unit tests**: 101 passing
- **Integration tests**: 5 skipped (require API keys)
- **Structural tests**: All package imports work

### Test Organization
```
tests/
├── unit/              # Fast unit tests
├── integration/       # Slow integration tests
├── api/              # API-specific tests
├── cli/              # CLI tests
└── common/           # Common utility tests
```

## API Changes

### Available Endpoints

```
POST   /api/v1/skills/           # Create skill
GET    /api/v1/skills/{id}      # Get skill
PATCH  /api/v1/skills/{id}      # Update skill
DELETE /api/v1/skills/{id}      # Delete skill
POST   /api/v1/skills/validate  # Validate skill
POST   /api/v1/skills/refine    # Refine skill with feedback

POST   /api/v1/quality/validate       # Validate quality
POST   /api/v1/quality/assess         # Assess quality
POST   /api/v1/quality/auto-fix       # Auto-fix issues
```

### Temporarily Unavailable (503)

```
POST /api/v1/optimization/analyze
POST /api/v1/optimization/improve
POST /api/v1/optimization/compare

POST /api/v1/conversational/message
GET  /api/v1/conversational/session/{id}/history
```

## Migration Guide for Developers

### If You Were Using Old Imports:

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

### If You Were Using Onboarding:

The onboarding module has been removed. You can create skills directly using the API or CLI:

```bash
uv run skill-fleet create "Your task description"
```

Or via API:
```bash
curl -X POST http://localhost:8000/api/v1/skills/ \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Your task", "user_id": "user123"}'
```

## Future Considerations

### Optional Enhancements

1. **Re-enable Optimization Endpoints**
   - Rebuild using new ValidationWorkflow
   - Add optimizer selection to workflow config

2. **Re-enable Conversational Interface**
   - Rebuild using new UnderstandingWorkflow
   - Implement session management

3. **Add More Tests**
   - Integration tests for HITL flows
   - Performance tests for workflows

4. **Documentation**
   - Add workflow diagrams
   - Create module usage examples

## Conclusion

The migration to the clean DSPy workflow architecture is complete. The codebase now has:

1. **Clear separation** of concerns (signatures/modules/workflows)
2. **Async-first design** throughout
3. **Centralized configuration** for DSPy
4. **No legacy code** from old architecture
5. **All tests passing** with no regressions

The current structure is stable, maintainable, and follows DSPy best practices.

## References

- [AGENTS.md](../../AGENTS.md) - Developer working guide
- [API Documentation](../api/index.md)
- [Contributing Guide](../development/CONTRIBUTING.md)
