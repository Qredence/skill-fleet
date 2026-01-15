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

| File                                               | Description                                                            | Status              |
|----------------------------------------------------|------------------------------------------------------------------------|---------------------|
| `2026-01-15-api-first-evolution-plan.md`           | API-First architecture evolution (6 phases)                            | Phase 2 In Progress |
| `2026-01-15-skill-creation-improvement-plan.md`    | DSPy optimization and skill quality improvements                       | Draft               |
| `2026-01-15-skill-creation-hardening.md`           | Fix HITL duplication, validation staleness, and draft artifact quality | Mostly Complete     |
| `2026-01-12-cli-chat-ux.md`                        | Improve API-backed CLI chat interactive experience                     | Active              |
| `2026-01-09-fastapi-baseline-tests.md`             | FastAPI production patterns baseline test scenarios (RED phase)        | In Progress         |
| `2026-01-09-fastapi-production-patterns-design.md` | FastAPI production patterns skill design                               | Active              |
| `cleanup-and-optimization-plan.md`                 | Code deduplication, legacy removal, and optimization tasks             | Partially Complete  |

## Code Quality Progress (2026-01-15)

The following phases from the Code Quality & Testing Improvement initiative have been completed:

| Phase   | Description                               | Status                       |
|---------|-------------------------------------------|------------------------------|
| Phase 1 | Linting & Code Style Cleanup              | ✅ Complete                   |
| Phase 2 | Test Coverage Improvement (+53 tests)     | ✅ Complete                   |
| Phase 3 | God Object Decomposition (agent/agent.py) | ⏳ Not Started                |
| Phase 4 | DSPy Best Practices Alignment             | ✅ Complete (already aligned) |
| Phase 5 | API Route Cleanup                         | ✅ Complete                   |
| Phase 6 | Documentation & Cleanup                   | ⏳ Not Started                |

**Key Accomplishments:**
- Fixed six ruff linting issues, formatted 13 files
- Added 53 new tests (+20% coverage)
- Created `common/security.py` for centralized path sanitization
- Created `api/dependencies.py` for FastAPI dependency injection
- Added `response_model` annotations to all API endpoints
- Verified DSPy implementation follows best practices (242 typed fields, async/sync consistency)

## API-First Evolution Progress (2026-01-15)

Progress on the API-First architecture evolution plan:

| Phase   | Description                               | Status         |
|---------|-------------------------------------------|----------------|
| Phase 1 | Schema Unification & Dependency Injection | ✅ Complete     |
| Phase 2 | Thin Client Refactoring                   | 🔄 In Progress |
| Phase 3 | Real-Time Communication (SSE)             | ⏳ Not Started  |
| Phase 4 | Persistent Job State                      | ⏳ Not Started  |
| Phase 5 | Automated SDK Generation                  | ⏳ Not Started  |
| Phase 6 | Cleanup & Consistency                     | ⏳ Not Started  |

**Phase 2 Progress (Thin Client Refactoring):**
- ✅ Created `api/schemas/hitl.py` with `StructuredQuestion`, `QuestionOption` models
- ✅ Added `normalize_questions()` server-side normalization function
- ✅ Updated `HITLPromptResponse.questions` to use typed `list[StructuredQuestion]`
- ✅ Simplified CLI's `runner.py` to pass through pre-structured data
- ⏳ CLI Pydantic validation for API responses (optional enhancement)
- ⏳ UI refactoring to call API directly (cliBridge.ts → apiClient.ts)

## Skill Creation Hardening Progress (2026-01-15)

Progress on the Skill Creation Hardening plan (`2026-01-15-skill-creation-hardening.md`):

**Completed:**
- ✅ Server HITL is event-driven (no polling race) - `wait_for_hitl_response()` uses Future + `notify_hitl_response()`
- ✅ DSPy `.forward()` warnings removed by switching to `.acall()` in Phase 1/2/3 modules
- ✅ Phase 3 re-validates after refinement so `validation_report` matches `refined_content`
- ✅ Draft saves preserve workflow metadata (capabilities, load_priority, keywords/scope/see_also)
- ✅ Authoring template updated with validator-required sections (`## Capabilities`, `## Dependencies`, `## Usage Examples`)
- ✅ `SkillValidator.validate_examples()` skips `examples/README.md`
- ✅ Phase 3 HITL validate/refine loops with bounded iterations
- ✅ Phase 3 canonicalizes YAML frontmatter from `SkillMetadata`
- ✅ Draft saves extract embedded artifacts (headings → `assets/`, code blocks → `examples/`)

**Remaining:**
- ⏳ Pydantic serializer warnings (Message/Choices/StreamingChoices) - needs stack trace and targeted fix
- ⏳ Optional: `prompt_id` versioning for full client idempotency

## Archived Plans

Plans in `./archive/` represent completed phases or legacy documentation that informed the current implementation:

| File                                                 | Description                                              | Archive Reason                              |
|------------------------------------------------------|----------------------------------------------------------|---------------------------------------------|
| `implementation-phase-1.md`                          | Foundation phase (Week 1-2)                              | Completed ✅                                 |
| `implementation-phase-2.md`                          | Core Workflow phase (Week 3-4)                           | Completed ✅                                 |
| `implementation-phase-final.md`                      | Final implementation summary                             | Phases 1-2 completed                        |
| `overview.md`                                        | High-level project overview and vision                   | Foundational planning complete              |
| `skill-creator-plan.md`                              | Detailed skill creator implementation                    | Largely implemented                         |
| `skills-creation-workflow.md`                        | Workflow design document                                 | Implemented                                 |
| `skills-taxonomy-implementation-strategy.md`         | Taxonomy implementation strategy                         | All phases completed ✅                      |
| `taxonomy-system.md`                                 | Taxonomy system design                                   | Implemented                                 |
| `nimble-serene-ember.md`                             | Enhanced transparency & interactivity for Guided Creator | Superseded by CLI Chat UX & API-First plans |
| `skills-fleet_codebase_restructure_4833ae18.plan.md` | Codebase restructuring and organization                  | Restructuring completed ✅                   |

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
*Last updated: 2026-01-15 14:27*
