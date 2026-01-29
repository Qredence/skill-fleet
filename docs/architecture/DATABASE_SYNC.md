# Database Sync Guide

Bidirectional synchronization between local `skills/` directory and Neon database.

---

## Overview

The Skills-Fleet system supports bidirectional sync between:
- **Local Files**: `skills/` directory with `SKILL.md` files
- **Neon Database**: Persistent storage with full skill metadata and relations

## Commands

### Export to Database

Export skills from local directory to Neon database:

```bash
# Export all skills to database
uv run skill-fleet export-to-db

# Preview without writing changes
uv run skill-fleet export-to-db --dry-run

# Use custom skills directory
uv run skill-fleet export-to-db --skills-dir ./skills

# Force overwrite existing skills
uv run skill-fleet export-to-db --force
```

**What it does:**
- Scans `skills/` directory for `SKILL.md` files
- Parses YAML frontmatter (name, description, keywords, tags)
- Extracts capabilities and skill content
- Infers taxonomy path from directory structure
- Creates skills with full metadata and relations
- Updates existing skills if found

### Import from Database

Import skills from Neon database to local directory:

```bash
# Import all active skills
uv run skill-fleet import-from-db

# Import specific skill by path
uv run skill-fleet import-from-db --skill-path "development/languages/python"

# Import only draft skills
uv run skill-fleet import-from-db --status draft

# Import all skills (including drafts)
uv run skill-fleet import-from-db --status all
```

**What it does:**
- Reads skills from Neon database
- Filters by path or status
- Writes `SKILL.md` files with YAML frontmatter
- Preserves all metadata (keywords, tags, capabilities)
- Maintains directory structure

### Bidirectional Sync

Synchronize both local files and database:

```bash
# Full bidirectional sync
uv run skill-fleet sync-db

# Preview sync without writing
uv run skill-fleet sync-db --dry-run
```

**What it does:**
1. Exports local changes to database
2. Imports database changes to local files
3. Ensures consistency between both sources

---

## Environment Configuration

The sync commands require `DATABASE_URL` to be set:

```bash
# From .env file
DATABASE_URL="postgresql://neondb_owner:password@host/database?sslmode=require"

# Or export directly
export DATABASE_URL="postgresql://neondb_owner:password@host/database?sslmode=require"
```

**Neon Database Connection:**
```
postgresql://neondb_owner:npg_DroldK7R6Bci@ep-divine-voice-ahu0xhvb.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require
```

---

## Workflow Examples

### Initial Setup

First time setting up the database:

```bash
# 1. Export existing local skills to database
uv run skill-fleet export-to-db

# 2. Verify skills were imported
uv run skill-fleet list

# Or query database directly:
# SELECT COUNT(*) FROM skills;
```

### Daily Development

Working with skills locally:

```bash
# 1. Edit skills locally
vim skills/python/async/SKILL.md

# 2. Export changes to database
uv run skill-fleet export-to-db

# 3. Verify in database
uv run skill-fleet list --filter python
```

### Database-First Workflow

Creating skills via API/database:

```bash
# 1. Create skill via API (e.g., background job)
curl -X POST http://localhost:8000/api/v2/skills \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Create skill for Docker"}'

# 2. Import new skill to local files
uv run skill-fleet import-from-db --status draft

# 3. Review and edit locally
vim skills/development/languages/docker/SKILL.md

# 4. Re-export changes
uv run skill-fleet export-to-db
```

### Team Collaboration

Multiple developers working on same codebase:

```bash
# Developer A: Exports changes
uv run skill-fleet export-to-db

# Developer B: Imports latest from database
uv run skill-fleet import-from-db

# Both stay in sync via database
```

---

## Conflict Resolution

### Export Conflicts

When exporting to database:
- **New skills**: Created in database
- **Existing skills**: Updated with current content
- **Use `--force`**: Overwrites database with local version

### Import Conflicts

When importing from database:
- **New files**: Created on local filesystem
- **Existing files**: Overwritten with database version
- **Use `--dry-run`**: Preview what will be overwritten

### Sync Conflicts

During bidirectional sync:
- Export happens first (local → database)
- Import happens second (database → local)
- Last write wins for each skill
- Review with `--dry-run` first

---

## Troubleshooting

### "DATABASE_URL not set"

**Problem**: Environment variable not configured

**Solution**:
```bash
# Check .env file
cat .env | grep DATABASE_URL

# Or export manually
export DATABASE_URL="postgresql://..."
```

### "Skills directory not found"

**Problem**: Skills directory doesn't exist or is empty

**Solution**:
```bash
# Check if directory exists
ls -la .skills/

# Or specify correct path
uv run skill-fleet export-to-db --skills-dir skills/
```

### "Duplicate key value violates unique constraint"

**Problem**: Skill already exists in database

**Solution**:
```bash
# Use force flag to update existing
uv run skill-fleet export-to-db --force
```

### Import creates wrong directory structure

**Problem**: Database skill paths don't match local structure

**Solution**:
- Check skill paths in database
- Ensure taxonomy categories are seeded
- Use correct path format: `development/languages/python`

---

## Data Integrity

### What Gets Synced

**Export to Database (Local → DB):**
- ✅ Skill name and description
- ✅ YAML frontmatter metadata
- ✅ Skill content (markdown)
- ✅ Keywords and tags
- ✅ Capabilities
- ✅ Taxonomy categorization
- ✅ Skill files (if present)
- ✅ Dependencies and references

**Import from Database (DB → Local):**
- ✅ All above fields
- ✅ Skill version
- ✅ Status (draft/active)
- ✅ Type and weight enums
- ✅ Load priority

### What Doesn't Get Synced

- ❌ Usage analytics (kept in database)
- ❌ Job history (kept in database)
- ❌ Validation reports (kept in database)
- ❌ HITL interactions (kept in database)

---

## Advanced Usage

### Filtering Imports

```bash
# Import only specific category
# (Currently requires direct skill-path filter)
uv run skill-fleet import-from-db --skill-path "development/frameworks/*"
```

### Custom Taxonomy Mapping

```bash
# Edit scripts/import_skills.py to customize taxonomy inference
# The infer_taxonomy() method determines category from path
```

### Batch Operations

```bash
# Export in dry-run mode to preview
uv run skill-fleet export-to-db --dry-run > export.log

# Review log, then apply
uv run skill-fleet export-to-db
```

---

## Database Queries

### Check Sync Status

```sql
-- Skills in database
SELECT COUNT(*) FROM skills;

-- Skills by status
SELECT status, COUNT(*) 
FROM skills 
GROUP BY status;

-- Skills by taxonomy
SELECT 
    tc.path,
    tc.name,
    COUNT(s.skill_id) as skill_count
FROM taxonomy_categories tc
LEFT JOIN skill_categories sc ON tc.category_id = sc.category_id
LEFT JOIN skills s ON sc.skill_id = s.skill_id
WHERE tc.level > 0
GROUP BY tc.path, tc.name
ORDER BY skill_count DESC;
```

### Find Orphaned Skills

```sql
-- Skills not in any taxonomy category
SELECT s.skill_id, s.name, s.skill_path
FROM skills s
LEFT JOIN skill_categories sc ON s.skill_id = sc.skill_id
WHERE sc.category_id IS NULL;
```

---

## Next Steps

After setting up database sync:

1. **Automate sync**: Add to CI/CD pipeline
2. **Set up API**: Start FastAPI server for background jobs
3. **Monitor usage**: Use analytics to track skill access
4. **Validate skills**: Ensure compliance with agentskills.io spec
5. **Optimize queries**: Add indexes for frequently used filters

---

**Related Documentation:**
- [CLI Reference](cli-reference.md)
- [API Reference](api-reference.md)
- [agentskills.io Compliance](agentskills-compliance.md)
- [Background Jobs](BACKGROUND_JOBS.md)
