# Database Sync Implementation Summary

Bidirectional synchronization between local `skills/` directory and Neon database is now complete.

---

## ✅ What Was Created

### 1. CLI Commands

**File**: `src/skill_fleet/cli/commands/db_sync.py`

Three new CLI commands:

#### `skill-fleet export-to-db`
Export skills from local directory to Neon database
- Parses `SKILL.md` files with YAML frontmatter
- Extracts metadata (name, description, keywords, tags)
- Infers taxonomy path from directory structure
- Creates skills with full relations (categories, capabilities, files)
- Updates existing skills (use `--force` to overwrite)

**Usage**:
```bash
uv run skill-fleet export-to-db                    # Export all
uv run skill-fleet export-to-db --dry-run          # Preview
uv run skill-fleet export-to-db --force            # Force update
```

#### `skill-fleet import-from-db`
Import skills from Neon database to local directory
- Reads skills from database with full metadata
- Filters by path or status (active/draft/all)
- Writes `SKILL.md` files with YAML frontmatter
- Maintains directory structure from skill paths

**Usage**:
```bash
uv run skill-fleet import-from-db                          # Import all active
uv run skill-fleet import-from-db --status draft        # Import drafts only
uv run skill-fleet import-from-db --status all         # Import all
uv run skill-fleet import-from-db --skill-path "development/languages/python"  # Import specific
```

#### `skill-fleet sync-db`
Bidirectional synchronization between local files and database
- Runs export-to-db first (local → database)
- Runs import-from-db second (database → local)
- Ensures both sources are consistent

**Usage**:
```bash
uv run skill-fleet sync-db                      # Full sync
uv run skill-fleet sync-db --dry-run          # Preview
```

### 2. Documentation

#### `docs/DATABASE_SYNC.md`
Comprehensive guide for database synchronization
- Detailed workflow explanations
- Environment setup instructions
- Troubleshooting tips
- Conflict resolution strategies
- Database queries for verification

#### `docs/CLI_SYNC_COMMANDS.md`
Quick reference for sync commands
- Command syntax and options
- Usage examples for all commands
- Common workflows
- Performance tips

### 3. Test Suite

**File**: `scripts/test_db_sync.py`

Automated tests for sync commands:
- Export dry-run test
- Export to database test
- Import from database test
- Import specific skill test
- Sync dry-run test

**Usage**:
```bash
# Run all tests (requires DATABASE_URL set)
uv run python scripts/test_db_sync.py
```

### 4. CLI Integration

**File**: `src/skill_fleet/cli/app.py` (modified)

New commands registered in CLI:
```python
from .commands.db_sync import export_to_db_command, import_from_db_command, sync_command

app.command(name="export-to-db")(export_to_db_command)
app.command(name="import-from-db")(import_from_db_command)
app.command(name="sync-db")(sync_command)
```

---

## 🚀 Quick Start

### Step 1: Set DATABASE_URL

```bash
# In .env file
DATABASE_URL="postgresql://neondb_owner:npg_DroldK7R6Bci@ep-divine-voice-ahu0xhvb.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Or export directly
export DATABASE_URL="postgresql://neondb_owner:npg_DroldK7R6Bci@ep-divine-voice-ahu0xhvb.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
```

### Step 2: Export Skills to Database

```bash
# Export all local skills to Neon
uv run skill-fleet export-to-db

# Preview first (recommended)
uv run skill-fleet export-to-db --dry-run
```

### Step 3: Verify in Database

```sql
-- Run in Neon Console SQL Editor
SELECT COUNT(*) as skill_count FROM skills;
SELECT s.name, s.skill_path, s.status FROM skills s ORDER BY s.skill_path;
```

### Step 4: Import Back to Local (Optional)

```bash
# Import all skills from database
uv run skill-fleet import-from-db --status all

# Verify skills were imported
ls -R skills/
```

---

## 📊 What Gets Synced

### Export to Database (Local → DB)

✅ **Skill Metadata**
- Name, description, version
- Type, weight, load priority
- Status (draft/active)
- Scope

✅ **Relations**
- Taxonomy categories (inferred from path)
- Keywords and tags
- Capabilities
- Skill files (if present)
- Dependencies and references

✅ **Content**
- Full markdown content
- YAML frontmatter preserved

### Import from Database (DB → Local)

✅ **All Above Fields**
- Complete skill metadata
- All relations
- YAML frontmatter reconstructed

✅ **Directory Structure**
- Skills organized by taxonomy path
- Example: `skills/development/languages/python/SKILL.md`

### What Doesn't Get Synced

❌ **Usage Analytics**
- Kept in database only
- Not exported to files

❌ **Job History**
- Kept in database only
- Not exported to files

❌ **Validation Reports**
- Kept in database only
- Not exported to files

---

## 🔄 Common Workflows

### Local-First Development

```bash
# 1. Edit skills locally
vim skills/python/async/SKILL.md

# 2. Export to database
uv run skill-fleet export-to-db

# 3. Repeat for each change
```

### Database-First Development

```bash
# 1. Create skill via API (background job)
curl -X POST http://localhost:8000/api/v2/skills \
  -d '{"task_description": "Create Docker skill"}'

# 2. Import draft to local files
uv run skill-fleet import-from-db --status draft

# 3. Edit and test locally
vim skills/operations/docker/SKILL.md

# 4. Re-export changes
uv run skill-fleet export-to-db
```

### Team Collaboration

```bash
# Developer A: Exports changes
uv run skill-fleet export-to-db

# Developer B: Pulls latest from database
uv run skill-fleet import-from-db

# Both work via database as shared source
```

### Sync Routine

```bash
# Run sync regularly to stay up to date
uv run skill-fleet sync-db

# Or set up cron/automated schedule
# 0 * * * * cd /path/to/skills-fleet && uv run skill-fleet sync-db
```

---

## 🎯 Benefits

1. **Bidirectional Sync**: Work with skills locally or in database, sync both ways
2. **Full Metadata Preservation**: Keywords, tags, capabilities all maintained
3. **Conflict Resolution**: `--force` flag and `--dry-run` for safe operations
4. **Taxonomy Awareness**: Automatic categorization based on directory structure
5. **Incremental Updates**: Only changed skills need re-exporting
6. **Team Collaboration**: Multiple developers can share database
7. **Version Control**: Skills can be managed in Git and database independently

---

## 📝 Next Steps

1. **Test Commands**: Run `uv run python scripts/test_db_sync.py`
2. **Start Using**: Export your skills to database
3. **Monitor**: Check Neon Console for synced skills
4. **Automate**: Add to CI/CD pipeline if desired
5. **Customize**: Edit `scripts/import_skills.py` for custom needs

---

## 📚 Documentation

- **[DATABASE_SYNC.md](docs/DATABASE_SYNC.md)**: Comprehensive sync guide
- **[CLI_SYNC_COMMANDS.md](docs/CLI_SYNC_COMMANDS.md)**: Command quick reference
- **[BACKGROUND_JOBS.md](docs/BACKGROUND_JOBS.md)**: Background job architecture
- **[AGENTS.md](AGENTS.md)**: Complete agent working guide

---

## 🔧 Technical Details

### Export Implementation
- Scans `.skills/` directory for `SKILL.md` files
- Parses YAML frontmatter using PyYAML
- Extracts capabilities using regex on content sections
- Infers taxonomy path from directory structure
- Uses SQLAlchemy ORM for database operations
- Updates existing skills (checks skill_path uniqueness)

### Import Implementation
- Queries skills from database with joins
- Filters by path or status
- Reconstructs YAML frontmatter from database fields
- Writes files preserving directory structure
- Handles overwrites of existing files

### Sync Implementation
- Calls export-to-db command first
- Calls import-from-db command second
- Propagates `--dry-run` flag
- Continues even if one phase fails
- Shows summary of both operations

---

**Status**: ✅ Complete and ready to use!

**Last Updated**: 2026-01-19
