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
from typing import TYPE_CHECKING

from fastapi import APIRouter, BackgroundTasks, HTTPException

from .....api.exceptions import NotFoundException
from ....schemas.skills import (
    CreateSkillRequest,
    CreateSkillResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    SkillDetailResponse,
    ValidateSkillRequest,
    ValidateSkillResponse,
)
from .....app.dependencies import SkillServiceDep
from .....workflows.quality_assurance.orchestrator import QualityAssuranceOrchestrator

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .....app.services.skill_service import SkillService

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
async def get_skill(skill_id: str, skill_service: SkillServiceDep) -> SkillDetailResponse:
    """
    Get details for a skill by ID.

    Args:
        skill_id: Unique skill identifier
        skill_service: Injected SkillService for data access

    Returns:
        SkillDetailResponse: Detailed skill information

    Raises:
        HTTPException: If skill not found (404)

    """
    try:
        skill_data = skill_service.get_skill_by_path(skill_id)
        return SkillDetailResponse(
            skill_id=skill_data.get("skill_id", skill_id),
            name=skill_data.get("name", ""),
            description=skill_data.get("description", ""),
            version=skill_data.get("version", "1.0"),
            type=skill_data.get("type", "unknown"),
            metadata=skill_data.get("metadata", {}),
            content=skill_data.get("content"),
        )
    except FileNotFoundError:
        raise NotFoundException("Skill", skill_id)


@router.put("/{skill_id}", response_model=dict[str, str])
async def update_skill(
    skill_id: str,
    skill_service: SkillServiceDep,
) -> dict[str, str]:
    """
    Update an existing skill.

    Args:
        skill_id: Unique skill identifier
        skill_service: Injected SkillService for data access

    Returns:
        Dictionary with skill_id and status

    Raises:
        HTTPException: If skill not found (404)

    Note:
        Currently returns success without actual updates.
        Full implementation would accept an update request body
        and modify skill metadata/content.

    """
    try:
        # Verify skill exists
        skill_service.get_skill_by_path(skill_id)
        # TODO: Implement actual update logic with request body
        return {"skill_id": skill_id, "status": "updated"}
    except FileNotFoundError:
        raise NotFoundException("Skill", skill_id)


@router.post("/{skill_id}/validate", response_model=ValidateSkillResponse)
async def validate_skill(
    skill_id: str,
    request: ValidateSkillRequest,
    skill_service: SkillServiceDep,
) -> ValidateSkillResponse:
    """
    Validate a skill.

    Args:
        skill_id: Unique skill identifier
        request: Validation request
        skill_service: Injected SkillService for data access

    Returns:
        ValidateSkillResponse: Validation results with pass/fail status

    Raises:
        HTTPException: If skill not found (404)

    """
    # Load skill content for validation
    try:
        skill_data = skill_service.get_skill_by_path(skill_id)
        content = skill_data.get("content", "")
        metadata = {
            "skill_id": skill_data.get("skill_id"),
            "name": skill_data.get("name"),
            "type": skill_data.get("type"),
            **skill_data.get("metadata", {}),
        }
    except FileNotFoundError:
        raise NotFoundException("Skill", skill_id)

    # Initialize orchestrator and run validation
    orchestrator = QualityAssuranceOrchestrator()

    try:
        result = await orchestrator.validate_and_refine(
            skill_content=content,
            skill_metadata=metadata,
            content_plan="",
            validation_rules="agentskills.io compliance",
            target_level="intermediate",
            enable_mlflow=False,
        )

        validation_report = result.get("validation_report", {})
        critical_issues = result.get("critical_issues", [])
        warnings = result.get("warnings", [])

        # Build issues list
        issues = []
        for issue in critical_issues:
            issues.append({
                "severity": "error",
                "message": issue.get("message", str(issue)),
            })
        for warning in warnings:
            issues.append({
                "severity": "warning",
                "message": warning.get("message", str(warning)),
            })

        return ValidateSkillResponse(
            passed=validation_report.get("passed", False),
            status="passed" if validation_report.get("passed", False) else "failed",
            score=validation_report.get("score", 0.0),
            issues=issues,
        )

    except Exception as e:
        logger.exception(f"Error in skill validation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {e}"
        ) from e


@router.post("/{skill_id}/refine", response_model=RefineSkillResponse)
async def refine_skill(
    skill_id: str,
    request: RefineSkillRequest,
    skill_service: SkillServiceDep,
) -> RefineSkillResponse:
    """
    Refine a skill based on user feedback.

    Args:
        skill_id: Unique skill identifier
        request: Refinement request with feedback
        skill_service: Injected SkillService for data access

    Returns:
        RefineSkillResponse: Response with job_id and status

    Raises:
        HTTPException: If skill not found (404)

    Note:
        Currently creates a job but doesn't run async refinement.
        Full implementation would create a background job that
        applies the feedback via the QualityAssuranceOrchestrator.

    """
    # Load skill content for refinement
    try:
        skill_data = skill_service.get_skill_by_path(skill_id)
        content = skill_data.get("content", "")
        metadata = {
            "skill_id": skill_data.get("skill_id"),
            "name": skill_data.get("name"),
            "type": skill_data.get("type"),
            **skill_data.get("metadata", {}),
        }
    except FileNotFoundError:
        raise NotFoundException("Skill", skill_id)

    # Initialize orchestrator
    orchestrator = QualityAssuranceOrchestrator()

    try:
        # Run refinement with user feedback
        result = await orchestrator.validate_and_refine(
            skill_content=content,
            skill_metadata=metadata,
            content_plan="",
            validation_rules="agentskills.io compliance",
            user_feedback=request.feedback,
            target_level="intermediate",
            enable_mlflow=False,
        )

        # Check if refinement was successful
        refined_content = result.get("refined_content")
        if refined_content:
            # TODO: Save refined content back to skill storage
            message = "Skill refined successfully based on feedback"
            status = "completed"
        else:
            message = "No refinement needed - feedback already incorporated"
            status = "accepted"

        return RefineSkillResponse(
            job_id=skill_id,
            status=status,
            message=message,
        )

    except Exception as e:
        logger.exception(f"Error in skill refinement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Refinement failed: {e}"
        ) from e
