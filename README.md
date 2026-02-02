# Skill Fleet

Skill Fleet is a local-first platform for creating, validating, and curating reusable **agent skills** as standards-compliant artifacts in a hierarchical on-disk taxonomy.

Skills are **draft-first** (generated into `skills/_drafts/<job_id>/...`), validated, and then explicitly promoted into the taxonomy.

---

## Quick Start

```bash
# from repo root
uv sync --group dev
cp .env.example .env

# Edit .env:
# - set GOOGLE_API_KEY (or use LITELLM_API_KEY + LITELLM_BASE_URL)
# - set DATABASE_URL (Postgres) OR set SKILL_FLEET_ENV=development to use SQLite fallback

uv run skill-fleet serve

# in another terminal
uv run skill-fleet chat "Create a Python decorators skill"
uv run skill-fleet promote <job_id>
```

---

## Why Skill Fleet?

- **Draft-first workflow**: jobs write drafts, you review, then promote
- **agentskills.io compliant**: every `SKILL.md` has required YAML frontmatter
- **FastAPI + background jobs**: long-running LLM workflows don’t block requests
- **Validation + quality checks**: structure, compliance, and quality assessment
- **Taxonomy-driven discovery**: skills live at stable paths and declare dependencies

---

## CLI (Most-Used Commands)

```bash
uv run skill-fleet --help
```

- `skill-fleet serve`: start the API server (auto-inits DB unless `--skip-db-init`)
- `skill-fleet dev`: start API server + TUI (best for development)
- `skill-fleet chat`: interactive guided skill creation (job + HITL)
- `skill-fleet create`: non-interactive skill creation (`--auto-approve`)
- `skill-fleet validate`: validate a skill directory (use `--json` for scripting)
- `skill-fleet promote`: promote a job’s draft into the taxonomy
- `skill-fleet generate-xml`: export `<available_skills>` XML for prompt injection

---

## API

- Health check: `GET /health`
- Main API: `/api/v1/*` (skills, taxonomy, jobs, HITL, quality, optimization, drafts, chat)
- OpenAPI docs (when running): `GET /docs`

See `docs/reference/api/endpoints.md` for endpoint details.

---

## Configuration

- Copy `.env.example` to `.env` and set what you need (LLM credentials, DB URL, CORS).
- LLM/task configuration lives in `src/skill_fleet/config/config.yaml` (default: `gemini/gemini-3-flash-preview`).

Common environment variables:

| Variable                               | Notes                                                                 |
| -------------------------------------- | --------------------------------------------------------------------- |
| `GOOGLE_API_KEY`                       | Direct Gemini credentials (default config)                            |
| `LITELLM_API_KEY` / `LITELLM_BASE_URL` | Use a LiteLLM proxy instead of direct provider creds                  |
| `DATABASE_URL`                         | Required in `SKILL_FLEET_ENV=production`; dev can fall back to SQLite |
| `SKILL_FLEET_CORS_ORIGINS`             | Required in production (comma-separated; `*` only in dev)             |
| `SKILL_FLEET_API_URL`                  | CLI target (default: `http://localhost:8000`)                         |
| `SKILL_FLEET_USER_ID`                  | User ID for analytics/context (default: `default`)                    |

---

## Development

```bash
# from repo root
uv run ruff check --fix .
uv run ruff format .
uv run pytest
```

More dev workflow details live in `AGENTS.md`.

---

## Documentation

- `docs/README.md`: documentation index (tutorials / how-to / reference / explanation)
- `docs/tutorials/getting-started.md`: onboarding + first workflow
- `docs/how-to-guides/cli-usage.md`: practical CLI workflows
- `docs/how-to-guides/create-a-skill.md`: end-to-end creation + promotion
- `docs/how-to-guides/validate-a-skill.md`: validation details + troubleshooting
- `docs/reference/api/endpoints.md`: API reference
- `SECURITY.md`: security policy

---

## License

Apache License 2.0. See `LICENSE`.

## Contributing

See `docs/explanation/development/contributing.md`.

---

**Version**: 0.3.5 (from `pyproject.toml`)
**Status**: Alpha
**Last Updated**: 2026-01-31
