"""Job management for async skill creation and HITL tracking."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from pydantic import BaseModel


class JobState(BaseModel):
    """Represents the current state of a background job."""

    job_id: str
    status: str = "pending"  # pending, running, pending_hitl, completed, failed
    hitl_type: str | None = None
    hitl_data: dict[str, Any] | None = None
    hitl_response: dict[str, Any] | None = None
    result: Any | None = None
    error: str | None = None
    saved_path: str | None = None  # Path where skill was saved (if completed)


# In-memory job store (use Redis in production)
JOBS: dict[str, JobState] = {}


def create_job() -> str:
    """Create a new job and return its unique ID."""
    job_id = str(uuid.uuid4())
    JOBS[job_id] = JobState(job_id=job_id)
    return job_id


def get_job(job_id: str) -> JobState | None:
    """Retrieve a job by its ID."""
    return JOBS.get(job_id)


async def wait_for_hitl_response(job_id: str, timeout: float = 3600.0) -> dict[str, Any]:
    """Wait for user to provide HITL response via API."""
    job = JOBS[job_id]
    start_time = asyncio.get_event_loop().time()

    while job.hitl_response is None:
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError("HITL response timed out")
        await asyncio.sleep(1)

    response = job.hitl_response
    job.hitl_response = None  # Clear for next interaction
    return response
