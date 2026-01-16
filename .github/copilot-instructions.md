# Copilot Instructions for skill-fleet

## Project Overview

**skill-fleet** is a hierarchical, dynamic capability framework for AI agents built on DSPy. The system enables agents to load skills on-demand through a just-in-time capability model, optimizing performance and reducing context bloat through an 8-level taxonomy structure with agentskills.io compliance.

### Key Facts

- **Language**: Python 3.12+ (primary), TypeScript/React (optional TUI)
- **Project Type**: AI/LLM framework with CLI, API, and TUI
- **Size**: ~56 Python files, ~63 skill directories, 145 tests
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (Python), bun (optional, for TUI)
- **LLM Framework**: DSPy with Google Gemini 3 Flash as default model
- **Testing**: pytest with asyncio support
- **Linting**: ruff (replaces flake8, black, isort)

## Current State (2026-01-16)

**Taxonomy v0.2 migration completed** - simplified 2-level taxonomy with canonical path resolution and alias support.

- **API-first execution**: FastAPI is the canonical surface for running DSPy workflows; the CLI (`skill-fleet create/chat/...`) is a thin API client.
- **Draft-first persistence**: jobs write drafts under `skills/_drafts/<job_id>/...`; promotion into the taxonomy is explicit via `uv run skill-fleet promote <job_id>` or the API.
- **Evaluation**: Calibration with Obra/superpowers standards implemented.
- **Known Issues**:
  - Job state is in-memory (loss on restart).
  - Rich `MarkupError` with certain special characters in CLI output.

## Build & Validation Workflow

### Prerequisites

- **uv package manager**: Must be pre-installed (see environment setup or admin configuration)
- **Python 3.12+**: Required for the project

### Initial Setup (First Time Only)

```bash
# Install all dependencies including dev tools
uv sync --group dev

# Verify installation
uv run skill-fleet --help
```

**Critical**: Always use `uv run` prefix for all Python commands. This ensures the virtual environment is activated correctly.

### Essential Commands (In Order)

**1. Install Dependencies**

```bash
uv sync --group dev
```

- Takes ~30-60 seconds on first run
- Downloads ~177 packages including DSPy, LiteLLM, MLflow, FastAPI
- Creates `.venv/` directory automatically
- Run this after pulling changes that modify `pyproject.toml` or `uv.lock`

**2. Run Linting (Fast, ~2-5 seconds)**

```bash
uv run ruff check .
```

- Always run BEFORE making commits
- Auto-fix issues with: `uv run ruff check --fix .`
- Format code with: `uv run ruff format .`
- Configured in `pyproject.toml`
- Excludes `skills/**` directory

**3. Run Tests (~10-30 seconds)**

```bash
# Full test suite (145 tests)
uv run pytest

# Specific test file
uv run pytest tests/unit/test_skill_validator.py

# With verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=src/skill_fleet
```

- Tests are in `tests/unit/` and `tests/integration/`
- Some integration tests require API keys (GOOGLE_API_KEY)
- Expected: 143 passed, 2 failed integration tests (require real LLM) without keys

**4. Validate Skills**

```bash
# Validate a specific skill
uv run skill-fleet validate skills/general/testing

# Migrate skills to agentskills.io format (dry-run first!)
uv run skill-fleet migrate --dry-run
uv run skill-fleet migrate

# Generate XML catalog
uv run skill-fleet generate-xml -o available_skills.xml
```

### Build Verification Script

The repository includes a `verify_migration.sh` script that runs a comprehensive check:

```bash
./scripts/verify_migration.sh
```

This verifies: old imports, build success, test pass, CLI entrypoint, directory structure.

## Project Architecture

### Directory Structure

```
skill-fleet/
├── .github/                    # GitHub workflows (Junie CI) & Copilot Instructions
├── src/skill_fleet/           # Main Python package (56 files)
│   ├── agent/                 # Conversational agent for interactive skill creation
│   ├── analytics/             # Usage tracking and recommendations
│   ├── api/                   # FastAPI server endpoints
│   ├── cli/                   # CLI commands (Typer-based)
│   │   ├── main.py           # Main CLI entry point
│   │   ├── interactive_typer.py
│   │   └── onboarding_cli.py
│   ├── common/                # Shared utilities (safe_json_loads, etc.)
│   ├── config/                # Packaged config defaults
│   ├── core/                  # Unified core architecture (DSPy, models, tools)
│   ├── llm/                   # LLM configuration
│   │   ├── dspy_config.py    # Centralized DSPy setup (IMPORTANT)
│   │   └── fleet_config.py   # LLM provider configs
│   ├── onboarding/            # User onboarding workflows
│   ├── taxonomy/              # Skill taxonomy management
│   ├── ui/                    # TypeScript/React TUI (optional)
│   ├── validators/            # agentskills.io compliance validators
│   │   └── skill_validator.py # Core validation logic
│   └── workflow/              # DEPRECATED: Consolidated into core/
├── skills/                    # Skills taxonomy (63 directories)
│   └── [taxonomy hierarchy]   # general/, development/, business/, etc.
├── tests/                     # Test suite (145 tests)
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests (require API keys)
├── config/                    # Configuration files
│   ├── config.yaml           # LLM model settings (Gemini 3 Flash)
│   ├── profiles/             # Bootstrap profiles
│   └── templates/            # Skill templates
├── docs/                      # Documentation
├── pyproject.toml            # Python metadata, dependencies, build config
├── uv.lock                   # Locked dependencies (auto-generated)
└── .env.example              # Environment variable template
```

### Key Configuration Files

**pyproject.toml**

- Project metadata
- Dependencies including DSPy, LiteLLM, FastAPI
- Dev dependencies: pytest, ruff, httpx
- Entry point: `skill-fleet` CLI
- pytest configuration
- ruff linting rules

**config/config.yaml**

- Default LLM: `gemini/gemini-3-flash-preview`
- Task-specific model configurations
- Temperature and reasoning effort per task type
- Requires: `GOOGLE_API_KEY` environment variable

**.gitignore**

- Excludes: `.venv/`, `.dspy_cache/`, `__pycache__/`, `node_modules/`
- Build artifacts: `.pytest_cache/`, `.ruff_cache/`
- Environment files: `.env`, `.env.*` (but keeps `.env.example`)

## Critical Concepts

### agentskills.io Compliance

Every `SKILL.md` file MUST have YAML frontmatter at the top:

```markdown
---
name: skill-name-in-kebab-case
description: A concise description (1-2 sentences)
---

# Skill Title

[Content...]
```

**Rules:**

1. Frontmatter must be first (no content before `---`)
2. `name` must be kebab-case (lowercase with hyphens)
3. `description` is required
4. No spaces, underscores, or CamelCase in names

**Validation:**

```bash
uv run skill-fleet validate path/to/skill
```

### DSPy Configuration

The system uses centralized DSPy configuration via `src/skill_fleet/llm/dspy_config.py`:

```python
from skill_fleet.llm.dspy_config import configure_dspy, get_task_lm

# Configure once at startup (CLI does this automatically)
lm = configure_dspy(default_task="skill_understand")

# Get task-specific LM
edit_lm = get_task_lm("skill_edit")
```

**Important**: CLI auto-configures DSPy on startup. Library users must call `configure_dspy()` explicitly.

**Environment Variables:**

- `DSPY_CACHEDIR`: Cache location (default: `.dspy_cache/`)
- `DSPY_TEMPERATURE`: Global temperature override

### 6-Step Skill Creation Workflow

1. **Understand**: Analyze task, determine taxonomy placement (high creativity)
2. **Plan**: Generate metadata, dependencies, capabilities (medium creativity)
3. **Initialize**: Create directory structure (minimal creativity)
4. **Edit**: Generate SKILL.md content with frontmatter (high creativity)
5. **Package**: Validate and bundle (medium creativity)
6. **Validate**: Check agentskills.io compliance (minimal creativity)

Each step uses a different DSPy module with task-specific LM configuration.

## Common Development Tasks

### Adding a New CLI Command

1. Create command file in `src/skill_fleet/cli/`
2. Define command using Typer decorators
3. Register in `src/skill_fleet/cli/app.py`
4. Add tests in `tests/cli/` (if directory exists, else `tests/`)
5. Update `docs/cli-reference.md`
6. Run: `uv run skill-fleet [new-command] --help` to verify

### Modifying Validation Rules

1. Edit `src/skill_fleet/validators/skill_validator.py`
2. Add tests in `tests/unit/test_skill_validator.py`
3. Run: `uv run pytest tests/unit/test_skill_validator.py -v`
4. Test migration: `uv run skill-fleet migrate --dry-run`
5. Update `docs/agentskills-compliance.md`

### Working with Skills

1. **Never manually edit all skills** - use migration tools
2. **Always validate** after manual edits: `uv run skill-fleet validate path/to/skill`
3. **Preview changes** with `--dry-run` flag
4. **Regenerate XML** after skill changes: `uv run skill-fleet generate-xml -o available_skills.xml`
5. **Use Kebab-Case**: Always use `my-skill-name`, never `my_skill` or `MySkill`.

## Known Issues & Gotchas

### 1. Missing API Key Errors

**Symptom**: "API key not found" or integration tests fail
**Solution**: Create `.env` file with `GOOGLE_API_KEY="your_key_here"`

### 2. Import Errors After Dependency Changes

**Symptom**: `ModuleNotFoundError` after pulling changes
**Solution**: Run `uv sync --group dev` to reinstall dependencies

### 3. YAML Frontmatter Position

**Common Mistake**: Adding frontmatter after content
**Correct**: Frontmatter must be the first thing in `SKILL.md`

```markdown
---
name: my-skill
description: Description here
---

# My Skill
```

### 4. Skill Name Format

**Wrong**: `My Skill`, `my_skill`, `MySkill`
**Correct**: `my-skill` (kebab-case only)

### 5. API vs CLI

**Note**: The CLI is a wrapper around the API logic in `src/skill_fleet/api` and `src/skill_fleet/core`.
**Best Practice**: When adding features, implement them in `core` or `api` first, then expose via CLI.

### 6. Ruff Linting Noise

**Issue**: Ruff reports errors in `skills/` directory
**Solution**: Skills are excluded in `pyproject.toml` line 56. If errors appear, ignore them or run: `uv run ruff check src/ tests/`

### 7. DSPy Cache Issues

**Symptom**: Stale LLM responses or errors about cache
**Solution**: Clear cache with `rm -rf .dspy_cache/` or `rm -rf ~/.cache/dspy/`

### 8. Network/Firewall Limitations

**Symptom**: DNS resolution failures, connection timeouts during setup or tests
**Blocked Domains**:

- `astral.sh` - Blocks curl-based uv installation (uv must be pre-installed by environment/admin)
- `openaipublic.blob.core.windows.net` - Blocks tiktoken encoding downloads during pytest

**Workarounds**:

- **For uv availability**: uv must be pre-installed in the environment by admins before the firewall is enabled
- **For tiktoken errors**: These are typically in integration tests that also require `GOOGLE_API_KEY`. Expected: 2 integration tests may fail with network errors
- **In CI/CD**: Configure Actions setup steps before firewall is enabled, or add domains to the custom allowlist in repository's Copilot settings (admin only)

## CI/CD Pipeline

### GitHub Workflow

- **File**: `.github/workflows/junie.yml`
- **Trigger**: Manual workflow dispatch only (not on push/PR)
- **Purpose**: Junie AI agent integration
- **No automatic CI**: Tests and linting must be run locally before committing

### Pre-Commit Checklist

Before every commit, run:

```bash
# 1. Lint and fix
uv run ruff check --fix .
uv run ruff format .

# 2. Run tests
uv run pytest

# 3. Validate skills (if you modified any)
uv run skill-fleet validate path/to/modified/skill

# 4. Check for common issues
git status  # Ensure no unexpected files (.venv/, .dspy_cache/, etc.)
```

## Testing Strategy

### Unit Tests (tests/unit/)

- Fast, no external dependencies
- Mock LLMs and file I/O
- Test individual modules and functions
- Run specific tests: `uv run pytest tests/unit/test_validators.py`

### Integration Tests (tests/integration/)

- Require `GOOGLE_API_KEY`
- Test full workflows with real LLMs
- May be slow (30-60 seconds)
- Run with: `uv run pytest tests/integration/ -v`

### Test Categories

- **Validators**: `tests/unit/test_skill_validator.py`
- **CLI**: Tests embedded in `tests/test_api.py`, `tests/test_onboarding.py`
- **Workflow**: `tests/unit/test_workflow_modules.py`, `tests/integration/test_workflow_integration.py`
- **Streaming**: `tests/test_streaming.py`
- **Analytics**: `tests/test_analytics.py`

### Running Focused Tests

```bash
# Single test file
uv run pytest tests/unit/test_skill_validator.py

# Single test function
uv run pytest tests/unit/test_skill_validator.py::test_validate_directory_skill

# All unit tests
uv run pytest tests/unit/

# Skip slow tests
uv run pytest -m "not slow"
```

## Environment Setup

### Required Environment Variables

```bash
GOOGLE_API_KEY="your_key_here"  # Required for skill generation
```

### Optional Environment Variables

```bash
DEEPINFRA_API_KEY="..."         # Alternative LLM provider
LITELLM_API_KEY="..."           # LiteLLM proxy
LANGFUSE_SECRET_KEY="..."       # Telemetry
REDIS_HOST="localhost"          # State management
DSPY_CACHEDIR="/path/to/cache"  # Override cache location
DSPY_TEMPERATURE="0.7"          # Global temperature override
LOG_LEVEL="DEBUG"               # Logging verbosity
```

Create a `.env` file in the repository root (see `.env.example` for template).

## Common Command Patterns

### Quick Reference

```bash
# Setup
uv sync --group dev

# Development cycle
uv run ruff check --fix .       # Lint and fix
uv run ruff format .             # Format code
uv run pytest                    # Run tests
uv run pytest -v                 # Verbose test output

# CLI usage
uv run skill-fleet --help        # Show all commands
uv run skill-fleet create "Skill description"
uv run skill-fleet validate path/to/skill
uv run skill-fleet migrate --dry-run
uv run skill-fleet generate-xml -o available_skills.xml

# Debugging
uv run python -c "from skill_fleet.cli import cli_entrypoint"  # Test imports
uv run skill-fleet --help        # Test CLI entrypoint
```

## Tips for Efficient Work

1. **Trust These Instructions**: The information here is verified and current. Only search documentation if something is unclear or appears incorrect.

2. **Use `uv run` Prefix**: Always prefix Python commands with `uv run` to ensure correct environment activation.

3. **Lint Before Commit**: Run `uv run ruff check --fix .` before committing to avoid CI failures.

4. **Test Locally**: No automatic CI exists. Run tests locally before pushing.

5. **Preview Changes**: Use `--dry-run` flags on migration and validation commands.

6. **Check Git Status**: Before committing, ensure `.venv/`, `.dspy_cache/`, and other build artifacts aren't staged.

7. **Read AGENTS.md**: For deeper technical details, see `AGENTS.md` in the root.

8. **Validate Skills**: After editing skills, always run validation: `uv run skill-fleet validate path/to/skill`

9. **Use Common Utilities**: Import from `skill_fleet.common.utils` for safe JSON parsing and utility functions.

10. **Follow Existing Patterns**: Check similar files/tests for structure and style conventions before creating new ones.

## Documentation Reference

- **README.md**: User-facing overview, features, setup
- **AGENTS.md**: AI agent working guide (technical deep dive)
- **docs/development/CONTRIBUTING.md**: Contributing guidelines, code style
- **docs/quick-start.md**: Step-by-step user onboarding
- **docs/cli-reference.md**: Complete CLI command reference
- **docs/agentskills-compliance.md**: agentskills.io specification details
- **docs/skill-creator-guide.md**: Detailed 6-step workflow explanation
- **docs/overview.md**: System architecture and design decisions

## Last Updated

2026-01-16
