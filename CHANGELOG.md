# Changelog

All notable changes to this project will be documented in this file.

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

## [Unreleased]

### Added

- **Interactive Chat CLI with Auto-Save** (January 12, 2026)
  - Interactive chat interface for guided skill creation via `uv run python -m skill_fleet.cli.app chat`
  - Full Phase 1, 2, and 3 HITL (Human-in-the-Loop) support in chat CLI
    - Phase 1: Clarification questions and confirmation dialogs (yellow/cyan panels)
    - Phase 2: Content preview with highlights (blue panel)
    - Phase 3: Validation reports with pass/fail indicators (green/red panels)
  - Automatic skill persistence to taxonomy directory after completion
  - `_save_skill_to_taxonomy()` function integrates with `TaxonomyManager.register_skill()`
  - Skills automatically saved to disk with proper directory structure:
    - `skills/{taxonomy_path}/SKILL.md` (with YAML frontmatter)
    - `skills/{taxonomy_path}/metadata.json` (extended metadata)
    - Subdirectories: examples/, capabilities/, tests/, resources/, etc.
  - Improved error handling in CLI client
    - Specific 404 handling for lost jobs (server restarts)
    - Helpful error messages for connection issues
    - Better exception display (type name, message)
  - Server mode options:
    - Production mode (default): Stable, no auto-reload
    - Development mode (`--reload`): Auto-reload with warnings
  - Display saved skill path on completion: `📁 Skill saved to: {path}`
- **FastAPI v2 server** with auto-discovery of DSPy programs/modules and routerized endpoints for skills, taxonomy, validation, chat, and HITL polling/response. Includes CORS defaults, `/health` probe, and shared DSPy configuration at startup.
- **Modular Typer CLI** rebuilt around `skill_fleet.cli.app` with dedicated commands for `serve`, `chat`, `create`, `validate`, `migrate`, `generate-xml`, `optimize`, `analytics`, and `onboard`, backed by a new HTTP client for HITL polling and API calls.
- **Expanded technical skill library** adding FastAPI backend architecture, DSPy framework usage, Python async/decorators/core syntax, pytest testing, code quality analysis, Docker containerization, design patterns, and concurrency skills under `skills/technical_skills/`.
- **Documentation updates** including refreshed README (Skill Fleet branding, setup, env vars, and CLI examples) and new implementation/review plan documents under `docs/plans/`.
- **Restructured documentation tree** with intro/getting-started/concepts folders + new guides (`docs/intro/introduction.md`, `docs/getting-started/index.md`, `docs/concepts/concept-guide.md`, `docs/concepts/developer-reference.md`) and updated cross-links from README, AGENTS.md, CLI/API references, and skill-creation guidelines to eliminate legacy quick-start pages.

### Changed

- CLI help and examples now use the new `skill-fleet` Typer entrypoint (`uv run python -m skill_fleet.cli.app ...`) instead of the removed single-file CLI.
- API bootstrapping centralizes DSPy configuration and exposes v2 endpoints, replacing the previous monolithic application wiring.
- Dependency versions for LLM stack and TUI stack bumped in README and lockfiles to reflect current environment.

### Removed

- Legacy CLI entrypoints (`src/skill_fleet/cli/main.py`, `interactive_typer.py`) and the old conversational reward pipeline were removed in favor of the new API + modular CLI flow.
- Outdated planning documents under `plans/` were retired/archived to reduce noise and align with the new workflow documentation.

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

[Unreleased]: https://github.com/Qredence/skill-fleet/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/Qredence/skill-fleet/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/Qredence/skill-fleet/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Qredence/skill-fleet/releases/tag/v0.1.0
