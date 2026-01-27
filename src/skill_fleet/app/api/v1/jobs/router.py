"""
Job management routes for v1 API.

This module provides endpoints for job status tracking.
These endpoints work with the jobs module which is shared across API versions.

Endpoints:
    GET /api/v1/jobs/{job_id} - Get job status and details
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ....exceptions import NotFoundException
from ....services.jobs import get_job

router = APIRouter()


class JobDetailResponse(BaseModel):
    """
    Response model for job details.

    Contains all job status information including progress, results,
    and HITL interaction data.
    """

    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    task_description: str = Field(..., description="Task description")
    user_id: str = Field(..., description="User ID")
    current_phase: str | None = Field(None, description="Current phase")
    progress_message: str | None = Field(None, description="Progress message")
    error: str | None = Field(None, description="Error message")
    result: dict | None = Field(None, description="Job result")
    draft_path: str | None = Field(None, description="Draft path")
    intended_taxonomy_path: str | None = Field(None, description="Intended taxonomy path")
    validation_passed: bool | None = Field(None, description="Validation passed")
    validation_status: str | None = Field(None, description="Validation status")
    validation_score: float | None = Field(None, description="Validation score")
    hitl_type: str | None = Field(None, description="HITL interaction type")


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
        task_description=getattr(job, "task_description", ""),
        user_id=getattr(job, "user_id", "default"),
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
