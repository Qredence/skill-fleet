# Copilot instructions: skill-fleet

## What this repo is

- Python 3.12+ project for **draft-first skill generation** (DSPy) with a **FastAPI server** and **Typer CLI**.
- “Skills” are on-disk artifacts under `skills/` (plus a DB for jobs/analytics/coordination).

## Entry points & boundaries

- **API server**: `uv run skill-fleet serve` → `uvicorn skill_fleet.app.main:app`.
  - FastAPI factory: `src/skill_fleet/app/factory.py` (CORS + middleware + exception mapping).
  - Routes: `src/skill_fleet/app/api/v1/router.py` (mounted at `/api/v1/*`).
- **CLI**: `src/skill_fleet/cli/app.py` (global `--api-url` / `SKILL_FLEET_API_URL`; most commands call the API via `SkillFleetClient`).

## Day-to-day dev loop (use uv)

- Install: `uv sync --group dev`
- Lint/format: `uv run ruff check --fix .` then `uv run ruff format .`
  - Note: `skills/**` is excluded from ruff (see `pyproject.toml`).
- Tests: `uv run pytest` (see `tests/conftest.py` for default env wiring).

## Critical runtime configuration

- **LLM config** is loaded by `configure_dspy()` from `config/config.yaml` (`src/skill_fleet/llm/dspy_config.py`).
  - Requires `GOOGLE_API_KEY` (or `LITELLM_API_KEY` fallback); see `.env.example`.
- **Database** is initialized during API lifespan (`src/skill_fleet/app/lifespan.py`) and by `skill_fleet.db.database.init_db()`.
  - Expect to set `DATABASE_URL` (PostgreSQL) when running the server; see `.env.example`.

## Core flow (draft-first)

1. CLI creates a job via `POST /api/v1/skills` (`src/skill_fleet/app/api/v1/skills/router.py`).
2. Workflow writes to `skills/_drafts/<job_id>/...` (draft artifacts).
3. Promote explicitly via `uv run skill-fleet promote <job_id>` or `POST /api/v1/drafts/{job_id}/promote`
   (`src/skill_fleet/app/api/v1/drafts/router.py`).

## Skill validation rules (what the code enforces)

- Validator: `src/skill_fleet/validators/skill_validator.py`.
- A directory-skill must have `SKILL.md` with **YAML frontmatter** and a **`## When to Use`** section.
- Preferred subdirs for new skills: `references/`, `guides/`, `templates/`, `scripts/`, `examples/` (+ `assets/`, `images/`, `static/`).
  Legacy dirs (`capabilities/`, `resources/`, `tests/`) are tolerated but discouraged.
- Treat filesystem paths as **untrusted input** in API code: use `skill_fleet.common.security` helpers
  (e.g., `resolve_path_within_root`, `sanitize_relative_file_path`, `sanitize_taxonomy_path`).
