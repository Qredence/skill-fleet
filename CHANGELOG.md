# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

[0.1.1]: https://github.com/Qredence/skill-fleet/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Qredence/skill-fleet/releases/tag/v0.1.0
