# skills-fleet – Agent Working Guide

This guide is for AI agents working on the **skills-fleet** codebase. It covers project structure, key concepts, development workflows, and important gotchas.

---

## 🎯 Project Purpose

The **Agentic Skills System** is a hierarchical, dynamic capability framework that enables AI agents to load skills on-demand. It addresses context bloat by organizing knowledge into a taxonomy where agents mount only the specific skills they need for a given task.

---

## 🏗️ Architecture Overview

### Core Components

1. **Skills Taxonomy** (`src/agentic_fleet/agentic_skills_system/skills/`)
   - 8-level hierarchical structure organizing agent capabilities
   - Each skill is a directory containing a `SKILL.md` file with YAML frontmatter
   - Skills are organized by domain (e.g., `general/`, `development/`, `business/`)

2. **Skill Creation Workflow** (`src/agentic_fleet/agentic_skills_system/workflow/`)
   - 6-step DSPy-based pipeline for generating new skills
   - Includes research, drafting, validation, and refinement stages
   - Supports Human-in-the-Loop (HITL) review at each stage

3. **CLI** (`src/agentic_fleet/agentic_skills_system/cli/`)
   - Primary interface for skill creation, validation, and migration
   - Built with Typer for a clean, typed command-line interface

4. **Validators** (`src/agentic_fleet/agentic_skills_system/validators/`)
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
# Clone and navigate to repo
cd skills-fleet

# Install Python dependencies
uv sync --group dev

# Install TUI dependencies (optional)
bun install

# Set up environment variables
echo 'GOOGLE_API_KEY="your_key_here"' > .env
```

### Creating a New Skill

```bash
# Interactive creation (recommended)
uv run skills-fleet create-skill --task "Create a skill for Docker best practices"

# Auto-approve mode (skips HITL review)
uv run skills-fleet create-skill --task "Create a skill for Docker best practices" --auto-approve
```

**The 6-step workflow:**
1. **Research**: Gather information about the skill topic
2. **Draft**: Generate initial skill content
3. **Validate**: Check format and compliance
4. **Refine**: Improve based on validation feedback
5. **Review**: Human-in-the-Loop approval (unless `--auto-approve`)
6. **Save**: Write to taxonomy

### Validating Skills

```bash
# Validate a specific skill directory
uv run skills-fleet validate-skill src/agentic_fleet/agentic_skills_system/skills/general/testing

# Migrate all skills to agentskills.io format
uv run skills-fleet migrate

# Preview migration without writing changes
uv run skills-fleet migrate --dry-run
```

### Generating XML for Agents

```bash
# Print XML to console
uv run skills-fleet generate-xml

# Save to file for agent prompt injection
uv run skills-fleet generate-xml -o available_skills.xml
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
uv run pytest --cov=src/agentic_fleet

# Linting and formatting
uv run ruff check .
uv run ruff format .
```

---

## 📂 Key Files & Directories

### Python Source

```
src/agentic_fleet/
├── agentic_skills_system/
│   ├── cli/
│   │   ├── main.py              # CLI entry point
│   │   ├── create_skill.py      # Skill creation command
│   │   ├── migrate.py           # Migration command
│   │   └── generate_xml.py      # XML generation command
│   ├── skills/                  # Skills taxonomy storage
│   │   ├── general/             # General-purpose skills
│   │   ├── development/         # Development skills
│   │   └── [other domains]/
│   ├── taxonomy/
│   │   ├── manager.py           # Taxonomy management
│   │   └── schema.py            # Taxonomy schema definitions
│   ├── workflow/
│   │   ├── skill_creator.py     # Main workflow orchestrator
│   │   └── signatures/          # DSPy signatures for each step
│   └── validators/
│       ├── skill_validator.py   # Core validation logic
│       └── frontmatter.py       # YAML frontmatter validation
├── llm/
│   ├── config.yaml              # LLM provider configuration
│   └── client.py                # LLM client wrapper
└── config.yaml                  # Global configuration
```

### Documentation

```
docs/
├── overview.md                  # System architecture
├── skill-creator-guide.md       # Detailed skill creation guide
├── agentskills-compliance.md    # agentskills.io specification guide
└── architecture/
    └── skill-creation-workflow.md
```

### Configuration

- **`pyproject.toml`**: Python package metadata, dependencies, entry points
- **`.env`**: Environment variables (API keys, configuration)
- **`src/agentic_fleet/config.yaml`**: LLM configuration (model selection, parameters)

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
uv run skills-fleet migrate --dry-run

# Step 2: Review output carefully

# Step 3: Apply changes
uv run skills-fleet migrate
```

### 5. Validation Before Committing

**ALWAYS** validate skills before creating a commit:
```bash
# Validate a specific skill
uv run skills-fleet validate-skill path/to/skill

# Generate XML to ensure all skills are discoverable
uv run skills-fleet generate-xml
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

# Optional
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

1. Create command file in `src/agentic_fleet/agentic_skills_system/cli/`
2. Define command using Typer
3. Register in `main.py`
4. Add tests in `tests/cli/`
5. Update CLI documentation

### Modifying the Skill Creation Workflow

1. Update DSPy signatures in `workflow/signatures/`
2. Modify workflow logic in `workflow/skill_creator.py`
3. Test with `uv run skills-fleet create-skill --task "Test task"`
4. Validate output format and quality

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
# Create skill
uv run skills-fleet create-skill --task "Your task description"

# Validate skill
uv run skills-fleet validate-skill path/to/skill

# Migrate to agentskills.io format
uv run skills-fleet migrate --dry-run
uv run skills-fleet migrate

# Generate XML
uv run skills-fleet generate-xml -o skills.xml

# Run tests
uv run pytest

# Lint/format
uv run ruff check .
uv run ruff format .
```

### Useful Paths

- Skills: `src/agentic_fleet/agentic_skills_system/skills/`
- CLI: `src/agentic_fleet/agentic_skills_system/cli/`
- Tests: `tests/`
- Docs: `docs/`
- Config: `src/agentic_fleet/config.yaml`

---

## 📚 Further Reading

- [agentskills.io Compliance Guide](docs/agentskills-compliance.md) - Complete specification
- [Skill Creator Guide](docs/skill-creator-guide.md) - Detailed creation workflow
- [Architecture Overview](docs/overview.md) - System design and concepts
- [CLI Reference](docs/cli-reference.md) - Full command documentation

---

## 💡 Tips for AI Agents

1. **Always read `SKILL.md` files** to understand skill format before creating new ones
2. **Use migration tools** when updating skill format - don't manually edit all files
3. **Validate early and often** - catch compliance issues before they spread
4. **Follow existing patterns** - check similar skills for structure and style
5. **Test your changes** - run pytest and validate-skill before considering work complete
6. **Document assumptions** - if you make decisions, explain them in commit messages
7. **Use dry-run mode** - preview changes before applying them to avoid mistakes

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

### "Tests failing after changes"
- Run `uv run pytest -v` for verbose output
- Check if validators need updating
- Verify skill format compliance

---

**Last Updated**: 2026-01-07
**Maintainer**: skills-fleet team
