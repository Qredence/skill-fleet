# Human-in-the-Loop (HITL) Guide

Last updated: 2026-01-27

HITL is central to Skills Fleet: long-running jobs pause for human confirmation, clarifications, previews, or validation.

## Key concepts

- HITL types: `clarify`, `confirm`, `preview`, `validate`.
- Jobs enter `pending_hitl` state and expose prompts at `GET /api/v2/hitl/{job_id}/prompt`.
- Clients submit responses to `POST /api/v2/hitl/{job_id}/response` with actions: `proceed`, `revise`, `refine`, `cancel`.

## Typical flow

1. Create job (POST /api/v2/skills/create) — returns `job_id`.
2. Poll job status (/api/v2/jobs/{job_id}). If `pending_hitl`, GET the prompt.
3. Display prompt to human reviewer and collect input.
4. POST response to `/api/v2/hitl/{job_id}/response`.
5. Job resumes and continues to next phase.

## Client considerations

- Use polling or webhooks to surface HITL prompts to humans.
- Keep default HITL timeout in mind (configurable in server); default implementation waits up to 1 hour.
- Validate inputs before submitting; use structured options when available.

## Best practices

- Provide concise, actionable HITL prompts to reviewers.
- Use `preview` checkpoints to show a short excerpt instead of full content when appropriate.
- Record reviewer decisions (audit trail) and log request IDs for tracing.

## See also

- API job docs: `docs/api/jobs.md`
- CLI interactive chat: `uv run skill-fleet chat` (shows HITL prompts in the terminal)
