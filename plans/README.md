# Plans Directory

This directory contains planning documents for the Skills Fleet project.

**Note:** This directory is excluded from git (see .gitignore) to keep planning documentation local-only.

## Directory Structure

```
plans/
├── README.md                           # This file
├── archive/                            # Completed/legacy plans
├── future/                             # Future exploration plans
└── [active plans]                      # Current work-in-progress plans
```

## Active Plans

| File                                          | Description                                           | Status              |
|-----------------------------------------------|-------------------------------------------------------|---------------------|
| `plan-main-restructure-latest.md`             | Main restructure plan (task-based DSPy organization)  | Active ✅           |
| `EXEC-0.2-optimizer-auto-selection.md`        | DSPy optimizer auto-selection strategy                 | Reference           |
| `technical-debt-audit.md`                     | Technical debt inventory and prioritization            | Reference           |
| `cleanup-and-optimization-plan.md`            | Code deduplication and optimization                    | Partially Complete  |

## Recent Progress (2026-01-23)

### Completed Tasks ✅

**Phase 1: Restructure DSPy Signatures by Task**
- ✅ Renamed signature directories from phase-based to task-based
- ✅ Created task-based subdirectories:
  - `task_analysis_planning/` (Phase 1)
  - `content_generation/` (Phase 2)
  - `quality_assurance/` (Phase 3)
  - `signature_optimization/` (Signature tuning)
- ✅ Renamed signature files:
  - `chat.py` → `conversational_interface.py`
  - `hitl.py` → `human_in_the_loop.py`

**Phase 2: Create Workflows Layer**
- ✅ Created `src/skill_fleet/workflows/` package
- ✅ Built 6 workflow orchestrators:
  - `TaskAnalysisOrchestrator` - Phase 1 understanding & planning
  - `ContentGenerationOrchestrator` - Phase 2 skill content creation
  - `QualityAssuranceOrchestrator` - Phase 3 validation & refinement
  - `HITLCheckpointManager` - HITL checkpoint management
  - `ConversationalOrchestrator` - Multi-turn conversation workflow
  - `SignatureTuningOrchestrator` - Signature optimization workflow

**Cleanup: Remove Duplicate Facade Layer**
- ✅ Removed `src/skill_fleet/dspy/` facade directory
- ✅ Removed `src/skill_fleet/compat/` compatibility layer
- ✅ Updated test imports to use new paths
- ✅ Fixed `test_core_rework.py` and `test_signature_reasoning_types.py`

**MLflow Integration Verification**
- ✅ Fixed `log_parameter()` function to support both 2-arg and 3-arg forms
- ✅ Verified all 6 workflow orchestrators have proper MLflow integration
- ✅ Tested MLflow logging with dual-form parameter support

**Configuration Files Review**
- ✅ Reviewed `config/config.yaml` - clean with proper task-model mapping
- ✅ Reviewed training data - properly versioned v2, v3, v4
- ✅ Reviewed `SKILL_md_template.md` - comprehensive agentskills.io compliant template

**Documentation Revamp**
- ✅ Archived outdated docs (PHASE_0_FOUNDATION.md, UPDATE_SUMMARY.md)
- ✅ Moved PHASE_1_OPTIMIZATION.md to docs/dspy/
- ✅ Reorganized top-level docs into proper categories:
  - ADAPTIVE_METRIC_WEIGHTING.md → docs/dspy/
  - BACKGROUND_JOBS.md → docs/architecture/
  - CLI_SYNC_COMMANDS.md → docs/cli/
  - DATABASE_SYNC.md → docs/architecture/
  - JOB_PERSISTENCE.md → docs/architecture/
  - OPTIMIZER_SELECTION.md → docs/dspy/optimization.md
  - STREAMING_ARCHITECTURE.md → docs/architecture/
  - STREAMING_QUICKSTART.md → docs/getting-started/
  - MLFLOW_SETUP.md → docs/getting-started/
- ✅ Created comprehensive `docs/workflows/` documentation for all 6 orchestrators
- ✅ Updated `docs/index.md` with new structure and recent changes

### In Progress 🔄

*No tasks currently in progress - all immediate cleanup tasks completed*

### Pending ⏳

See task list for full pending items:
- Phase 3: Separate Domain Logic (depends on workflows)
- Phase 4: Implement DSPy 3.1.2 Best Practices
- Phase 5: Wire FastAPI to Workflows
- Phase 6: Restructure CLI
- Update tests for new structure
- MLflow integration for skill creation

## Archived Plans

Plans in `./archive/` represent completed phases or legacy documentation:

| Category                | Examples                                      |
|-------------------------|-----------------------------------------------|
| Implementation phases  | `implementation-phase-*.md` (completed)      |
| CLI reviews            | `cli-*.md` (merged to codebase)               |
| Feature plans           | `skills-taxonomy-*.md` (implemented)          |
| Old restructure plans   | `plan-main-restructure.md` (superseded)       |

## Plan Naming Convention

- **Date-prefixed**: `YYYY-MM-DD-description.md` for time-sensitive plans
- **Feature-based**: `feature-name-plan.md` for ongoing features
- **Versioned**: `plan-name-version.md` for evolving plans (e.g., `latest`)

---
*Last updated: 2026-01-23*
