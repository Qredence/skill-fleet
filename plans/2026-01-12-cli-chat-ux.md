# 2026-01-12 — CLI Chat Interactive UX (API-backed)

## Goal

- Make `skill-fleet chat` feel conversational and resilient while keeping a **single source of truth** in the FastAPI job + HITL workflow.
- Ensure the API remains the canonical DSPy execution surface (CLI is a thin client).

## Current State

- CLI `create`/`chat` uses:
  - `POST /api/v2/skills/create` to start a background job
  - `GET /api/v2/hitl/{job_id}/prompt` to poll for HITL prompts
  - `POST /api/v2/hitl/{job_id}/response` to answer prompts
- There is no separate `/api/v2/chat/*` surface.
- Shared HITL runner keeps `create` and `chat` behavior consistent.
- Template guidance lives in:
  - `config/templates/SKILL_md_template.md`
  - `config/templates/metadata_template.json`

## Findings (CLI chat UX)

- Polling UX: while the job is `running`, the CLI is silent (no progress affordance).
- HITL input UX: task descriptions and refinement feedback are often multi-line, but prompts are currently single-line.
- Resilience: jobs are stored in-memory; restart loses state (CLI sees 404).
- Mixed execution modes: some CLI commands call the API, others run local DSPy/workflow code (confusing when troubleshooting).

## Recommendations

### CLI UX

1. Add a Rich `Live` status line/spinner while waiting for prompts.
2. Add multi-line input helpers for:
   - initial task description
   - refine/revise feedback
3. Add resume/reconnect:
   - `skill-fleet chat --resume <job_id>`
   - `skill-fleet create --resume <job_id>` (optional)
4. Provide consistent command affordances during HITL:
   - `/help`, `/cancel`, `/exit`

### API

1. Add job inspection:
   - `GET /api/v2/jobs/{job_id}` → status, timestamps, current phase/type
2. Add explicit cancellation:
   - `POST /api/v2/jobs/{job_id}/cancel`
3. Replace polling with push (later):
   - SSE or WebSocket endpoint for HITL prompt delivery
4. Persist jobs in Redis (production mode) to survive restarts.

### DSPy + templates

1. Treat `SKILL_md_template.md` as the canonical authoring structure for generated output.
2. Standardize `metadata.json` output shape across the taxonomy (align to `metadata_template.json` + add a migration if needed).
3. Decide whether to converge `src/skill_fleet/core/` and `src/skill_fleet/workflow/` or document them as intentionally separate stacks.

## Execution Checklist

- [ ] Add `/api/v2/jobs/*` endpoints and `SkillFleetClient` methods.
- [ ] Update CLI HITL runner to show live “waiting” status and support resume.
- [ ] Add unit tests for HITL runner behavior and cancel/clarify parsing in `SkillCreationProgram`.
- [ ] Update documentation (`AGENTS.md`, README) to describe the API-backed chat flow and templates.

## Validation

```bash
# from repo root
uv run ruff check src/skill_fleet
uv run pytest -q tests/unit
```

