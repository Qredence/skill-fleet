# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- Regression coverage for draft promotion and draft-save parsing helpers
  - Added API tests for `POST /api/v1/drafts/{job_id}/promote` (including `delete_draft=true`)
  - Added unit tests for safe filename handling and code block extraction in draft saves
  - Added unit tests for dict-like access helpers on core models

### Changed

- Internal refactors to reduce nesting and improve maintainability (no intended behavior change)
  - Draft promotion and draft save flows extracted into smaller, focused helpers
  - Validation workflow refactored to centralize threshold resolution and refinement logic
  - Conversation service response routing split into clearer helper methods
- CI release workflow can now be manually dispatched to publish an existing tag

### Fixed

- Draft promotion `delete_draft=true` no longer deletes the session file and then recreates it
- Draft promotion rollback paths preserve original tracebacks (bare `raise`)
- Draft save warning logs include traceback context for easier debugging

## [0.3.6] - 2026-02-03

### Added

- **Typed Phase Output Models** (February 2026)
  - New `src/skill_fleet/core/workflows/models.py` with Pydantic models for workflow contracts
  - `QualityThresholds` - Centralized quality threshold configuration with validation
  - Phase output models: `Phase1UnderstandingOutput`, `Phase2GenerationOutput`, `Phase3ValidationOutput`
  - Module output models: `RequirementsOutput`, `IntentOutput`, `TaxonomyOutput`, `DependencyOutput`, `PlanOutput`, etc.
  - Helper functions: `dict_to_requirements()`, `dict_to_intent()`, `dict_to_taxonomy()`, etc. for gradual migration
  - `DEFAULT_QUALITY_THRESHOLDS` global instance for consistent quality scoring across workflows

- **Centralized Utility Decorators**
  - `src/skill_fleet/common/logging_utils.py` - `sanitize_for_log()` function for safe logging of sensitive data
  - `src/skill_fleet/common/llm_fallback.py` - `@with_llm_fallback` decorator for graceful DSPy module degradation
  - `src/skill_fleet/common/utils.py` - `@timed_execution` decorator for performance tracking

### Changed

- **Workflows use centralized quality thresholds**
  - `GenerationWorkflow` now uses `DEFAULT_QUALITY_THRESHOLDS.refinement_target_quality` (0.80) instead of hardcoded 0.8
  - `ValidationWorkflow` now uses `DEFAULT_QUALITY_THRESHOLDS.validation_pass_threshold` (0.75) instead of hardcoded 0.75
  - Quality threshold parameters now accept `None` with automatic fallback to centralized defaults
  - Updated all workflow method signatures: `quality_threshold: float | None = None`

- **DSPy 3.1.2+ Async-First Refactoring**: Aligned codebase with DSPy best practices
  - Removed local wrapper modules (`pot.py`, `react.py`, `refine.py`)
  - Re-exported DSPy primitives (`ReAct`, `Refine`, `ProgramOfThought`) directly
  - Updated `BaseModule`: `aforward()` now primary abstract method, `forward()` delegates via `run_async`
  - Replaced all `asyncio.run()` calls in core modules with `dspy.utils.syncify.run_async`
  - Consolidated dual logic in modules to async-first pattern
  - Updated docstring examples to use recommended `module()` call pattern
  - Added comprehensive test suite (`test_async_first_refactor.py`) verifying:
    - Forward/aforward delegation working correctly
    - DSPy primitives re-exported properly
    - No legacy wrapper modules remain
    - `run_async` correctly bridges sync/async boundaries

### Fixed

- Missing imports in `validation/compliance.py` (`with_llm_fallback`, `timed_execution`)
- Missing `llm_fallback_enabled` import in `understanding/requirements.py`
- D401 docstring imperative mood violations in multiple modules
- `func.__name__` type error with `getattr()` fallback in `utils.py`
- Removed 7 unused `# type: ignore[override]` comments across modules
- Code formatting and linting across core modules (12 files reformatted)
- Type hints and import organization in refactored modules

## [0.3.5] - 2026-01-29

### Breaking Changes

- **Architecture Restructure**: Complete FastAPI-centric directory restructure
  - `src/skill_fleet/app/` → `src/skill_fleet/api/` (API layer flattening)
  - `src/skill_fleet/db/` → `src/skill_fleet/infrastructure/db/`
  - `src/skill_fleet/llm/` → `src/skill_fleet/dspy/` (centralized DSPy config)
  - New `src/skill_fleet/common/` top-level module for shared utilities
  - All imports converted from relative to absolute
- **Removed deprecated modules**:
  - `skill_fleet.core.creator` (use `api.services` instead)
  - `skill_fleet.onboarding.bootstrap`
  - `skill_fleet.agent` (entire agent package)
  - Old DSPy phase-based organization

### Added

- **FastAPI v1 API**: New clean API structure
  - Background task support for async skill creation
  - HITL (Human-in-the-Loop) integration with question types
  - Real-time streaming endpoints
  - Job management with polling
- **Workflow Architecture**: Task-based DSPy organization
  - `core/workflows/skill_creation/` with orchestrators
  - Understanding, Generation, and Validation workflows
  - Hierarchical MLflow tracking (parent + child runs)
- **Real-time CLI Chat** (`skill-fleet chat`):
  - Streaming updates with 100ms polling
  - Live thinking/reasoning display
  - Arrow key navigation for multi-choice questions
  - Immediate response to HITL prompts
- **Taxonomy improvements**:
  - `TaxonomyManager` with agentskills.io compliance
  - YAML frontmatter parsing for SKILL.md
  - Path resolution with alias support
  - Dependency validation and circular detection
- **Documentation**:
  - API migration guide (`docs/api/MIGRATION_V1_TO_V2.md`)
  - Import path guide (`docs/development/IMPORT_PATH_GUIDE.md`)
  - Service extension guide (`docs/development/SERVICE_EXTENSION_GUIDE.md`)

### Changed

- **DSPy Configuration**: Moved to centralized `skill_fleet.dspy` module
  - Task-specific LM instances via `get_task_lm()`
  - Environment variable support for `DSPY_CACHEDIR`, `DSPY_TEMPERATURE`
- **CLI improvements**:
  - New `terminal` command for Python-only interface
  - Fast polling for real-time updates (`--fast` flag)
- **Testing**: Restructured test directory to match source structure
  - `tests/api/` for API-specific tests
  - `tests/unit/` and `tests/integration/` separation

### Removed

- **Obsolete files** (from root directory):
  - `RE_STRUCTURE_SUMMARY.md`
  - `IMPLEMENTATION_SUMMARY.md`
  - `TASKLIST_PROGRESS.md`
- **Deprecated code**:
  - Legacy agent package (`src/skill_fleet/agent/`)
  - Old CLI onboarding modules
  - Outdated test files with broken imports

### Fixed

- All import paths updated to use absolute imports
- Circular dependency issues resolved
- Lifespan startup errors fixed
- Monitoring module import issues resolved

---

## [0.2.0] - 2026-01-16

### Breaking Changes

- **Taxonomy Migration**: Simplified from 8-level to 2-level taxonomy
  - Old paths: `skills/technical_skills/programming/languages/python/async`
  - New paths: `skills/python/async`
  - Legacy paths still resolve with deprecation warnings
  - Use canonical paths in new code and documentation

### Added

- `src/skill_fleet/taxonomy/models.py`: Pydantic models for taxonomy index
- `scripts/generate_taxonomy_index.py`: Generate index from mapping report
- `scripts/migrate_skills_structure.py`: Migrate skills to canonical paths
- `skills/taxonomy_index.json`: Canonical index for path resolution
- Taxonomy alias support for backward compatibility

### Changed

- `TaxonomyManager`: Added index-based skill resolution with alias support
- `SkillValidator`: Enhanced path traversal protection and alias detection
- API routes: Updated to use canonical path resolution
- Documentation: Updated for new taxonomy structure

### Removed

- Legacy taxonomy directories: `technical_skills/`, `domain_knowledge/`, `task_focus_areas`, etc.
- Deprecated `src/skill_fleet/migration.py` (workflow consolidated into core/)
- Placeholder directories: `miscellaneous/`

### Fixed

- Deprecated print statements in onboarding (replaced with logging)
- Docstring formatting inconsistencies
- Path resolution now supports both canonical IDs and legacy aliases
- **Automatic Linting & Formatting** (January 16, 2026)
  - Added `_lint_and_format_skill()` method to TaxonomyManager
  - All newly generated skills are automatically linted and formatted
  - Runs `ruff check` and `ruff format` on Python files in examples/ and scripts/
  - Fixed existing linting issues in skills directory:
    - Added docstring to `skills/devops/docker/examples/example_2.py`
    - Sorted imports in `skills/memory/universal/examples/basic_usage.py`
    - Removed f-string prefix from constant string
  - Linting failures log warnings but don't block skill creation
- **Migration Module Recreation** (January 16, 2026)
  - Recreated `src/skill_fleet/common/migration.py` with `migrate_all_skills()` function
  - Fixed broken import in `src/skill_fleet/cli/commands/migrate.py`
  - Import now correctly points to `...common.migration` instead of deprecated `...migration`

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] - 2026-01-11

### Added

- Conversational modules using DSPy MultiChainComparison and Predict ([7a36e76](https://github.com/Qredence/skill-fleet/commit/7a36e76))
  - Modules for interpreting user intent, detecting multi-skill needs, generating clarifying questions
  - Simple prediction modules for assessing readiness, confirming understanding, processing feedback
  - Comprehensive unit tests for all new conversational modules
- Interactive Typer CLI (`interactive_typer.py`) for enhanced user interaction ([7a36e76](https://github.com/Qredence/skill-fleet/commit/7a36e76))
- MLflow database file for model tracking ([18a32ba](https://github.com/Qredence/skill-fleet/commit/18a32ba))
- Comprehensive Copilot instructions and environment setup ([699c2e4](https://github.com/Qredence/skill-fleet/commit/699c2e4))
  - `.github/copilot-instructions.md` with build/test workflows
  - `copilot-setup-steps.yml` for environment configuration
  - Network/firewall limitations documentation
- Enhanced SKILL.md template with improved structure and detailed guidelines ([d57261d](https://github.com/Qredence/skill-fleet/commit/d57261d))
- Metadata template (`config/templates/metadata_template.json`) for tooling support ([d57261d](https://github.com/Qredence/skill-fleet/commit/d57261d))
- Python testing instructions (`.github/instructions/python-tests.instructions.md`) ([8ce71ef](https://github.com/Qredence/skill-fleet/commit/8ce71ef))
- `datasets` dependency for improved data handling ([d57261d](https://github.com/Qredence/skill-fleet/commit/d57261d))
- Centralized DSPy configuration via `skill_fleet.llm.dspy_config` module
  - `configure_dspy()` function for one-time DSPy initialization
  - `get_task_lm()` function for task-specific LM instances
  - Environment variable support for `DSPY_CACHEDIR` and `DSPY_TEMPERATURE`
- `revision_feedback` parameter to `EditSkillContent` signature for iterative refinement
- Proper UTC timestamp generation for skill evolution metadata using `datetime.now(UTC).isoformat()`
- Common utilities module `src/skill_fleet/common/utils.py`
  - `safe_json_loads()` for robust JSON parsing with fallback
  - `safe_float()` for safe float conversion
- Documentation:
  - API reference documentation for new modules
  - DSPy configuration section in CLI reference
  - Contributing guide (`docs/development/CONTRIBUTING.md`)
  - Architecture Decision Records (`docs/development/ARCHITECTURE_DECISIONS.md`)

### Changed

- Upgraded LLM model version in web search and integration tests for improved performance ([7a36e76](https://github.com/Qredence/skill-fleet/commit/7a36e76))
- Major refactoring of agent, CLI, and workflow modules for improved code quality ([699c2e4](https://github.com/Qredence/skill-fleet/commit/699c2e4))
- Updated README.md with repository clone URL ([8ce71ef](https://github.com/Qredence/skill-fleet/commit/8ce71ef))
- Evolution metadata now includes proper timestamps and change summaries
  - `timestamp`: ISO 8601 UTC timestamp of creation/revision
  - `change_summary`: Human-readable description of changes
- CLI now calls `configure_dspy()` on startup for consistent DSPy settings
- Improved revision feedback handling in skill editing workflow
- Import ordering improvements for better code organization

### Removed

- Legacy signature classes `UnderstandTaskForSkillLegacy` and `PlanSkillStructureLegacy` from `workflow/signatures.py`
- Legacy comment block from workflow/signatures.py
- Duplicate utility functions from `workflow/modules.py` and `agent/modules.py` (now centralized in `common/utils.py`)
- Unused imports: `gather_context` from agent/agent.py

### Fixed

- Hardcoded empty strings in evolution metadata replaced with proper values
- TODO comments for `revision_feedback` incorporation addressed
- Linting issues with import ordering in modified files
- Model naming and temperature configuration issues ([7a36e76](https://github.com/Qredence/skill-fleet/commit/7a36e76))

---

## [0.1.1] - 2026-01-09

### Fixed

- Capability serialization now correctly handles lists of Pydantic models ([d5f8890](https://github.com/Qredence/skill-fleet/commit/d5f8890))
- Dependency validation properly handles `DependencyRef` objects in `TaxonomySkillCreator._validate_plan` ([d5f8890](https://github.com/Qredence/skill-fleet/commit/d5f8890))
- Added `aforward` methods to all DSPy modules to support async execution via `acall` ([d5f8890](https://github.com/Qredence/skill-fleet/commit/d5f8890))
- Fixed `dspy.context` calls to fallback to `dspy.settings.lm` when no specific LM is provided ([d5f8890](https://github.com/Qredence/skill-fleet/commit/d5f8890))
- Corrected typo 'fbr' in workflow modules that prevented test collection ([d5f8890](https://github.com/Qredence/skill-fleet/commit/d5f8890))

### Changed

- Renamed project from "skills-fleet" to "skill-fleet" across all documentation ([e888e9b](https://github.com/Qredence/skill-fleet/commit/e888e9b))
- Updated `.gitignore` and removed obsolete custom memory skill files ([c7b7134](https://github.com/Qredence/skill-fleet/commit/c7b7134))

## [0.1.0] - Initial Release

### Added

- Initial release of the Skills Fleet framework
- Taxonomy-based skill management system
- DSPy-powered skill creation workflow
- CLI interface for skill operations
- Memory block skills for agent memory management

[Unreleased]: https://github.com/Qredence/skill-fleet/compare/v0.3.6...HEAD
[0.3.6]: https://github.com/Qredence/skill-fleet/compare/5a743bf...v0.3.6
[0.3.5]: https://github.com/Qredence/skill-fleet/compare/8d571bf...5a743bf
[0.2.0]: https://github.com/Qredence/skill-fleet/compare/v0.1.2...8d571bf
[0.1.1]: https://github.com/Qredence/skill-fleet/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Qredence/skill-fleet/releases/tag/v0.1.0
