"""Job inspection routes.

The Skill Fleet server runs skill creation as background jobs. This router
exposes read-only job state for clients (CLI/UI) to inspect progress and
persisted artifacts.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..jobs import get_job

router = APIRouter()


@router.get("/{job_id}")
async def get_job_state(job_id: str):
    """Fetch job status and any persisted artifacts/results."""
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump(mode="json", exclude_none=True)
