# Plans Directory

This directory contains planning documents for the Skills Fleet project.

## Directory Structure

```
plans/
├── README.md                 # This file
├── archive/                  # Completed/legacy plans
└── [active plans]            # Current work-in-progress plans
```

## Active Plans

| File | Description | Status |
|------|-------------|--------|
| `cleanup-and-optimization-plan.md` | Code deduplication, legacy removal, and optimization tasks | Draft - In Progress |
| `skills-fleet_codebase_restructure_4833ae18.plan.md` | Codebase restructuring and organization | Pending |
| `2026-01-09-fastapi-baseline-tests.md` | FastAPI production patterns baseline test scenarios | Active |
| `2026-01-09-fastapi-production-patterns-design.md` | FastAPI production patterns skill design | Active |
| `2026-01-12-cli-chat-ux.md` | Improve API-backed CLI chat interactive experience | Active |

## Archived Plans

Plans in `./archive/` represent completed phases or legacy documentation that informed the current implementation:

| File | Description | Archive Reason |
|------|-------------|----------------|
| `implementation-phase-1.md` | Foundation phase (Week 1-2) | Completed ✅ |
| `implementation-phase-2.md` | Core Workflow phase (Week 3-4) | Completed ✅ |
| `implementation-phase-final.md` | Final implementation summary | Phases 1-2 completed |
| `overview.md` | High-level project overview and vision | Foundational planning complete |
| `skill-creator-plan.md` | Detailed skill creator implementation | Largely implemented |
| `skills-creation-workflow.md` | Workflow design document | Implemented |
| `skills-taxonomy-implementation-strategy.md` | Taxonomy implementation strategy | All phases completed ✅ |
| `taxonomy-system.md` | Taxonomy system design | Implemented |

## Plan Naming Convention

- **Date-prefixed**: `YYYY-MM-DD-description.md` for time-sensitive or feature-specific plans
- **Feature-based**: `feature-name-plan.md` for ongoing feature development
- **Generated**: `name_hash.plan.md` for auto-generated planning documents

## Archiving Guidelines

Move plans to `./archive/` when:
- All tasks/phases are marked as completed (✅)
- The plan has been superseded by a newer version
- The feature/phase described has been fully implemented
- The plan is no longer actively referenced for current work

---
*Last reorganized: 2026-01-11*
