# AGENTS.md

This repo is **Skill Fleet**: a local-first platform for creating, validating, and curating **agentskills.io**-style skills via a 3‑phase workflow (**Understanding → Generation → Validation**).

## Stack

- Python **3.12+**
- Package manager/runtime: **uv**
- API: **FastAPI** (`uvicorn`)
- CLI: **Typer** (`skill-fleet`)
- LLM orchestration: **DSPy**

## Quick Commands (from repo root)

```bash
# install (dev)
uv sync --group dev

# API server (development)
uv run skill-fleet dev
#
# Note: `skill-fleet dev` forces `SKILL_FLEET_ENV=development` to avoid production DB requirements.

# create skill (non-interactive)
uv run skill-fleet create "Create a Python decorators skill" --auto-approve

# validate + promote
uv run skill-fleet validate skills/_drafts/<job_id>
uv run skill-fleet promote <job_id> --delete-draft
```

### Makefile Shortcuts

```bash
make help
make install-dev
make dev
make test
make lint-fix
make format
make type-check
make security
make db-migrate
```

## Core Workflows

### Draft-First Skill Lifecycle

1. Create a job (`skill-fleet create …` or `skill-fleet chat …`)
2. Draft is written to `skills/_drafts/<job_id>/`
3. Validate (`skill-fleet validate …`)
4. Promote (`skill-fleet promote <job_id>`)

Useful flags:

- `skill-fleet serve --auto-accept` skips interactive prompts (useful for CI/automation)
- `skill-fleet promote --force` promotes even if workflow validation failed
- `skill-fleet promote --overwrite/--no-overwrite` controls replacing existing taxonomy skill
- `skill-fleet serve --skip-db-init` assumes DB is already initialized

### Interactive (HITL) Creation

- `uv run skill-fleet chat [TASK]` streams phases + HITL prompts
- `uv run skill-fleet terminal [TASK]` is a simpler terminal chat interface
- If arrow-key dialogs are flaky, pass `--force-plain-text`
- For compatibility mode (polling-only), use `skill-fleet chat --poll`

### Export / Consumption

- `uv run skill-fleet generate-xml [-o out.xml]` exports `<available_skills>` XML for prompt injection

### Migration / Analytics

- `uv run skill-fleet migrate --dry-run` migrates existing skills toward agentskills.io format
- `uv run skill-fleet analytics --user-id all --json` shows usage analytics and recommendations

## Database & Migrations

The CLI includes database commands:

```bash
uv run skill-fleet db status
uv run skill-fleet db init
uv run skill-fleet db migrate
```

The Makefile uses Alembic directly:

```bash
make db-migrate
make db-revision NAME="add_jobs_table"
```

## Dev Tools (scripts/)

High-level script entrypoints (see `scripts/README.md`):

```bash
# full quality suite (lint + test + typecheck)
uv run python scripts/check.py quality

# db init/migrate/seed/verify
uv run python scripts/manage_db.py init

# training data workflow
uv run python scripts/manage_data.py prepare

# optimization workflow
uv run python scripts/manage_opt.py mipro
```

MLflow UI for experiments:

```bash
./scripts/start-mlflow.sh
```

## Tests & Quality

```bash
uv run pytest
uv run pytest tests/unit/
uv run pytest -m "not integration"

uv run ruff check --fix .
uv run ruff format .
uv run ty check
uv run bandit -c pyproject.toml -r src/
uv run pre-commit run --all-files
```

Notes:

- `skills/**` and `.skills/**` are excluded from Ruff (see `pyproject.toml`).
- Integration tests may require live LLM credentials; use `-m "not integration"` when running offline.

## Configuration & Environment Variables

LLM credentials (prefers LiteLLM proxy when present):

- `LITELLM_API_KEY` (optional, preferred when set)
- `LITELLM_BASE_URL` (optional, for LiteLLM proxy)
- `GOOGLE_API_KEY` or `GEMINI_API_KEY` (fallback)

App / CLI:

- `SKILL_FLEET_ENV` (`development` default, `production` for PostgreSQL + stricter CORS)
- `SKILL_FLEET_CORS_ORIGINS` (comma-separated)
- `SKILL_FLEET_SKILLS_ROOT` (defaults to `./skills`)
- `SKILL_FLEET_API_URL` (CLI default: `http://localhost:8000`)
- `SKILL_FLEET_USER_ID` (CLI default: `default`)

Tests:

- `SKILL_FLEET_ALLOW_LLM_FALLBACK` enables deterministic fallbacks for tests

Model overrides (advanced):

- `FLEET_MODEL_DEFAULT`, `FLEET_MODEL_<TASK_NAME>`, `FLEET_MODEL_<ROLE>`
- `DSPY_TEMPERATURE` overrides temperature globally
- Base config lives in `src/skill_fleet/config/config.yaml`

## Code Conventions / Safety

- No `print()` in library code; use `logging.getLogger(__name__)`.
- Async-first modules implement `aforward()` (see `src/skill_fleet/core/modules/base.py`).
- Use `resolve_path_within_root(...)` for any filesystem access involving user input (`src/skill_fleet/common/security.py`).

## References

- Project overview + CLI: `README.md`
- Full docs index: `docs/README.md`
