# API Guide

Last updated: 2026-01-27

## Summary

This guide describes the Skills Fleet HTTP API and recommends how to use it.

- Production API: v2 (base path `/api/v2`) — job-based, stable
- Experimental chat API: v1 (base path `/api/v1`) — streaming/chat features

If you are integrating with Skills Fleet for production use, prefer the v2 endpoints.

## Quick start

Start the server locally:

```bash
uv run skill-fleet serve --port 8000
# or
uvicorn skill_fleet.app.main:app --reload --port 8000
```

OpenAPI: http://localhost:8000/docs

Base URL (local): `http://localhost:8000/api/v2`

## Design overview

v2 uses a job-based pattern for long-running workflows: create a job, poll for status, and respond to HITL checkpoints when requested. This prevents HTTP timeouts and supports interactive human-in-the-loop review.

Key patterns:

- Asynchronous job creation (202 Accepted + job_id)
- Polling job status and HITL prompts
- Draft-first flow: generated drafts are saved under `skills/_drafts/<job_id>/...` and must be promoted to the taxonomy

## Core endpoints (high-level)

- POST /api/v2/skills/create — create a skill (async)
- GET /api/v2/skills/{path} — retrieve a skill by path or id
- GET /api/v2/hitl/{job_id}/prompt — get current HITL prompt for a job
- POST /api/v2/hitl/{job_id}/response — submit HITL response
- GET /api/v2/taxonomy — list taxonomy
- GET /api/v2/taxonomy/xml — generate agentskills.io `<available_skills>` XML
- POST /api/v2/validation/skill — validate a skill directory
- POST /api/v2/evaluation/evaluate — quality evaluation (DSPy metrics)
- POST /api/v2/optimization/start — start DSPy optimization job
- GET /api/v2/jobs/{job_id} — get job status
- POST /api/v2/drafts/{job_id}/promote — promote draft to taxonomy

For a complete reference see: `docs/api/V2_ENDPOINTS.md` (detailed) and `docs/api/V2_SCHEMAS.md` (schemas).

## Simple example (create + poll HITL)

```python
import requests, time

BASE = "http://localhost:8000/api/v2"

# Create job
resp = requests.post(f"{BASE}/skills/create", json={"task_description": "Create a Python decorators skill"})
job_id = resp.json()["job_id"]

# Poll for HITL or completion
while True:
    status = requests.get(f"{BASE}/jobs/{job_id}").json()
    if status["status"] == "pending_hitl":
        prompt = requests.get(f"{BASE}/hitl/{job_id}/prompt").json()
        # respond with 'proceed' or other actions
        requests.post(f"{BASE}/hitl/{job_id}/response", json={"action": "proceed", "response": "intermediate"})
    elif status["status"] == "completed":
        print("Job complete")
        break
    elif status["status"] == "failed":
        raise RuntimeError(status.get("error"))
    time.sleep(2)
```

## Versioning guidance

- Use v2 for production integrations.
- Use v1 only for experimental streaming/chat clients — v1 is intentionally separate and may change.

## Authentication & security

The default dev setup has no auth. For production add API key or OAuth/JWT middleware. See `docs/api/middleware.md` for recommended patterns and example middleware snippets.

## Links & references

- Detailed v2 endpoints: `docs/api/V2_ENDPOINTS.md`
- Schemas: `docs/api/V2_SCHEMAS.md` and `src/skill_fleet/api/schemas/`
- Job system & HITL: `docs/api/jobs.md` and `docs/guides/hitl.md`
- Taxonomy & agentskills.io: `docs/concepts/agentskills-compliance.md`
