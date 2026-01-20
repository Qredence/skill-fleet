"""Job inspection routes.

The Skill Fleet server runs skill creation as background jobs. This router
exposes read-only job state for clients (CLI/UI) to inspect progress and
persisted artifacts.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from ..exceptions import NotFoundException
from ..job_manager import get_job_manager
from ..jobs import list_saved_sessions, load_job_session
from ..schemas import JobState

router = APIRouter()


@router.get("/", response_model=list[JobState])
async def list_jobs(
    status: str | None = Query(default=None, description="Filter by status"),
    user_id: str | None = Query(default=None, description="Filter by user ID"),
    include_saved: bool = Query(default=True, description="Include jobs from disk sessions"),
) -> list[JobState]:
    """List all jobs with optional filtering.

    Returns jobs from in-memory store and optionally from persisted sessions.

    Args:
        status: Filter by job status (pending, running, pending_hitl, completed, failed)
        user_id: Filter by user ID
        include_saved: Whether to load and include jobs from disk sessions

    Returns:
        List of JobState objects matching the filters
    """
    jobs: list[JobState] = []
    manager = get_job_manager()

    # Get in-memory jobs from manager cache
    for job_id in list(manager.memory.store.keys()):
        job = manager.get_job(job_id)
        if job:
            jobs.append(job)

    # Load persisted sessions if requested (for jobs older than TTL)
    if include_saved:
        saved_ids = list_saved_sessions()
        for job_id in saved_ids:
            if not manager.memory.get(job_id):
                # Offload blocking file I/O to thread pool to avoid blocking event loop
                loaded = await asyncio.to_thread(load_job_session, job_id)
                if loaded:
                    jobs.append(loaded)

    # Apply filters
    if status:
        jobs = [j for j in jobs if j.status == status]
    if user_id:
        jobs = [j for j in jobs if j.user_id == user_id]

    # Sort by updated_at descending (most recent first)
    jobs.sort(key=lambda j: j.updated_at, reverse=True)

    return jobs


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
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if job is None:
        raise NotFoundException("Job", job_id)
    return job
