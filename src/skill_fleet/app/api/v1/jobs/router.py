"""
Job management routes for v1 API.

This module provides endpoints for job status tracking.
These endpoints work with the jobs module which is shared across API versions.

Endpoints:
    GET /api/v1/jobs/{job_id} - Get job status and details
"""

from __future__ import annotations

from fastapi import APIRouter

from ....api.exceptions import NotFoundException
from ....api.jobs import get_job

router = APIRouter()


class JobDetailResponse:
    """
    Response model for job details.

    Contains all job status information including progress, results,
    and HITL interaction data.
    """
    def __init__(
        self,
        job_id: str,
        status: str,
        task_description: str,
        user_id: str,
        current_phase: str | None = None,
        progress_message: str | None = None,
        error: str | None = None,
        result: dict | None = None,
        draft_path: str | None = None,
        intended_taxonomy_path: str | None = None,
        validation_passed: bool | None = None,
        validation_status: str | None = None,
        validation_score: float | None = None,
        hitl_type: str | None = None,
    ):
        self.job_id = job_id
        self.status = status
        self.task_description = task_description
        self.user_id = user_id
        self.current_phase = current_phase
        self.progress_message = progress_message
        self.error = error
        self.result = result
        self.draft_path = draft_path
        self.intended_taxonomy_path = intended_taxonomy_path
        self.validation_passed = validation_passed
        self.validation_status = validation_status
        self.validation_score = validation_score
        self.hitl_type = hitl_type


@router.get("/{job_id}")
async def get_job_status(job_id: str) -> JobDetailResponse:
    """
    Get job status and details.

    Args:
        job_id: The job ID to retrieve

    Returns:
        JobDetailResponse with job status and details

    Raises:
        NotFoundException: If job not found (404)

    """
    job = get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    return JobDetailResponse(
        job_id=job.job_id,
        status=job.status,
        task_description=job.task_description,
        user_id=job.user_id,
        current_phase=job.current_phase,
        progress_message=job.progress_message,
        error=job.error,
        result=job.result.model_dump() if job.result else None,
        draft_path=job.draft_path,
        intended_taxonomy_path=job.intended_taxonomy_path,
        validation_passed=job.validation_passed,
        validation_status=job.validation_status,
        validation_score=job.validation_score,
        hitl_type=job.hitl_type,
    )
