# Skills Fleet Codebase Restructuring Status

**Last Updated**: 2026-01-25
**Status**: ✅ FastAPI-Centric Restructure Complete

## Overview

The Skills Fleet codebase has undergone a restructuring to improve maintainability, clarity, and separation of concerns. This document describes the current architecture, completed work, and future considerations.

## What's New (Post-Restructure)

### Architecture Enhancements

1. **Domain Layer (DDD Patterns)**
   - Domain entities: `Skill`, `Job`, `TaxonomyPath`
   - Value objects with validation
   - Specification pattern for business rules
   - Domain events for future event-driven architecture
   - Repository interfaces for data access abstraction

2. **Service Layer**
   - `BaseService` with dependency injection
   - `SkillService`, `JobService`, `ConversationService`
   - MLflow hierarchical run tracking
   - Automatic artifact logging

3. **Caching Layer**
   - In-memory cache with TTL configuration
   - Pattern-based invalidation
   - Cache statistics and monitoring
   - Redis migration path documented

4. **Conversational Interface (v1 API)**
   - Session management with state machine
   - Multi-turn conversations
   - Intent-based routing
   - Server-Sent Events (SSE) streaming

5. **API Versioning Clarity**
   - v2 API: Main, stable API for skill operations
   - v1 API: Experimental chat streaming endpoints
   - See [API Migration Guide](../api/MIGRATION_V1_TO_V2.md)

## Architecture Pattern: Facade + Delegation

The codebase uses a **facade pattern** where public-facing directories provide clean import paths while delegating to internal implementation modules. This provides:

1. **Flexibility in import styles** - Support both DDD-style and module-based imports
2. **Backward compatibility** - Old imports continue to work during migration
3. **Clear boundaries** - Separation between public API and internal implementation
4. **Gradual migration** - Can update imports incrementally without breaking changes

## Directory Structure

### Public API Surface

```
skill-fleet/
├── src/skill_fleet/
│   ├── app/              # FastAPI entry point (facade)
│   │   ├── main.py       # Delegates to api/app.py
│   │   └── api/          # Placeholder for future API routes
│   │
│   ├── domain/           # Domain-driven design facade (NEW)
│   │   ├── models/       # Domain entities (Skill, Job)
│   │   ├── repositories/ # Repository interfaces
│   │   ├── services/     # Domain services
│   │   └── specifications/ # Business rules (Specification pattern)
│   │
│   ├── services/         # Service layer facade (NEW)
│   │   └── __init__.py   # Re-exports from core.services
│   │
│   ├── dspy/             # Task-based DSPy facades
│   │   ├── signatures/   # Re-exports with task-based names
│   │   ├── modules/      # Re-exports DSPy modules
│   │   └── programs/     # Re-exports DSPy programs
│   │
│   ├── infrastructure/   # Technical infrastructure facade
│   │   └── database/     # Re-exports database layer
│   │
│   ├── api/              # FastAPI implementation
│   │   ├── app.py        # Application factory
│   │   ├── routes/       # API endpoints (v2 main, v1 experimental chat)
│   │   ├── schemas/      # Pydantic models
│   │   └── cache/        # Caching layer (NEW)
│   │
│   ├── core/             # Core business logic
│   │   ├── dspy/         # DSPy integration (actual code)
│   │   ├── services/     # Service implementations
│   │   ├── models.py     # Pydantic models
│   │   └── config.py     # Configuration models
│   │
│   ├── db/               # Database layer
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── repositories.py # Repository implementations
│   │   └── database.py   # Connection management
│   │
│   ├── cli/              # Command-line interface
│   │   ├── app.py        # Typer application
│   │   ├── commands/     # Individual commands
│   │   └── client.py     # API client
│   │
│   ├── taxonomy/         # Taxonomy management
│   │   └── manager.py    # Taxonomy operations
│   │
│   ├── validators/       # Skill validation
│   │   └── skill_validator.py
│   │
│   ├── analytics/        # Usage analytics
│   │   └── engine.py     # Tracking and recommendations
│   │
│   ├── onboarding/       # User onboarding
│   │   └── bootstrap.py  # Skill bootstrapping
│   │
│   ├── llm/              # LLM configuration
│   │   ├── dspy_config.py # Centralized DSPy setup
│   │   └── fleet_config.py # Provider configuration
│   │
│   └── common/           # Shared utilities
│       ├── utils.py      # JSON parsing, type conversion
│       ├── paths.py      # Path utilities
│       ├── security.py   # Path sanitization
│       └── async_utils.py # Async helpers
```

### Internal Implementation

```
skill-fleet/
├── src/skill_fleet/
│   ├── api/              # FastAPI implementation
│   │   ├── app.py        # Application factory
│   │   ├── routes/       # API endpoints
│   │   ├── schemas/      # Pydantic models
│   │   ├── middleware/   # CORS, logging, etc.
│   │   └── jobs.py       # Background job system
│   │
│   ├── core/             # Core business logic
│   │   ├── dspy/         # DSPy integration (actual code)
│   │   │   ├── modules/  # Phase 1, 2, 3 modules
│   │   │   ├── signatures/ # DSPy signatures
│   │   │   ├── metrics/  # Quality metrics
│   │   │   └── skill_creator.py # Main orchestrator
│   │   ├── models.py     # Pydantic models
│   │   ├── config.py     # Configuration models
│   │   └── creator.py    # Skill creator facade
│   │
│   ├── db/               # Database layer
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── repositories.py # Repository pattern
│   │   └── database.py   # Connection management
│   │
│   ├── cli/              # Command-line interface
│   │   ├── app.py        # Typer application
│   │   ├── commands/     # Individual commands
│   │   └── client.py     # API client
│   │
│   ├── taxonomy/         # Taxonomy management
│   │   └── manager.py    # Taxonomy operations
│   │
│   ├── validators/       # Skill validation
│   │   └── skill_validator.py
│   │
│   ├── analytics/        # Usage analytics
│   │   └── engine.py     # Tracking and recommendations
│   │
│   ├── onboarding/       # User onboarding
│   │   └── bootstrap.py  # Skill bootstrapping
│   │
│   ├── llm/              # LLM configuration
│   │   ├── dspy_config.py # Centralized DSPy setup
│   │   └── fleet_config.py # Provider configuration
│   │
│   ├── common/           # Shared utilities
│   │   ├── utils.py      # JSON parsing, type conversion
│   │   ├── paths.py      # Path utilities
│   │   ├── security.py   # Path sanitization
│   │   └── async_utils.py # Async helpers
│   │
│   └── compat/           # Compatibility layer
│       ├── __init__.py   # Re-export helpers
│       └── deprecation.py # Deprecation warnings
```

## Import Guidelines

### Recommended Patterns

#### For Application Code

```python
# FastAPI application
from skill_fleet.app import create_app, app

# Domain models (DDD style)
from skill_fleet.domain.skill import SkillMetadata, Capability
from skill_fleet.domain.taxonomy import TaxonomyManager

# DSPy components (task-based)
from skill_fleet.dspy.signatures import GatherRequirements, AnalyzeIntent
from skill_fleet.dspy.modules import Phase1UnderstandingModule
from skill_fleet.dspy.programs import SkillCreationProgram

# Services
from skill_fleet.services import BaseService, ConversationSession

# Infrastructure
from skill_fleet.infrastructure.database import get_db, SkillRepository
```

#### For Internal Code

```python
# Core implementations
from skill_fleet.core.dspy import SkillCreationProgram
from skill_fleet.core.dspy.modules.phase1_understanding import Phase1UnderstandingModule
from skill_fleet.core.models import SkillMetadata

# API internals
from skill_fleet.api.app import create_app
from skill_fleet.api.routes import skills, taxonomy

# Database
from skill_fleet.db import get_db, SkillRepository
from skill_fleet.db.models import SkillModel

# Taxonomy
from skill_fleet.taxonomy.manager import TaxonomyManager
```

## Completed Work

### Phase 1: Foundation ✅
- Created directory structure
- Set up re-export compatibility layers
- Extracted common utilities to `common/`
- Centralized DSPy configuration in `llm/dspy_config.py`

### Phase 2: Code Quality & TODO Resolution ✅

#### Implementations Completed:
1. **User Profile Storage** (`onboarding/bootstrap.py`)
   - Saves user profiles to `_analytics/user_profiles/{user_id}.json`
   - Tracks onboarding progress and mounted skills

2. **Analytics Enhancement** (`analytics/engine.py`)
   - Added combo-based skill recommendations
   - Pattern matching for common skill combinations
   - Prioritized recommendations by usage frequency

3. **Documentation Updates**
   - Updated `app/main.py` to clarify delegation pattern
   - Enhanced TODO comments with implementation details
   - Removed misleading "migration period" language

4. **Code Quality**
   - Fixed linting issues (import sorting, unnecessary list() calls)
   - All unit tests passing (415 tests)
   - No regressions introduced

## Current Status

### What Works
- ✅ All facade directories provide clean import paths
- ✅ Internal implementation is well-organized
- ✅ Deprecation warnings guide migration
- ✅ Tests validate all functionality
- ✅ Documentation is comprehensive

### What's Intentional
- **Dual import paths**: Both facade and direct imports work
- **Delegation pattern**: `app/` delegates to `api/` (this is by design)
- **Re-exports**: Domain/services/infrastructure re-export for flexibility
- **Multiple DSPy locations**: `dspy/` (facade) and `core/dspy/` (implementation)

## Future Considerations

### Optional Enhancements

1. **Parent Skills Content Fetching**
   - Currently: Generation works without explicit parent context
   - Future: Could fetch parent skill content for better composition
   - See TODO in `core/dspy/skill_creator.py:330`

2. **Import Path Consolidation**
   - Currently: Multiple valid import paths for flexibility
   - Future: Could standardize on single canonical path if confusion arises
   - Would require codebase-wide import updates

3. **API Route Migration**
   - Currently: Routes in `api/routes/` work well
   - Future: Could move to `app/api/v2/` for version isolation
   - Low priority - current structure is clear

4. **Database Layer Migration**
   - Currently: `db/` contains implementation, `infrastructure/database/` re-exports
   - Future: Could physically move code to infrastructure
   - Benefit: Clearer separation of infrastructure concerns
   - Cost: Many import updates needed

## Decision Rationale

### Why Keep Both `core/dspy/` and `dspy/`?

**Reasons:**
1. **Clear organization**: Core implementation vs. public API
2. **Task-based naming**: `dspy/` provides task-based names (cleaner for users)
3. **Phase-based naming**: `core/dspy/` keeps phase-based structure (clear workflow)
4. **Flexibility**: Users can choose import style that fits their needs

**Trade-off:**
- More directories to navigate
- Potential confusion about which to use
- Mitigated by: Clear documentation and deprecation warnings

### Why Keep `app/` and `api/` Separate?

**Reasons:**
1. **Public vs. internal**: `app/` is entry point, `api/` is implementation
2. **Clean interface**: `app/main.py` is simple and clear
3. **Future flexibility**: Could add other app types (GraphQL, gRPC) without restructuring
4. **Version isolation**: Future API versions can be isolated

**Trade-off:**
- Extra indirection (delegation)
- Mitigated by: Clear documentation explaining pattern

## Testing

### Test Coverage
- **Unit tests**: 415 passing
- **Integration tests**: 25 (require API keys)
- **Coverage**: Maintained during restructuring

### Test Categories
- CLI commands
- API endpoints
- DSPy modules
- Validation logic
- Analytics engine
- Database operations

## Dependencies

No new dependencies added during restructuring. All changes use existing packages:
- FastAPI for API layer
- DSPy for workflow orchestration
- Typer for CLI
- SQLAlchemy for database
- Pydantic for models

## Migration Timeline

| Phase | Description | Status |
|-------|-------------|--------|
| 0.5 | Directory structure created | ✅ Complete |
| 1 | Re-export compatibility layers | ✅ Complete |
| 2 | Code quality & TODO resolution | ✅ Complete |
| 3 | Documentation updates | ✅ Complete |
| 4 | Optional: Import consolidation | 🔄 Optional |
| 5 | Optional: Physical code moves | 🔄 Optional |
| 6 | Optional: Remove deprecations | 🔄 Optional |
| 7 | Optional: API version migration | 🔄 Optional |

## Conclusion

The restructuring has successfully established:
1. **Clear architecture** with facade pattern
2. **Backward compatibility** through re-exports
3. **Improved organization** with separation of concerns
4. **Flexible imports** supporting multiple styles
5. **No regressions** - all tests passing

The current structure is stable, maintainable, and ready for continued development. Future phases are optional enhancements that can be considered based on team feedback and evolving needs.

## References

- [Cleanup & Optimization Plan](../../plans/cleanup-and-optimization-plan.md)
- [API Documentation](../api/index.md)
- [DSPy Documentation](../dspy/index.md)
- [Developer Reference](../concepts/developer-reference.md)
- [Contributing Guide](../development/CONTRIBUTING.md)
