---
name: skills-fleet codebase restructure
overview: Restructure the skills-fleet codebase from `src/skill_fleet/` to a cleaner organization, identify and address legacy/unused files, fix naming inconsistencies, and reorganize large files for better maintainability.
todos:
  - id: fix-legacy-references
    content: Fix all 'agentic_fleet' references to 'skill_fleet' in README.md, AGENTS.md, package.json, and verify_migration.sh
    status: pending
  - id: rename-cli-directory
    content: Rename 'cli_submodules/' to 'cli/' and update all imports
    status: pending
  - id: reorganize-config
    content: Move config.yaml and profiles/ to root config/ directory and update all path references
    status: pending
  - id: move-tui
    content: Move src/tui/ to src/skill_fleet/ui/ and update package.json build configs
    status: pending
  - id: audit-phase1-phase2
    content: Determine if phase1_understand.py and phase2_scope.py are actually used or legacy files
    status: pending
  - id: separate-agent
    content: Create agent/ directory and move conversational_*.py files, then split large conversational_agent.py
    status: pending
  - id: consolidate-rewards
    content: Consolidate workflow/rewards.py with rewards/ directory or reorganize clearly
    status: pending
  - id: extract-research-tracing
    content: Extract research_tools.py and reasoning_*.py to workflow/research/ and workflow/tracing/
    status: pending
  - id: update-imports
    content: Update all import statements throughout codebase to match new structure
    status: pending
  - id: update-tests
    content: Update all test files with new import paths and verify tests pass
    status: pending
  - id: update-docs
    content: Update documentation (AGENTS.md, README.md, docs/) with new structure and paths
    status: pending
  - id: verify-cli-tui
    content: Verify CLI commands and TUI build work with new structure
    status: pending
isProject: false
---

# Skills-Fleet Codebase Restructuring Plan

## Current State Analysis

### Statistics

- **Total Python files**: 40
- **Total LOC**: 15,381 lines
- **Package structure**: `src/skill_fleet/`
- **Largest files**:
  - `conversational_agent.py`: 1,557 lines
  - `modules.py`: 1,138 lines
  - `conversational_modules.py`: 1,113 lines
  - `taxonomy/manager.py`: 947 lines
  - `workflow/models.py`: 718 lines
  - `cli_submodules/main.py`: 671 lines

### Issues Identified

1. **Legacy References**:

   - `agentic_fleet` references in `README.md`, `AGENTS.md`, `package.json`, `verify_migration.sh`
   - Package.json TUI path: `src/agentic_fleet/tui/main.tsx` (should be `src/tui/main.tsx`)

2. **Directory Structure Issues**:

   - Config file at `src/skill_fleet/config.yaml` (should be at root or `config/`)
   - CLI in `cli_submodules/` (awkward naming, should be `cli/`)
   - TUI at `src/tui/` (should be `src/skill_fleet/ui/` for consistency)
   - Workflow directory has both `modules.py` and `conversational_modules.py` (unclear separation)

3. **Potential Legacy/Unused Files**:

   - `phase1_understand.py` and `phase2_scope.py`: Appear to be separate implementation path for reasoning visibility, but not directly imported by main workflow
   - `phase1_signatures.py` and `phase2_signatures.py`: Separate signatures for Phase1/Phase2
   - `rewards.py` at root of workflow vs `rewards/` directory with phase1/phase2 rewards (consolidation needed)

4. **Large Files Needing Refactoring**:

   - `conversational_agent.py` (1,557 lines) - should be split into agent + handlers
   - `modules.py` (1,138 lines) - consider splitting by workflow step
   - `conversational_modules.py` (1,113 lines) - consider splitting by agent capability
   - `taxonomy/manager.py` (947 lines) - consider splitting into manager + helpers

## Proposed New Structure

```
src/skill_fleet/
├── __init__.py
├── cli/                          # Renamed from cli_submodules
│   ├── __init__.py
│   ├── main.py                   # Main CLI entry point
│   ├── commands/                 # Split large main.py
│   │   ├── __init__.py
│   │   ├── create.py
│   │   ├── validate.py
│   │   ├── migrate.py
│   │   ├── optimize.py
│   │   ├── analytics.py
│   │   └── interactive.py
│   └── interactive_cli.py
│
├── core/                         # Core domain logic (renamed from top-level mix)
│   ├── __init__.py
│   ├── taxonomy/
│   │   ├── __init__.py
│   │   ├── manager.py            # Split into manager + helpers
│   │   └── helpers.py            # Extracted from manager.py
│   └── validators/
│       ├── __init__.py
│       └── skill_validator.py
│
├── workflow/                     # Main skill creation workflow
│   ├── __init__.py
│   ├── creator.py                # Renamed from skill_creator.py
│   ├── programs.py               # DSPy programs
│   ├── signatures.py             # Main workflow signatures
│   ├── modules.py                # Main workflow modules (consider splitting)
│   │   ├── understand.py         # Future: split by step
│   │   ├── plan.py
│   │   ├── initialize.py
│   │   ├── edit.py
│   │   └── package.py
│   ├── feedback.py               # HITL feedback handlers
│   ├── rewards.py                # Main rewards (consolidate with rewards/)
│   ├── evaluation.py
│   ├── optimizer.py
│   ├── optimize.py
│   ├── models.py                 # Pydantic models
│   │
│   ├── research/                 # Research tools (extracted)
│   │   ├── __init__.py
│   │   ├── tools.py              # Renamed from research_tools.py
│   │   └── filesystem.py         # Extracted filesystem operations
│   │
│   ├── tracing/                  # Reasoning and tracing (extracted)
│   │   ├── __init__.py
│   │   ├── tracer.py             # Renamed from reasoning_tracer.py
│   │   ├── config.py             # Renamed from reasoning_config.py
│   │   └── mlflow.py             # Renamed from mlflow_integration.py
│   │
│   └── data/                     # Training data
│       └── trainset.json
│
├── agent/                        # Conversational agent (separated from workflow)
│   ├── __init__.py
│   ├── agent.py                  # Renamed from conversational_agent.py (split)
│   ├── handlers.py               # Extracted handler logic
│   ├── state.py                  # State management
│   ├── modules.py                # Renamed from conversational_modules.py
│   ├── signatures.py             # Renamed from conversational_signatures.py
│   └── phase1/                   # Phase 1 reasoning (if still needed)
│       ├── __init__.py
│       ├── understand.py         # Renamed from phase1_understand.py
│       └── signatures.py         # Renamed from phase1_signatures.py
│   └── phase2/                   # Phase 2 reasoning (if still needed)
│       ├── __init__.py
│       ├── scope.py              # Renamed from phase2_scope.py
│       └── signatures.py         # Renamed from phase2_signatures.py
│
├── llm/                          # LLM configuration and client
│   ├── __init__.py
│   ├── config.py                 # Renamed from fleet_config.py
│   └── client.py                 # Future: extracted client logic
│
├── analytics/                    # Analytics and recommendations
│   ├── __init__.py
│   └── engine.py
│
├── onboarding/                   # User onboarding
│   ├── __init__.py
│   └── bootstrap.py
│
├── migration.py                  # Migration utilities (could move to cli/commands/)
│
└── ui/                           # TUI (moved from src/tui)
    ├── __init__.py
    ├── main.tsx
    └── src/
        ├── components/
        ├── hooks/
        ├── services/
        └── tools/

config/                           # Configuration files (new directory)
├── config.yaml                   # Moved from src/skill_fleet/config.yaml
└── profiles/
    └── bootstrap_profiles.json   # Moved from src/skill_fleet/config/profiles/
```

## Migration Steps

### Phase 1: Fix Legacy References

1. Update all `agentic_fleet` references to `skill_fleet`:

   - `README.md`
   - `AGENTS.md`
   - `package.json` (TUI script path)
   - `verify_migration.sh`

2. Update import paths in all Python files
3. Update pyproject.toml if needed

### Phase 2: Reorganize Core Structure

1. Rename `cli_submodules/` → `cli/`
2. Move config files:

   - `src/skill_fleet/config.yaml` → `config/config.yaml`
   - `src/skill_fleet/config/profiles/` → `config/profiles/`

3. Update all config path references
4. Move TUI: `src/tui/` → `src/skill_fleet/ui/`
5. Update package.json and build configs

### Phase 3: Consolidate Workflow

1. Decide on Phase1/Phase2 files:

   - **Option A**: Keep as separate reasoning visibility path → move to `agent/phase1/` and `agent/phase2/`
   - **Option B**: Integrate into main workflow → merge functionality into main modules
   - **Recommendation**: Option A - keep separate but organize better

2. Consolidate rewards:

   - Merge `workflow/rewards.py` with `workflow/rewards/phase1_rewards.py` and `phase2_rewards.py`
   - Keep unified rewards in `workflow/rewards.py`
   - Keep phase-specific rewards in `agent/phase1/` and `agent/phase2/`

3. Extract research tools to `workflow/research/`
4. Extract tracing to `workflow/tracing/`

### Phase 4: Separate Conversational Agent

1. Create `agent/` directory
2. Move conversational files:

   - `conversational_agent.py` → `agent/agent.py` (then split)
   - `conversational_modules.py` → `agent/modules.py`
   - `conversational_signatures.py` → `agent/signatures.py`

3. Split `agent.py`:

   - Core agent logic → `agent/agent.py`
   - Handler logic → `agent/handlers.py`
   - State management → `agent/state.py`

4. Move Phase1/Phase2 to `agent/phase1/` and `agent/phase2/`

### Phase 5: Refactor Large Files (Future)

1. Split `taxonomy/manager.py`:

   - Core manager → `core/taxonomy/manager.py`
   - Helper functions → `core/taxonomy/helpers.py`

2. Split `workflow/modules.py`:

   - One file per workflow step (understand.py, plan.py, etc.)
   - Or keep as single file but add clear sections

3. Split `agent/modules.py`:

   - One module per agent capability
   - Or organize by functional area

### Phase 6: Clean Up Unused Files

1. Audit Phase1/Phase2 usage:

   - Check if `Phase1Understand` and `Phase2Scope` are actually called
   - If unused, mark for deletion or move to `legacy/` for reference

2. Check for duplicate functionality:

   - `signatures.py` vs `phase1_signatures.py`/`phase2_signatures.py`
   - Ensure clear separation of concerns

3. Remove empty directories and `__pycache__`
4. Update `.gitignore` if needed

## File Location Changes Summary

| Current Path | New Path | Notes |

|-------------|----------|-------|

| `src/skill_fleet/cli_submodules/` | `src/skill_fleet/cli/` | Rename directory |

| `src/skill_fleet/config.yaml` | `config/config.yaml` | Move to root config/ |

| `src/skill_fleet/config/profiles/` | `config/profiles/` | Move to root config/ |

| `src/tui/` | `src/skill_fleet/ui/` | Move under package |

| `src/skill_fleet/workflow/conversational_*.py` | `src/skill_fleet/agent/` | Separate agent logic |

| `src/skill_fleet/workflow/phase1_*.py` | `src/skill_fleet/agent/phase1/` | Organize by phase |

| `src/skill_fleet/workflow/phase2_*.py` | `src/skill_fleet/agent/phase2/` | Organize by phase |

| `src/skill_fleet/workflow/research_tools.py` | `src/skill_fleet/workflow/research/tools.py` | Extract to subdir |

| `src/skill_fleet/workflow/reasoning_*.py` | `src/skill_fleet/workflow/tracing/` | Rename and organize |

| `src/skill_fleet/workflow/mlflow_integration.py` | `src/skill_fleet/workflow/tracing/mlflow.py` | Move to tracing |

| `src/skill_fleet/llm/fleet_config.py` | `src/skill_fleet/llm/config.py` | Rename for clarity |

| `src/skill_fleet/taxonomy/manager.py` | `src/skill_fleet/core/taxonomy/manager.py` | Move to core |

| `src/skill_fleet/validators/` | `src/skill_fleet/core/validators/` | Move to core |

| `src/skill_fleet/workflow/skill_creator.py` | `src/skill_fleet/workflow/creator.py` | Shorter name |

## Import Path Updates Required

Update all imports from:

- `skill_fleet.cli_submodules` → `skill_fleet.cli`
- `skill_fleet.workflow.conversational_agent` → `skill_fleet.agent.agent`
- `skill_fleet.workflow.conversational_modules` → `skill_fleet.agent.modules`
- `skill_fleet.workflow.phase1_understand` → `skill_fleet.agent.phase1.understand`
- `skill_fleet.workflow.reasoning_tracer` → `skill_fleet.workflow.tracing.tracer`
- `skill_fleet.llm.fleet_config` → `skill_fleet.llm.config`
- Config path references: update hardcoded paths to use `config/config.yaml`

## Testing Strategy

1. **Unit Tests**: Update import paths in all test files
2. **Integration Tests**: Verify CLI commands still work
3. **Import Verification**: Run `python -m skill_fleet.cli.main --help` to verify imports
4. **TUI Build**: Verify TUI builds with new path structure
5. **Documentation**: Update all code references in docs

## Benefits of Restructure

1. **Clearer Organization**: Separation of workflow, agent, and core logic
2. **Better Maintainability**: Smaller, focused files and directories
3. **Reduced Confusion**: Eliminates `agentic_fleet` legacy references
4. **Improved Discoverability**: Logical grouping of related functionality
5. **Easier Testing**: Clear module boundaries make testing straightforward
6. **Scalability**: Structure supports future growth without reorganization

## Risks & Considerations

1. **Breaking Changes**: All import paths will change - requires comprehensive testing
2. **Git History**: Large moves may complicate git blame/history (consider `git mv` with history)
3. **Documentation**: Extensive docs need updating
4. **External Dependencies**: Any external code using these imports will break
5. **Phase1/Phase2**: Need to verify these are actually used before reorganizing

## Next Steps

1. **Audit Phase1/Phase2 Usage**: Determine if these files are actually called in production code
2. **Create Migration Script**: Python script to automate import path updates
3. **Branch Strategy**: Create feature branch for restructuring
4. **Incremental Migration**: Phase by phase to minimize risk
5. **Update CI/CD**: Ensure tests pass after each phase