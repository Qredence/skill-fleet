# CLI Commands Reference

**Last Updated**: 2026-01-31
**Version**: skill-fleet 0.5.0

## Overview

The Skill Fleet CLI provides command-line access to all skill creation, validation, and management operations. All commands should be run with `uv run` to ensure the correct virtual environment.

```bash
uv run skill-fleet --help
```

## Command Groups

- [Core Commands](#core-commands) - Essential skill creation workflow
- [Server Commands](#server-commands) - API server management
- [Database Commands](#database-commands) - Database operations
- [Utility Commands](#utility-commands) - Helpers and tools

---

## Core Commands

### create

Create a new skill using the 3-phase workflow (Understanding → Generation → Validation).

```bash
uv run skill-fleet create "TASK_DESCRIPTION" [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK` | string | Yes | Description of the skill to create |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--auto-approve` | False | Skip interactive HITL prompts |

**Examples:**

```bash
# Create a skill interactively
uv run skill-fleet create "Create a Python async/await programming skill"

# Create a skill without prompts (CI/automation)
uv run skill-fleet create "Python async skill" --auto-approve
```

**Output:**
- Creates a job and displays progress
- Shows final skill content in a panel
- Displays validation results
- For drafts: shows promotion command

---

### chat

Start an interactive guided session for skill creation with real-time streaming.

```bash
uv run skill-fleet chat [TASK] [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TASK` | string | No | Optional initial task description |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--auto-approve` | False | Skip interactive prompts |
| `--show-thinking/--no-show-thinking` | True | Show rationale/thinking panels |
| `--force-plain-text` | False | Disable arrow-key dialogs |
| `--no-tui` | False | Disable Ink TUI, use terminal chat |
| `--fast/--slow` | True | Use fast polling (100ms) |

**Examples:**

```bash
# Interactive chat mode
uv run skill-fleet chat

# Start with a task
uv run skill-fleet chat "Create a React hooks skill"

# CI mode (no interaction)
uv run skill-fleet chat "Python skill" --auto-approve --no-show-thinking
```

**Features:**
- Real-time streaming with 100ms polling
- Live thinking/reasoning display
- Arrow key navigation for choices
- Automatic TUI fallback

---

### promote

Promote a completed job's draft into the taxonomy.

```bash
uv run skill-fleet promote JOB_ID [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `JOB_ID` | string | Yes | Job ID from create command |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--overwrite/--no-overwrite` | True | Overwrite existing skill at path |
| `--delete-draft` | False | Delete draft after promotion |
| `--force` | False | Promote even if validation failed |

**Examples:**

```bash
# Promote a completed job
uv run skill-fleet promote f47ac10b-58cc-4372-a567-0e02b2c3d479

# Promote and cleanup
uv run skill-fleet promote <job_id> --delete-draft

# Force promotion despite validation issues
uv run skill-fleet promote <job_id> --force
```

---

### validate

Validate a skill's metadata and structure.

```bash
uv run skill-fleet validate SKILL_PATH [OPTIONS]
```

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SKILL_PATH` | string | Yes | Path to skill directory or JSON file |

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--skills-root` | Auto-detected | Skills taxonomy root directory |
| `--json` | False | Output JSON only |

**Examples:**

```bash
# Validate a skill
uv run skill-fleet validate technical/programming/python/async

# Validate with JSON output (for scripts)
uv run skill-fleet validate path/to/skill --json

# Validate with custom skills root
uv run skill-fleet validate my-skill --skills-root /custom/path
```

**Exit Codes:**
- `0` - Validation passed
- `2` - Validation failed

---

## Server Commands

### serve

Start the Skill Fleet API server.

```bash
uv run skill-fleet serve [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--port, -p` | 8000 | Port to run server on |
| `--host` | 127.0.0.1 | Host to bind to |
| `--reload, -r` | False | Enable auto-reload (dev mode) |
| `--auto-accept` | False | Skip interactive prompts |
| `--force-plain-text` | False | Disable arrow-key dialogs |
| `--skip-db-init` | False | Skip database initialization |

**Examples:**

```bash
# Start server with defaults
uv run skill-fleet serve

# Development mode with auto-reload
uv run skill-fleet serve --reload

# Production mode on different port
uv run skill-fleet serve --port 8080 --host 0.0.0.0

# Non-interactive mode
uv run skill-fleet serve --auto-accept --port 8000
```

**Features:**
- Interactive configuration prompts (unless `--auto-accept`)
- Automatic database initialization
- Development mode with auto-reload

---

## Database Commands

### db init

Initialize the database schema.

```bash
uv run skill-fleet db init [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--force` | False | Force re-creation (DELETES all data) |

**Examples:**

```bash
# Initialize database (safe to run multiple times)
uv run skill-fleet db init

# Reset database (WARNING: destructive)
uv run skill-fleet db init --force
```

**Tables Created:**
- `skills` - Skill metadata and content
- `jobs` - Background job tracking
- `hitl_interactions` - HITL session data

---

### db health

Check database health and connection status.

```bash
uv run skill-fleet db health
```

**Output:**
- Connection status
- Table counts
- Migration status

---

## Utility Commands

### list

List all skills in the taxonomy.

```bash
uv run skill-fleet list [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--skills-root` | Auto-detected | Skills taxonomy root |
| `--category` | All | Filter by category |
| `--format` | table | Output format: table, json, yaml |

**Examples:**

```bash
# List all skills
uv run skill-fleet list

# List by category
uv run skill-fleet list --category technical/programming

# JSON output for scripting
uv run skill-fleet list --format json
```

---

### migrate

Migrate skills to agentskills.io format.

```bash
uv run skill-fleet migrate [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--source` | Required | Source directory to migrate |
| `--dry-run` | False | Show what would change without applying |

**Examples:**

```bash
# Preview migration
uv run skill-fleet migrate --source ./old-skills --dry-run

# Apply migration
uv run skill-fleet migrate --source ./old-skills
```

---

### generate-xml

Export skills to agentskills.io XML format.

```bash
uv run skill-fleet generate-xml [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | stdout | Output file path |
| `--skills-root` | Auto-detected | Skills taxonomy root |

**Examples:**

```bash
# Export to file
uv run skill-fleet generate-xml -o available_skills.xml

# Export to stdout
uv run skill-fleet generate-xml
```

---

### analytics

View skill analytics and usage statistics.

```bash
uv run skill-fleet analytics [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--skill-id` | All | Filter by specific skill |
| `--period` | 30d | Time period: 7d, 30d, 90d |
| `--format` | table | Output format: table, json |

**Examples:**

```bash
# View all analytics
uv run skill-fleet analytics

# Specific skill analytics
uv run skill-fleet analytics --skill-id python-async

# JSON output
uv run skill-fleet analytics --format json --period 90d
```

---

### dev

Development utilities and helpers.

```bash
uv run skill-fleet dev [COMMAND] [OPTIONS]
```

**Subcommands:**

| Subcommand | Description |
|------------|-------------|
| `shell` | Open interactive shell with context |
| `test-api` | Test API connectivity |
| `seed` | Seed database with test data |

**Examples:**

```bash
# Open dev shell
uv run skill-fleet dev shell

# Test API connection
uv run skill-fleet dev test-api

# Seed test data
uv run skill-fleet dev seed
```

---

### terminal

Launch the terminal UI (TUI) for interactive skill management.

```bash
uv run skill-fleet terminal [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--theme` | default | UI theme: default, dark, light |

**Examples:**

```bash
# Launch TUI
uv run skill-fleet terminal

# With dark theme
uv run skill-fleet terminal --theme dark
```

---

## Global Options

These options work with any command:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit |
| `--verbose, -v` | Enable verbose output |
| `--quiet, -q` | Suppress non-error output |

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKILL_FLEET_API_URL` | API server URL | http://localhost:8000 |
| `SKILL_FLEET_USER_ID` | Default user ID | default |
| `SKILL_FLEET_SKILLS_ROOT` | Skills taxonomy root | Auto-detected |
| `SKILL_FLEET_DB_URL` | Database connection URL | sqlite:///skill_fleet.db |
| `SKILL_FLEET_CORS_ORIGINS` | Allowed CORS origins | * |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Validation failed |
| `3` | Connection error |
| `130` | Interrupted (Ctrl+C) |

---

## Examples

### Complete Workflow

```bash
# 1. Start the server
uv run skill-fleet serve --reload

# 2. In another terminal, create a skill
uv run skill-fleet create "Python async programming skill"

# 3. Promote the completed job
uv run skill-fleet promote <job_id>

# 4. Validate the promoted skill
uv run skill-fleet validate technical/programming/python/async
```

### CI/CD Pipeline

```bash
# Non-interactive skill creation
uv run skill-fleet create "Task description" --auto-approve

# Validate with JSON output for processing
uv run skill-fleet validate path/to/skill --json > validation.json

# Export for deployment
uv run skill-fleet generate-xml -o skills.xml
```

---

## Related Documentation

- [CLI How-To Guide](../../how-to-guides/cli-usage.md) - Common workflows and examples
- [API Reference](../api/endpoints.md) - REST API documentation
- [Getting Started](../../tutorials/getting-started.md) - First-time user tutorial
