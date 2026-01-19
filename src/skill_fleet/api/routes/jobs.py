"""Job inspection routes.

The Skill Fleet server runs skill creation as background jobs. This router
exposes read-only job state for clients (CLI/UI) to inspect progress and
persisted artifacts.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..exceptions import NotFoundException
from ..jobs import get_job
from ..schemas import JobState

router = APIRouter()


@router.get("/{job_id}", response_model=JobState)
async def get_job_state(job_id: str) -> JobState:
    """Fetch job status and any persisted artifacts/results.

    Returns the complete job state including:
    - Current status (pending, running, pending_hitl, completed, failed)
    - HITL interaction data if waiting for user input
    - Validation results if completed
    - Draft/final paths for the created skill

    Args:
        job_id: Unique identifier for the job

    Returns:
        JobState with all job details

    Raises:
        NotFoundException: If job not found
    """
    job = get_job(job_id)
    if job is None:
        raise NotFoundException("Job", job_id)
    return job
