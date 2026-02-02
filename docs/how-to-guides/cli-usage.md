# CLI Usage Guide

**Last Updated**: 2026-01-31

This guide covers common CLI workflows for skill creation, validation, and management.

## Prerequisites

All commands use `uv run` to ensure the correct Python environment:

```bash
uv run skill-fleet --help
```

## Quick Start Workflow

### 1. Start the API Server

The CLI requires a running API server for most operations:

```bash
uv run skill-fleet serve
```

This starts the server on `http://localhost:8000` with:
- Interactive setup prompts (unless `--auto-accept`)
- Automatic database initialization
- Development mode with `--reload` flag

**Production mode:**
```bash
uv run skill-fleet serve --port 8080 --host 0.0.0.0 --no-reload
```

---

## Creating Skills

### Interactive Mode (Recommended)

The chat command provides the best interactive experience:

```bash
uv run skill-fleet chat "Create a Python async programming skill"
```

**Features:**
- Real-time streaming updates
- Live reasoning/thinking display
- Arrow key navigation for choices
- Automatic HITL handling

### Non-Interactive Mode (CI/Automation)

For scripts and automation, use `--auto-approve`:

```bash
uv run skill-fleet create "Python async skill" --auto-approve
```

This:
- Skips all interactive prompts
- Uses default values for all choices
- Returns when complete or on error

---

## Working with Jobs

### Create a Job

```bash
uv run skill-fleet create "Task description"
```

Output shows:
```
🚀 Starting skill creation job...
✓ Job created: f47ac10b-58cc-4372-a567-0e02b2c3d479
[Progress displays...]
✨ Skill Creation Completed!
📁 Skill saved to: .skills/python-async
```

### Promote a Draft

After a job completes, promote it to the taxonomy:

```bash
uv run skill-fleet promote f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Options:**
- `--delete-draft` - Clean up draft after promotion
- `--force` - Promote even if validation had issues
- `--no-overwrite` - Fail if skill already exists

---

## Validating Skills

### Basic Validation

```bash
uv run skill-fleet validate technical/programming/python/async
```

Output:
```
validation: passed
warnings:
- Description could be more specific
```

### JSON Output for Scripting

```bash
uv run skill-fleet validate path/to/skill --json
```

Use in scripts:
```bash
if uv run skill-fleet validate "$SKILL_PATH" --json | jq -e '.passed'; then
    echo "Validation passed"
else
    echo "Validation failed"
fi
```

---

## Database Management

### Initialize Database

First-time setup or after schema changes:

```bash
uv run skill-fleet db init
```

Safe to run multiple times (idempotent).

### Reset Database (Development Only)

⚠️ **Warning: This deletes all data**

```bash
uv run skill-fleet db init --force
```

---

## Exporting Skills

### Generate XML for agentskills.io

```bash
uv run skill-fleet generate-xml -o available_skills.xml
```

This exports all skills in the agentskills.io XML format for:
- External integrations
- Skill registries
- Backup purposes

---

## Common Workflows

### Development Workflow

```bash
# 1. Ensure database is initialized
uv run skill-fleet db init

# 2. Start server in development mode
uv run skill-fleet serve --reload

# 3. In another terminal, create skills interactively
uv run skill-fleet chat "Create a React hooks skill"

# 4. Validate before promoting
uv run skill-fleet validate .skills/drafts/react-hooks

# 5. Promote to taxonomy
uv run skill-fleet promote <job_id> --delete-draft
```

### CI/CD Workflow

```bash
#!/bin/bash
set -e

# Start server in background
uv run skill-fleet serve --auto-accept --port 8000 &
SERVER_PID=$!

# Wait for server to be ready
sleep 5

# Create skill non-interactively
uv run skill-fleet create "Production skill" --auto-approve

# Validate output
uv run skill-fleet validate path/to/skill --json | jq -e '.passed'

# Generate deployment artifact
uv run skill-fleet generate-xml -o skills.xml

# Cleanup
kill $SERVER_PID
```

### Batch Processing

Process multiple skills from a file:

```bash
#!/bin/bash
while IFS= read -r task; do
    echo "Creating: $task"
    uv run skill-fleet create "$task" --auto-approve
done < tasks.txt
```

---

## Troubleshooting

### Connection Errors

If you see:
```
Could not connect to API server at http://localhost:8000
```

**Solution:**
1. Start the server: `uv run skill-fleet serve`
2. Check if port 8000 is available
3. Verify `SKILL_FLEET_API_URL` environment variable

### Validation Failures

If validation fails:
```bash
# Get detailed JSON output
uv run skill-fleet validate path/to/skill --json

# Check specific issues
uv run skill-fleet validate path/to/skill --json | jq '.errors, .warnings'
```

Common fixes:
- Missing `SKILL.md` file
- Invalid frontmatter YAML
- Missing required fields (name, description)

### Database Issues

If you see database errors:
```bash
# Reinitialize database
uv run skill-fleet db init --force

# Or check health
uv run skill-fleet db health
```

---

## Best Practices

1. **Always validate before promoting**
   ```bash
   uv run skill-fleet validate path/to/draft && uv run skill-fleet promote <job_id>
   ```

2. **Use `--auto-approve` only in controlled environments**
   - Never use in production without review
   - Good for CI/CD pipelines with pre-defined tasks

3. **Keep skills root organized**
   ```bash
   export SKILL_FLEET_SKILLS_ROOT=/path/to/skills
   ```

4. **Use JSON output for automation**
   ```bash
   uv run skill-fleet list --format json | jq '.[] | select(.category == "technical")'
   ```

5. **Clean up drafts regularly**
   ```bash
   uv run skill-fleet promote <job_id> --delete-draft
   ```

---

## Related Documentation

- [CLI Commands Reference](../reference/cli/commands.md) - Complete command reference
- [Getting Started](../tutorials/getting-started.md) - First-time tutorial
- [API Reference](../reference/api/endpoints.md) - REST API documentation
