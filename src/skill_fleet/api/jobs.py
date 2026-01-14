"""Job management for async skill creation and HITL tracking."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Import Pydantic models from schemas per FastAPI best practices
from .schemas import DeepUnderstandingState, JobState, TDDWorkflowState

logger = logging.getLogger(__name__)


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

    # Update timestamp when response received
    job.updated_at = datetime.now(UTC)

    return response


# =============================================================================
# Session Persistence
# =============================================================================


# Session directory for persistence
SESSION_DIR = Path(".skill_fleet_sessions")
SESSION_DIR.mkdir(exist_ok=True)


def save_job_session(job_id: str) -> bool:
    """Save job state to disk for persistence.

    Args:
        job_id: The job ID to save

    Returns:
        True if save succeeded, False otherwise
    """
    job = JOBS.get(job_id)
    if not job:
        logger.warning(f"Cannot save session: job {job_id} not found")
        return False

    try:
        session_file = SESSION_DIR / f"{job_id}.json"
        session_data = job.model_dump(mode="json", exclude_none=True)
        session_file.write_text(json.dumps(session_data, indent=2, default=str), encoding="utf-8")
        logger.debug(f"Saved session for job {job_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to save session for job {job_id}: {e}")
        return False


def load_job_session(job_id: str) -> JobState | None:
    """Load job state from disk.

    Args:
        job_id: The job ID to load

    Returns:
        JobState if found, None otherwise
    """
    try:
        session_file = SESSION_DIR / f"{job_id}.json"
        if not session_file.exists():
            return None

        session_data = json.loads(session_file.read_text(encoding="utf-8"))

        # Reconstruct JobState from saved data
        # Need to handle nested models properly
        tdd_data = session_data.pop("tdd_workflow", {})
        deep_data = session_data.pop("deep_understanding", {})

        job = JobState(**session_data)

        # Restore nested models
        if tdd_data:
            job.tdd_workflow = TDDWorkflowState(**tdd_data)
        if deep_data:
            job.deep_understanding = DeepUnderstandingState(**deep_data)

        JOBS[job_id] = job
        logger.info(f"Loaded session for job {job_id}")
        return job

    except Exception as e:
        logger.error(f"Failed to load session for job {job_id}: {e}")
        return None


def list_saved_sessions() -> list[str]:
    """List all saved session IDs.

    Returns:
        List of job IDs with saved sessions
    """
    try:
        return [f.stem for f in SESSION_DIR.glob("*.json")]
    except Exception:
        return []


def delete_job_session(job_id: str) -> bool:
    """Delete a saved session.

    Args:
        job_id: The job ID to delete

    Returns:
        True if deletion succeeded, False otherwise
    """
    try:
        session_file = SESSION_DIR / f"{job_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete session for job {job_id}: {e}")
        return False


def cleanup_old_sessions(max_age_hours: float = 24.0) -> int:
    """Clean up old session files.

    Args:
        max_age_hours: Maximum age in hours before deletion

    Returns:
        Number of sessions cleaned up
    """
    import time

    cleaned = 0
    cutoff_time = time.time() - (max_age_hours * 3600)

    try:
        for session_file in SESSION_DIR.glob("*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    cleaned += 1
                except Exception:
                    pass
    except Exception:
        pass

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old session(s)")

    return cleaned
