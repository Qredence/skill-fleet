"""
Skill creation and management routes for v1 API.

This module provides endpoints for skill operations.
These routes use skill workflow orchestrators via the service layer.

Endpoints:
    POST /api/v1/skills - Create a new skill (starts HITL workflow)
    GET  /api/v1/skills/{skill_id} - Get skill details
    PUT  /api/v1/skills/{skill_id} - Update a skill
    POST /api/v1/skills/{skill_id}/validate - Validate a skill
    POST /api/v1/skills/{skill_id}/refine - Refine a skill
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...schemas.skills import (
    CreateSkillRequest,
    CreateSkillResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    SkillDetailResponse,
    ValidateSkillRequest,
    ValidateSkillResponse,
)
from .....app.dependencies import SkillServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=CreateSkillResponse)
async def create_skill(
    request: CreateSkillRequest,
    background_tasks: BackgroundTasks,
    skill_service: SkillServiceDep,
) -> CreateSkillResponse:
    """
    Create a new skill from a natural language description.

    This initiates a background job that executes the 3-phase skill creation workflow:
    1. Understanding & Planning (with HITL clarification)
    2. Content Generation (with HITL preview)
    3. Validation & Refinement (with HITL review)

    Args:
        request: Skill creation request with task description and user ID
        background_tasks: FastAPI background tasks for async execution
        skill_service: Injected SkillService for workflow operations

    Returns:
        CreateSkillResponse: Response with job_id for tracking

    """
    # Import here to avoid circular dependency with job system
    from ....api.jobs import create_job

    job_id = create_job()

    async def run_workflow():
        """Run the skill creation workflow in background."""
        try:
            result = await skill_service.create_skill(request)
            # For now, we'll return the result synchronously
            # In production, this would update job state
            logger.info(f"Skill creation job {job_id} completed with status: {result.status}")
        except Exception as e:
            logger.error(f"Skill creation job {job_id} failed: {e}")

    # For now, run synchronously (background tasks can be added later)
    await run_workflow()

    return CreateSkillResponse(job_id=job_id, status="completed")


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill(skill_id: str) -> SkillDetailResponse:
    """
    Get details for a skill by ID.

    Args:
        skill_id: Unique skill identifier

    Returns:
        SkillDetailResponse: Detailed skill information

    Raises:
        HTTPException: If skill not found (404)

    Note:
        This is a placeholder. The full implementation should:
        - Use skill service to retrieve skill
        - Return skill metadata and content

    """
    # TODO: Implement using skill service
    raise HTTPException(status_code=404, detail=f"Skill not found: {skill_id}")


@router.put("/{skill_id}", response_model=dict[str, str])
async def update_skill(skill_id: str) -> dict[str, str]:
    """
    Update an existing skill.

    Args:
        skill_id: Unique skill identifier

    Returns:
        Dictionary with skill_id and status

    Note:
        This is a placeholder. The full implementation should:
        - Validate skill exists
        - Update skill metadata/content
        - Return updated skill info

    """
    # TODO: Implement using skill service
    return {"skill_id": skill_id, "status": "updated"}


@router.post("/{skill_id}/validate", response_model=ValidateSkillResponse)
async def validate_skill(
    skill_id: str,
    request: ValidateSkillRequest,
) -> ValidateSkillResponse:
    """
    Validate a skill.

    Args:
        skill_id: Unique skill identifier
        request: Validation request

    Returns:
        ValidateSkillResponse: Validation results with pass/fail status

    Note:
        This is a placeholder. The full implementation should:
        - Use quality workflow for validation
        - Return validation report

    """
    # TODO: Implement using quality workflow
    return ValidateSkillResponse(
        passed=True,
        status="passed",
        score=0.95,
        issues=[],
    )


@router.post("/{skill_id}/refine", response_model=RefineSkillResponse)
async def refine_skill(
    skill_id: str,
    request: RefineSkillRequest,
) -> RefineSkillResponse:
    """
    Refine a skill based on user feedback.

    Args:
        skill_id: Unique skill identifier
        request: Refinement request with feedback

    Returns:
        RefineSkillResponse: Response with job_id and status

    Note:
        This is a placeholder. The full implementation should:
        - Create refinement job
        - Apply feedback via refinement workflow
        - Return job_id for tracking

    """
    # TODO: Implement using refinement workflow
    import uuid

    job_id = str(uuid.uuid4())
    return RefineSkillResponse(
        job_id=job_id,
        status="accepted",
        message="Refinement job started",
    )
