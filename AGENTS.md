# skill-fleet – Agent Working Guide

This guide is for AI agents working on the **skill-fleet** codebase. It covers project structure, key concepts, development workflows, and important gotchas.

---

## 🎯 Project Purpose

The **Agentic Skills System** is a hierarchical, dynamic capability framework that enables AI agents to load skills on-demand. It addresses context bloat by organizing knowledge into a taxonomy where agents mount only the specific skills they need for a given task.

---

## 🏗️ Architecture Overview

### Core Components

1. **Skills Taxonomy** (`skills/`)
   - 8-level hierarchical structure organizing agent capabilities
   - Each skill is a directory containing a `SKILL.md` file with YAML frontmatter
   - Skills are organized by domain (e.g., `general/`, `development/`, `business/`)

2. **Skill Creation (API + DSPy)** (`src/skill_fleet/api/`, `src/skill_fleet/core/`)
   - FastAPI background jobs + HITL prompt loop (create job → prompt → response)
   - DSPy program: `src/skill_fleet/core/programs/skill_creator.py` (3-phase orchestrator)
   - Authoring templates:
     - `config/templates/SKILL_md_template.md` (SKILL.md structure + frontmatter rules)
     - `config/templates/metadata_template.json` (metadata.json shape + fields)
   - Note: `src/skill_fleet/workflow/` still exists (used by onboarding/optimizer); API-backed `create`/`chat` uses the `core/` program.

3. **CLI** (`src/skill_fleet/cli/`)
   - Primary interface for skill creation, validation, and migration
   - Built with Typer for a clean, typed command-line interface

4. **Validators** (`src/skill_fleet/validators/`)
   - Ensures skills meet quality and compliance standards
   - Validates YAML frontmatter, content structure, and agentskills.io compliance

---

## 📋 agentskills.io Compliance

### What It Means

**agentskills.io** is a specification for standardizing agent skills to enable:
- **Discoverability**: Agents can enumerate available skills via XML
- **Interoperability**: Skills can be shared across different agent frameworks
- **Metadata**: Standardized frontmatter enables automated indexing and searching

### Required Format

Every `SKILL.md` file MUST include YAML frontmatter:

```yaml
---
name: skill-name-in-kebab-case
description: A concise description of what this skill provides (1-2 sentences)
---
```

### Key Requirements

1. **`name`**: Must be in kebab-case (lowercase with hyphens)
2. **`description`**: Brief, clear explanation of the skill's purpose
3. **Frontmatter**: Must be at the very top of the file (no content before `---`)

### Example

```markdown
---
name: python-async-programming
description: Comprehensive guide to Python's asyncio framework, including coroutines, event loops, and concurrent programming patterns.
---

# Python Async Programming

[Skill content follows...]
```

---

## 🛠️ Development Workflow

### Setting Up

```bash
# From repo root

# Install Python dependencies (including dev tools)
uv sync --group dev

# Install TUI dependencies (optional)
bun install

# Configure environment
cp .env.example .env
# then edit .env (at minimum: GOOGLE_API_KEY)
```

### Creating a New Skill

```bash
# Start the API server (required for API-backed commands like create/chat/list)
uv run skill-fleet serve
# Dev mode with auto-reload
uv run skill-fleet serve --reload

# Create a new skill (HITL by default)
uv run skill-fleet create "Create a skill for Docker best practices"

# Auto-approve mode (skips interactive prompts)
uv run skill-fleet create "Create a skill for Docker best practices" --auto-approve

# Interactive chat mode
uv run skill-fleet chat
uv run skill-fleet chat "Create a skill for Docker best practices"
uv run skill-fleet chat --auto-approve
```

**API-backed guided flow (create/chat):**
1. **Clarify (optional)**: Ask targeted questions when the task is ambiguous
2. **Confirm**: Show an understanding summary + proposed taxonomy path (proceed/revise/cancel)
3. **Preview**: Show a draft preview (proceed/refine/cancel)
4. **Validate**: Show validation report (proceed/refine/cancel)
5. **Save**: Persist to `skills/` (auto-save when the job completes)

### Creating a Revised Skill

```bash
# Create a revised version with specific feedback
# (Implemented via the API-backed workflow; use chat to iterate with HITL)
uv run skill-fleet chat
```

Use chat/HITL prompts to provide specific guidance for improving an existing skill.

### DSPy Configuration

The system uses centralized DSPy configuration for consistent LLM settings across all operations:

```python
from skill_fleet.llm.dspy_config import configure_dspy, get_task_lm

# Configure once at startup (the API server does this automatically)
lm = configure_dspy(default_task="skill_understand")

# Get task-specific LM when needed
edit_lm = get_task_lm("skill_edit")
```

**Environment Variables:**
- `DSPY_CACHEDIR`: Override DSPy cache directory (default: `.dspy_cache`)
- `DSPY_TEMPERATURE`: Global temperature override for all tasks

**Task-Specific LMs:**
Different workflow phases use different LM configurations:
- `skill_understand`: Task analysis (high temperature for creativity)
- `skill_plan`: Structure planning (medium temperature)
- `skill_initialize`: Directory initialization (minimal temperature)
- `skill_edit`: Content generation (medium temperature)
- `skill_package`: Validation and packaging (low temperature)
- `skill_validate`: Compliance checking (minimal temperature)

### Validating Skills

```bash
# Validate a specific skill directory
uv run skill-fleet validate skills/general/testing

# Migrate all skills to agentskills.io format
uv run skill-fleet migrate

# Preview migration without writing changes
uv run skill-fleet migrate --dry-run
```

### Generating XML for Agents

```bash
# Print XML to console
uv run skill-fleet generate-xml

# Save to file for agent prompt injection
uv run skill-fleet generate-xml -o available_skills.xml
```

The generated XML follows the agentskills.io format:
```xml
<available_skills>
  <skill>
    <name>python-async-programming</name>
    <description>Comprehensive guide to Python's asyncio framework...</description>
  </skill>
  <!-- More skills... -->
</available_skills>
```

### Testing

```bash
# Run full test suite
uv run pytest

# Run specific test file
uv run pytest tests/test_validators.py

# Run with coverage
uv run pytest --cov=src/skill_fleet

# Linting and formatting
uv run ruff check .
uv run ruff format .
```

---

## 📂 Key Files & Directories

### Python Source

```
src/skill_fleet/
├── agent/
│   └── agent.py                 # Conversational agent for skill creation
├── cli/
│   ├── __init__.py              # Exposes cli_entrypoint()
│   └── app.py                   # Typer app + command registration
├── common/
│   └── utils.py                 # Shared utility functions
├── core/
│   ├── programs/
│   │   └── skill_creator.py      # API-backed 3-phase DSPy program + HITL hooks
│   ├── modules/                 # Phase modules + HITL utilities
│   ├── signatures/              # DSPy signatures for each phase
│   └── config/                  # Pydantic models + core config
├── llm/
│   ├── dspy_config.py           # Centralized DSPy configuration
│   └── fleet_config.py          # LLM provider configuration
├── taxonomy/
│   └── manager.py               # Taxonomy management
├── validators/
│   └── skill_validator.py       # Core validation logic
└── workflow/
    ├── creator.py               # Main workflow orchestrator
    ├── modules.py               # DSPy modules
    ├── programs.py              # DSPy programs
    └── signatures.py            # DSPy signatures for each step
```

### Documentation

```
docs/
├── overview.md                     # System architecture
├── skill-creator-guide.md          # Detailed skill creation guide
├── agentskills-compliance.md       # agentskills.io specification guide
├── cli-reference.md                # Complete CLI reference
├── api-reference.md                # Python API documentation
├── development/
│   ├── CONTRIBUTING.md             # Contributing guidelines
│   └── ARCHITECTURE_DECISIONS.md   # Architecture decision records
└── architecture/
    └── skill-creation-workflow.md
```

### Configuration

- **`pyproject.toml`**: Python package metadata, dependencies, entry points
- **`.env`**: Environment variables (API keys, configuration)
- **`config/config.yaml`**: LLM configuration (model selection, parameters)
- **`src/skill_fleet/config/`**: Packaged defaults for wheels (kept in sync with `config/`)

---

## ⚠️ Common Footguns & Best Practices

### 1. YAML Frontmatter

**PROBLEM**: Frontmatter not at the top of the file
```markdown
# My Skill

---
name: my-skill
---

[Content...]
```

**SOLUTION**: Frontmatter MUST be the first thing in the file
```markdown
---
name: my-skill
description: Description here
---

# My Skill

[Content...]
```

### 2. Skill Name Format

**PROBLEM**: Incorrect name format
```yaml
name: My Skill        # ❌ Contains spaces
name: my_skill        # ❌ Uses underscores
name: MySkill         # ❌ CamelCase
```

**SOLUTION**: Use kebab-case
```yaml
name: my-skill        # ✅ Correct format
```

### 3. Missing Description

**PROBLEM**: No description in frontmatter
```yaml
---
name: my-skill
---
```

**SOLUTION**: Always include a description
```yaml
---
name: my-skill
description: This skill teaches developers how to use Docker effectively.
---
```

### 4. Migration Workflow

**ALWAYS** run with `--dry-run` first to preview changes:
```bash
# Step 1: Preview
uv run skill-fleet migrate --dry-run

# Step 2: Review output carefully

# Step 3: Apply changes
uv run skill-fleet migrate
```

### 5. Validation Before Committing

**ALWAYS** validate skills before creating a commit:
```bash
# Validate a specific skill
uv run skill-fleet validate path/to/skill

# Generate XML to ensure all skills are discoverable
uv run skill-fleet generate-xml
```

If validation fails, fix issues before committing.

### 6. Testing After Changes

**ALWAYS** run tests after modifying core code:
```bash
uv run pytest

# If tests fail, fix them before committing
```

---

## 🔧 Toolchain

### Required

- **Python**: 3.12+ (managed via `uv`)
- **uv**: Fast Python package manager
- **zsh**: Default shell

### Optional

- **bun**: For TUI development
- **zig**: Required for building OpenTUI components

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_key_here

# Optional (CLI)
SKILL_FLEET_API_URL=http://localhost:8000
SKILL_FLEET_USER_ID=default

# Optional (API)
SKILL_FLEET_SKILLS_ROOT=skills
SKILL_FLEET_CORS_ORIGINS=http://localhost:3000

# Optional (providers/observability)
DEEPINFRA_API_KEY=your_key_here
LITELLM_API_KEY=your_key_here
LANGFUSE_SECRET_KEY=your_key_here
REDIS_HOST=localhost
DSPY_CACHEDIR=/path/to/cache
DSPY_TEMPERATURE=0.7
```

---

## 📊 Common Development Tasks

### Adding a New CLI Command

1. Create command file in `src/skill_fleet/cli/`
2. Define command using Typer
3. Register in `src/skill_fleet/cli/app.py`
4. Add tests in `tests/cli/`
5. Update CLI documentation

### Modifying the Skill Creation Workflow

1. API-backed flow (create/chat): update `src/skill_fleet/core/` modules/signatures/programs
2. Template guidance: update `config/templates/SKILL_md_template.md` and/or `config/templates/metadata_template.json`
3. Run the API server, then test with `uv run skill-fleet create "Test task"`
4. Validate output format and quality (and run unit tests)

### Adding a New Validator

1. Create validator in `validators/`
2. Register in `skill_validator.py`
3. Add tests in `tests/validators/`
4. Update documentation

### Extending the Taxonomy

1. Add new category in `skills/`
2. Create `README.md` for the category
3. Add example skills
4. Update taxonomy schema if needed

---

## 🚀 Quick Reference

### Essential Commands

```bash
# CLI help
uv run skill-fleet --help

# Start API server (required for API-backed create/chat/list)
uv run skill-fleet serve

# Create a skill (HITL by default)
uv run skill-fleet create "Your task description"

# Validate skill
uv run skill-fleet validate skills/general/testing

# Migrate to agentskills.io format
uv run skill-fleet migrate --dry-run
uv run skill-fleet migrate

# Generate XML
uv run skill-fleet generate-xml -o skills.xml

# Run tests
uv run pytest

# Lint/format
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
```

### Useful Paths

- Skills: `skills/`
- CLI: `src/skill_fleet/cli/`
- Tests: `tests/`
- Docs: `docs/`
- Config: `config/config.yaml`

---

## 📚 Further Reading

### User Documentation
- [Getting Started](docs/getting-started/index.md) - Quick installation, CLI usage, validation, and templates
- [agentskills.io Compliance Guide](docs/agentskills-compliance.md) - Complete specification
- [Skill Creator Guide](docs/skill-creator-guide.md) - Detailed creation workflow
- [Architecture Overview](docs/overview.md) - System design and concepts
- [CLI Reference](docs/cli-reference.md) - Full command documentation
- [API Reference](docs/api-reference.md) - Python API documentation

### Developer Documentation
- [Contributing Guide](docs/development/CONTRIBUTING.md) - Development setup and workflows
- [Architecture Decisions](docs/development/ARCHITECTURE_DECISIONS.md) - Key architectural decisions and their rationale

---

## 💡 Tips for AI Agents

1. **Always read `SKILL.md` files** to understand skill format before creating new ones
2. **Use migration tools** when updating skill format - don't manually edit all files
3. **Validate early and often** - catch compliance issues before they spread
4. **Follow existing patterns** - check similar skills for structure and style
5. **Test your changes** - run `uv run pytest` and `uv run skill-fleet validate` before considering work complete
6. **Document assumptions** - if you make decisions, explain them in commit messages
7. **Use dry-run mode** - preview changes before applying them to avoid mistakes
8. **Use common utilities** - import from `skill_fleet.common.utils` for safe JSON/float conversion
9. **Understand DSPy configuration** - the API server calls `configure_dspy()`; local workflows should call it (or pass task-specific LMs) before running DSPy programs
10. **Follow templates** - keep new skills aligned with `config/templates/SKILL_md_template.md` and `config/templates/metadata_template.json`

---

## 🐛 Troubleshooting

### "YAML frontmatter not found"
- Ensure frontmatter is at the very top of the file
- Check that you have both opening and closing `---` delimiters

### "Invalid skill name format"
- Use kebab-case only (lowercase with hyphens)
- No spaces, underscores, or capital letters

### "DSPy cache issues"
- Clear cache: `rm -rf ~/.cache/dspy/`
- Or set custom cache dir: `export DSPY_CACHEDIR=/path/to/cache`

### "DSPy not configured"
- CLI automatically configures DSPy on startup
- For library use: call `configure_dspy()` before any DSPy operations
- Check `config/config.yaml` for LM settings
- Verify `GOOGLE_API_KEY` is set

### "Tests failing after changes"
- Run `uv run pytest -v` for verbose output
- Check if validators need updating
- Verify skill format compliance

---

**Last Updated**: 2026-01-12
**Maintainer**: skill-fleet team
