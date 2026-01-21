# Skill Fleet Scripts

This directory contains utility scripts for the Skill Fleet framework, organized by function.

## 🚀 Entry Points

These are the high-level tools you should use first:

| Script | Description |
|--------|-------------|
| `manage_db.py` | Database management (init, migrate, seed, verify). |
| `manage_data.py` | Training data management (extract, synthetic, prepare). |
| `manage_opt.py` | DSPy optimization management (mipro, gepa, benchmark). |
| `check.py` | Development tools (quality, dev, cleanup). |

## 🗂️ Internal Scripts

Implementation scripts are organized in `scripts/internal/`:

| Directory | Purpose |
|-----------|---------|
| `internal/db/` | Database utilities (migrations, taxonomy). |
| `internal/opt/` | DSPy optimization scripts. |
| `internal/data/` | Training data generation. |
| `internal/tests/` | Test runner and validation scripts. |
| `internal/dev/` | Development utilities (dev server, quality checks). |
| `internal/setup/` | Setup and configuration scripts. |

## Usage Examples

### Database Setup
```bash
# Initialize schema and seed data
uv run python scripts/manage_db.py init

# Verify database state
uv run python scripts/manage_db.py verify
```

### Training Data Workflow
```bash
# Prepare training data (extract from skills + synthetic)
uv run python scripts/manage_data.py prepare

```

### Optimization Workflow
```bash
# Run MIPROv2 optimization
uv run python scripts/manage_opt.py mipro

# Run GEPA optimization
uv run python scripts/manage_opt.py gepa

# Compare optimizers
uv run python scripts/manage_opt.py benchmark
```

### Development
```bash
# Run full quality suite (lint, test, typecheck)
uv run python scripts/check.py quality

# Start development server & TUI
uv run python scripts/check.py dev

# Run technical debt cleanup
uv run python scripts/check.py cleanup
```

### Legacy Scripts
The `scripts/archive/` directory contains older scripts that have been consolidated into the new manager tools. These are kept for reference but should not be used directly.
