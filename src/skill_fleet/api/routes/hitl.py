"""HITL interaction routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..jobs import get_job

router = APIRouter()


@router.get("/{job_id}/prompt")
async def get_prompt(job_id: str):
    """Retrieve the current HITL prompt for a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    return {
        "status": job.status,
        "type": job.hitl_type,
        # Phase 1: Clarification
        "questions": hitl_data.get("questions"),
        "rationale": hitl_data.get("rationale"),
        # Phase 1: Confirmation
        "summary": hitl_data.get("summary"),
        "path": hitl_data.get("path"),
        # Phase 2: Preview
        "content": hitl_data.get("content"),
        "highlights": hitl_data.get("highlights"),
        # Phase 3: Validation
        "report": hitl_data.get("report"),
        "passed": hitl_data.get("passed"),
        # Result data
        "skill_content": job.result.skill_content if job.result else None,
        "saved_path": job.saved_path,  # Path where skill was saved
        "error": job.error,
    }


@router.post("/{job_id}/response")
async def post_response(job_id: str, response: dict):
    """Submit a response to an HITL prompt."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.hitl_response = response
    return {"status": "accepted"}
