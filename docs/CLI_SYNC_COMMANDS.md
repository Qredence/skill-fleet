# CLI Commands for Database Sync

Quick reference for the new database sync commands.

---

## Available Commands

### `skill-fleet export-to-db`

Export skills from local directory to Neon database.

```bash
uv run skill-fleet export-to-db [OPTIONS]
```

**Options:**
- `--skills-dir, -s`: Skills directory path (default: `.skills`)
- `--dry-run, -n`: Preview changes without writing
- `--force, -f`: Force overwrite of existing skills

**Environment Variables:**
- `SKILL_FLEET_SKILLS_DIR`: Default skills directory
- `DATABASE_URL`: Neon database connection string

**Examples:**
```bash
# Export all skills
uv run skill-fleet export-to-db

# Preview export
uv run skill-fleet export-to-db --dry-run

# Export with force overwrite
uv run skill-fleet export-to-db --force

# Use custom skills directory
uv run skill-fleet export-to-db --skills-dir ./skills
```

**Output:**
- Creates/updates skills in database
- Prints summary table with counts (created, updated, skipped, errors)
- Exit code 0 on success, 1 on errors

---

### `skill-fleet import-from-db`

Import skills from Neon database to local directory.

```bash
uv run skill-fleet import-from-db [OPTIONS]
```

**Options:**
- `--skills-dir, -s`: Target skills directory (default: `skills`)
- `--skill-path, -p`: Import specific skill by path
- `--status`: Filter by status (default: `active`)

**Status Filters:**
- `active`: Import only active skills
- `draft`: Import only draft skills
- `all`: Import all skills (active + draft)

**Environment Variables:**
- `SKILL_FLEET_SKILLS_DIR`: Default skills directory
- `DATABASE_URL`: Neon database connection string

**Examples:**
```bash
# Import all active skills
uv run skill-fleet import-from-db

# Import specific skill
uv run skill-fleet import-from-db --skill-path "development/languages/python"

# Import only drafts
uv run skill-fleet import-from-db --status draft

# Import all skills
uv run skill-fleet import-from-db --status all
```

**Output:**
- Creates `SKILL.md` files in skills directory
- Maintains directory structure from skill paths
- Prints summary table (created, updated, total)
- Exit code 0 on success, 1 on errors

---

### `skill-fleet sync-db`

Bidirectional synchronization between local files and database.

```bash
uv run skill-fleet sync-db [OPTIONS]
```

**Options:**
- `--skills-dir, -s`: Skills directory path (default: `.skills`)
- `--dry-run, -n`: Preview changes without writing

**Environment Variables:**
- `SKILL_FLEET_SKILLS_DIR`: Default skills directory
- `DATABASE_URL`: Neon database connection string

**Examples:**
```bash
# Full bidirectional sync
uv run skill-fleet sync-db

# Preview sync
uv run skill-fleet sync-db --dry-run

# Sync with custom directory
uv run skill-fleet sync-db --skills-dir ./skills
```

**Workflow:**
1. **Export Phase**: Local → Database (updates DB with local changes)
2. **Import Phase**: Database → Local (updates files with DB changes)
3. **Completion**: Both sources are synchronized

**Output:**
- Runs export-to-db first
- Runs import-from-db second
- Prints summary of both phases
- Exit code 0 on success, 1 on errors

---

## Common Workflows

### Initial Setup

First time setting up database sync:

```bash
# 1. Set DATABASE_URL
export DATABASE_URL="postgresql://..."

# 2. Export existing skills
uv run skill-fleet export-to-db

# 3. Verify in database
# (Use Neon Console SQL Editor)
# SELECT COUNT(*) FROM skills;

# 4. (Optional) Import back to verify
# mv skills skills.backup
# uv run skill-fleet import-from-db
# diff -r skills.backup skills
```

### Daily Development

Edit skills locally and sync to database:

```bash
# 1. Edit skill locally
vim .skills/python/async/SKILL.md

# 2. Sync to database
uv run skill-fleet export-to-db

# 3. Continue editing...
vim .skills/python/async/SKILL.md

# 4. Sync again
uv run skill-fleet export-to-db
```

### Team Collaboration

Multiple developers using same database:

```bash
# Developer A: Export changes
uv run skill-fleet export-to-db

# Developer B: Pull latest changes
uv run skill-fleet import-from-db

# Developer B: Make changes
vim skills/development/docker/SKILL.md

# Developer B: Export changes
uv run skill-fleet export-to-db
```

### Database-First Workflow

Create skills via API, then pull to local files:

```bash
# 1. Create skill via API
curl -X POST http://localhost:8000/api/v2/skills \
  -d '{"task_description": "Create Docker skill"}'

# 2. Import drafts from database
uv run skill-fleet import-from-db --status draft

# 3. Edit locally
vim skills/operations/docker/SKILL.md

# 4. Re-export
uv run skill-fleet export-to-db
```

### Conflict Resolution

Handle conflicts between local and database versions:

```bash
# Scenario: Local changes and database changes

# Option 1: Local wins (force database update)
uv run skill-fleet export-to-db --force

# Option 2: Database wins (pull from database)
uv run skill-fleet import-from-db

# Option 3: Manual review (use dry-run)
uv run skill-fleet export-to-db --dry-run
# Review changes, then apply
uv run skill-fleet export-to-db
```

---

## Environment Setup

### Required Variables

```bash
# Neon Database URL (REQUIRED)
export DATABASE_URL="postgresql://neondb_owner:npg_DroldK7R6Bci@ep-divine-voice-ahu0xhvb.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Skills directory (OPTIONAL)
export SKILL_FLEET_SKILLS_DIR=".skills"
```

### From .env File

```bash
# .env file
DATABASE_URL="postgresql://neondb_owner:npg_DroldK7R6Bci@ep-divine-voice-ahu0xhvb.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
SKILL_FLEET_SKILLS_DIR=".skills"
```

---

## Testing

### Run Test Suite

```bash
# Run all sync tests
uv run python scripts/test_db_sync.py
```

**Test Coverage:**
- Export dry-run
- Export to database
- Import from database
- Import specific skill
- Sync dry-run

---

## Troubleshooting

### "DATABASE_URL not set"

**Error:** `DATABASE_URL not set in environment`

**Solution:**
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Or export manually
export DATABASE_URL="postgresql://..."
```

### "Skills directory not found"

**Error:** `Skills directory not found: ...`

**Solution:**
```bash
# Check directory exists
ls -la .skills/

# Or specify correct path
uv run skill-fleet export-to-db --skills-dir skills/
```

### "Duplicate key value violates unique constraint"

**Error:** Skill already exists in database

**Solution:**
```bash
# Use force flag to update existing
uv run skill-fleet export-to-db --force
```

### Import creates wrong directory structure

**Problem:** Database skill paths don't match local structure

**Solution:**
- Verify taxonomy is seeded
- Check skill paths in database
- Use correct format: `development/languages/python`

---

## Performance Tips

### Large Skill Sets

```bash
# For many skills, use dry-run first
uv run skill-fleet export-to-db --dry-run > export.log

# Review log, then apply
uv run skill-fleet export-to-db
```

### Incremental Updates

```bash
# Export only changed skills (import script handles this automatically)
# Just run export regularly
uv run skill-fleet export-to-db
```

### Network Optimization

```bash
# For slow connections, batch imports
# Import all at once rather than one-by-one
uv run skill-fleet import-from-db --status all
```

---

## Related Commands

- `skill-fleet list`: List skills in database
- `skill-fleet validate`: Validate skill files
- `skill-fleet create`: Create new skill via API

---

## Next Steps

After mastering database sync:

1. **Set up API**: Start FastAPI server for background jobs
2. **Automate sync**: Add to Git hooks or CI/CD
3. **Monitor usage**: Use analytics to track sync patterns
4. **Validate quality**: Ensure compliance with agentskills.io spec
