# CLI Reference

Complete command-line interface reference for the skill-fleet system.

> **Note (2026-01-13):** This document contains legacy command names from earlier
> iterations of the CLI. For the current Typer CLI (`skill-fleet create/chat/list/...`)
> see:
>
> - `docs/cli/commands.md`
> - `docs/cli/interactive-chat.md`
>
> You can always confirm the live command surface via: `uv run skill-fleet --help`.

## Overview

The `skill-fleet` CLI provides commands for creating, validating, migrating, and managing agent skills.

## Installation

```bash
# Install from project root
uv sync --group dev
```

## Global Options

All commands support these global options:

```bash
--help, -h        Show help message
--version         Show version information
```

## Commands

### create-skill

Create a new skill using the DSPy-powered 6-step workflow.

**Usage:**

```bash
uv run skill-fleet create-skill --task "TASK_DESCRIPTION" [OPTIONS]
```

**Required Arguments:**

- `--task TEXT` - Description of the skill to create

**Optional Arguments:**

- `--user-id TEXT` - ID of the user creating the skill (default: `default`)
- `--max-iterations INT` - Maximum feedback loops (default: `3`)
- `--auto-approve` - Skip HITL review and auto-approve if validation passes
- `--config PATH` - Path to fleet configuration YAML (default: `config/config.yaml`)
- `--skills-root PATH` - Path to taxonomy root (default: `skills`)
- `--json` - Output result as JSON

**Examples:**

```bash
# Basic skill creation with HITL review
uv run skill-fleet create-skill --task "Create a Python async programming skill"

# Auto-approve for CI/CD workflows
uv run skill-fleet create-skill --task "Create FastAPI integration skill" --auto-approve

# JSON output for programmatic use
uv run skill-fleet create-skill --task "Create data validation skill" --json

# Custom user context
uv run skill-fleet create-skill --task "Create testing utilities" --user-id developer_123
```

---

### validate-skill

Validate a skill directory against taxonomy standards and agentskills.io compliance.

**Usage:**

```bash
uv run skill-fleet validate-skill PATH [OPTIONS]
```

**Required Arguments:**

- `PATH` - Path to the skill directory to validate

**Optional Arguments:**

- `--json` - Output result as JSON
- `--strict` - Treat warnings as errors

**What is Validated:**

- Directory structure (metadata.json, SKILL.md, subdirectories)
- Metadata completeness and format
- YAML frontmatter compliance (agentskills.io)
- Dependencies validity
- Capability documentation
- Example files presence
- Resource files presence

**Examples:**

```bash
# Validate a single skill
uv run skill-fleet validate-skill skills/technical_skills/programming/languages/python/decorators

# JSON output
uv run skill-fleet validate-skill path/to/skill --json

# Strict mode (warnings = errors)
uv run skill-fleet validate-skill path/to/skill --strict
```

**Exit Codes:**

- `0` - Validation passed
- `1` - Validation failed (or warnings in strict mode)

---

### migrate

Migrate existing skills to agentskills.io-compliant format with YAML frontmatter.

**Usage:**

```bash
uv run skill-fleet migrate [OPTIONS]
```

**Optional Arguments:**

- `--skills-root PATH` - Skills taxonomy root (default: `skills`)
- `--dry-run` - Preview changes without writing to disk
- `--json` - Output result as JSON

**What it Does:**

1. Scans all skill directories with `metadata.json`
2. Generates kebab-case names from skill IDs
3. Extracts or generates descriptions
4. Creates YAML frontmatter
5. Prepends frontmatter to SKILL.md files
6. Updates metadata.json with name and description

**Safety Features:**

- Idempotent (safe to run multiple times)
- Skips already-compliant skills
- Preserves existing content
- Dry-run mode for preview

**Examples:**

```bash
# Migrate all skills
uv run skill-fleet migrate

# Preview changes without writing
uv run skill-fleet migrate --dry-run

# Custom skills directory
uv run skill-fleet migrate --skills-root /path/to/skills

# JSON output for automation
uv run skill-fleet migrate --json
```

**Exit Codes:**

- `0` - Migration successful (or all skills already compliant)
- `1` - One or more migrations failed

**Output:**

```
============================================================
Migrating skills to agentskills.io format
Skills root: /path/to/skills
============================================================

Migrated: technical_skills/programming/languages/python/decorators -> python-decorators
  - Added YAML frontmatter
  - Added name to metadata.json

Skipped: _core/reasoning -> core-reasoning
  - Frontmatter already present and valid

============================================================
Migration Summary:
  Total skills: 15
  Successful: 12
  Skipped (already compliant): 3
  Failed: 0
```

---

### generate-xml

Generate `<available_skills>` XML for agent prompt injection following agentskills.io standard.

**Usage:**

```bash
uv run skill-fleet generate-xml [OPTIONS]
```

**Optional Arguments:**

- `--skills-root PATH` - Skills taxonomy root (default: `skills`)
- `--output, -o PATH` - Output file (default: stdout)

**Output Format:**

```xml
<available_skills>
  <skill>
    <name>python-decorators</name>
    <description>Ability to design, implement, and apply higher-order functions...</description>
    <location>/path/to/skills/.../SKILL.md</location>
  </skill>
  <!-- more skills -->
</available_skills>
```

**Examples:**

```bash
# Print to stdout
uv run skill-fleet generate-xml

# Save to file
uv run skill-fleet generate-xml -o available_skills.xml

# Custom skills directory
uv run skill-fleet generate-xml --skills-root /path/to/skills

# Pipe to other tools
uv run skill-fleet generate-xml | xmllint --format -
```

**Use Cases:**

- Agent system prompt injection
- Skill catalog generation
- Documentation automation
- Integration with agentskills.io-compliant tools

---

### onboard

Interactive user onboarding to create personalized skill profiles.

**Usage:**

```bash
uv run skill-fleet onboard --user-id USER_ID [OPTIONS]
```

**Required Arguments:**

- `--user-id TEXT` - Unique user identifier

**Optional Arguments:**

- `--skills-root PATH` - Skills taxonomy root
- `--config PATH` - Path to configuration file

**Examples:**

```bash
# Start onboarding
uv run skill-fleet onboard --user-id developer_123

# With custom configuration
uv run skill-fleet onboard --user-id analyst_456 --config custom_config.yaml
```

---

### analytics

View usage analytics and statistics for skills.

**Usage:**

```bash
uv run skill-fleet analytics --user-id USER_ID [OPTIONS]
```

**Required Arguments:**

- `--user-id TEXT` - User identifier

**Optional Arguments:**

- `--json` - Output as JSON
- `--time-range TEXT` - Time range for analytics (e.g., `7d`, `30d`, `all`)

**Examples:**

```bash
# View analytics
uv run skill-fleet analytics --user-id developer_123

# JSON output
uv run skill-fleet analytics --user-id developer_123 --json

# Specific time range
uv run skill-fleet analytics --user-id developer_123 --time-range 30d
```

---

## Common Workflows

### New Skill Creation

```bash
# 1. Create skill
uv run skill-fleet create-skill --task "Create authentication utilities"

# 2. Validate (automatically done during creation, but can re-run)
uv run skill-fleet validate-skill path/to/new/skill

# 3. Regenerate XML for agent context
uv run skill-fleet generate-xml -o available_skills.xml
```

### Migrating Existing Skills

```bash
# 1. Preview migration
uv run skill-fleet migrate --dry-run

# 2. Apply migration
uv run skill-fleet migrate

# 3. Validate all migrated skills
for skill in $(find skills -name "metadata.json" -type f); do
  uv run skill-fleet validate-skill "$(dirname "$skill")"
done

# 4. Generate XML
uv run skill-fleet generate-xml -o available_skills.xml
```

### CI/CD Integration

```bash
# Create skill in automated pipeline
uv run skill-fleet create-skill \
  --task "Create monitoring utilities" \
  --auto-approve \
  --json > result.json

# Check exit code
if [ $? -eq 0 ]; then
  echo "Skill created successfully"
  uv run skill-fleet generate-xml -o available_skills.xml
else
  echo "Skill creation failed"
  exit 1
fi
```

### Bulk Validation

```bash
# Validate all skills
find skills -name "metadata.json" -type f | while read metadata; do
  skill_dir=$(dirname "$metadata")
  echo "Validating: $skill_dir"
  uv run skill-fleet validate-skill "$skill_dir" || echo "FAILED: $skill_dir"
done
```

## Environment Variables

The CLI respects these environment variables:

- `GOOGLE_API_KEY` - **Required** for skill generation (Gemini API)
- `DEEPINFRA_API_KEY` - Optional alternative LLM provider
- `LITELLM_API_KEY` - Optional for LiteLLM proxy
- `LANGFUSE_SECRET_KEY` - Optional for telemetry
- `DSPY_CACHEDIR` - Custom cache directory for DSPy
- `DSPY_TEMPERATURE` - Global temperature override

## Configuration Files

### Fleet Configuration (config.yaml)

Controls LLM configuration and workflow behavior:

```yaml
llm:
  provider: google
  model: gemini-3-flash-preview
  thinking_level:
    planning: high
    understanding: medium
    initialization: minimal
```

### Taxonomy Configuration (taxonomy_meta.json)

Stored in skills root, tracks taxonomy metadata:

```json
{
  "version": "1.0.0",
  "last_updated": "2024-01-07T12:00:00Z",
  "total_skills": 42
}
```

## Exit Codes

All commands follow these exit code conventions:

- `0` - Success
- `1` - General error or validation failure
- `2` - Invalid arguments or usage
- `130` - Interrupted (Ctrl+C)

## Logging

Control verbosity with environment variables:

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uv run skill-fleet create-skill --task "..."

# Quiet mode (errors only)
export LOG_LEVEL=ERROR
uv run skill-fleet migrate
```

## Getting Help

```bash
# General help
uv run skill-fleet --help

# Command-specific help
uv run skill-fleet create-skill --help
uv run skill-fleet migrate --help
uv run skill-fleet generate-xml --help
```

## DSPy Configuration

The CLI now automatically configures DSPy settings on startup using the centralized `configure_dspy()` function. This ensures consistent LM configuration across all commands.

### Environment Variables

**DSPY_CACHEDIR**
Override DSPy cache directory (default: `.dspy_cache` in current directory)

```bash
export DSPY_CACHEDIR=/var/cache/dspy
uv run skill-fleet create-skill --task "..."
```

**DSPY_TEMPERATURE**
Override LM temperature globally for all operations

```bash
export DSPY_TEMPERATURE=0.7
uv run skill-fleet create-skill --task "..."
```

### Configuration Priority

LM settings are resolved in the following order (highest to lowest priority):

1. **Command-specific LM** - Individual commands may use task-specific LMs
2. **Environment variables** - `DSPY_TEMPERATURE`, `DSPY_CACHEDIR`
3. **config.yaml settings** - Task-specific and role-based model configuration
4. **Defaults** - Fallback defaults when no other configuration is present

### Task-Specific LMs

The system uses different LMs for different phases of skill creation:

| Task               | Purpose                               |
| ------------------ | ------------------------------------- |
| `skill_understand` | Task analysis and understanding       |
| `skill_plan`       | Structure planning                    |
| `skill_initialize` | Directory and metadata initialization |
| `skill_edit`       | Content generation                    |
| `skill_package`    | Validation and packaging              |
| `skill_validate`   | Compliance checking                   |

These are configured in `config/config.yaml` under the `model_tasks` section.

---

## See Also

- [API Reference](api-reference.md) - Python programmatic API
- [Overview](overview.md) - System architecture
- [Getting Started Guide](getting-started/index.md) - Installation & CLI workflow

---

## Additional Resources

- [Skill Creator Guide](skill-creator-guide.md) - Detailed workflow explanation
- [agentskills.io Compliance](agentskills-compliance.md) - Migration and validation details
