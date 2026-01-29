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

import json
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

from ..dependencies import get_skill_service
from ..exceptions import NotFoundException
from ..schemas.skills import (
    CreateSkillRequest,
    CreateSkillResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    SkillDetailResponse,
    ValidateSkillRequest,
    ValidateSkillResponse,
)
from ..services.skill_service import SkillService

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/", response_model=CreateSkillResponse)
async def create_skill(
    request: CreateSkillRequest,
    background_tasks: BackgroundTasks,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
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
    from ..services.jobs import create_job, get_job

    job_id = create_job(
        task_description=request.task_description,
        user_id=request.user_id,
    )

    async def run_workflow():
        """Run the skill creation workflow in background."""
        try:
            result = await skill_service.create_skill(
                request,
                existing_job_id=job_id,
            )
            logger.info(f"Skill creation job {job_id} completed with status: {result.status}")
        except Exception as e:
            logger.error(f"Skill creation job {job_id} failed: {e}")
            # Update job status to failed
            job = get_job(job_id)
            if job:
                from ..services.jobs import update_job
                update_job(job_id, {"status": "failed", "error": str(e)})

    # Add workflow to background tasks and return immediately
    background_tasks.add_task(run_workflow)

    return CreateSkillResponse(job_id=job_id, status="pending")


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill(
    skill_id: str, skill_service: Annotated[SkillService, Depends(get_skill_service)]
) -> SkillDetailResponse:
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
    except FileNotFoundError as err:
        raise NotFoundException("Skill", skill_id) from err


class UpdateSkillRequest(BaseModel):
    """Request body for updating a skill."""

    content: str | None = None
    metadata: dict | None = None


@router.put("/{skill_id}", response_model=dict[str, str])
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
) -> dict[str, str]:
    """
    Update an existing skill.

    Args:
        skill_id: Unique skill identifier
        request: Update request with content and/or metadata
        skill_service: Injected SkillService for data access

    Returns:
        Dictionary with skill_id and status

    Raises:
        HTTPException: If skill not found (404)

    """
    try:
        # Verify skill exists
        skill_service.get_skill_by_path(skill_id)

        # Resolve the actual filesystem path
        from skill_fleet.taxonomy.manager import TaxonomyManager

        taxonomy_manager = TaxonomyManager(skill_service.skills_root)
        relative_path = taxonomy_manager.resolve_skill_location(skill_id)
        skill_path = skill_service.skills_root / relative_path

        # Update skill if content provided
        if request.content:
            skill_md_path = skill_path / "SKILL.md"
            if skill_md_path.exists():
                skill_md_path.write_text(request.content, encoding="utf-8")

        # Update metadata if provided
        if request.metadata:
            metadata_path = skill_path / "metadata.json"
            if metadata_path.exists():
                # Read existing metadata
                current = json.loads(metadata_path.read_text(encoding="utf-8"))
                # Merge updates
                current.update(request.metadata)
                # Write back
                metadata_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

        return {"skill_id": skill_id, "status": "updated"}
    except FileNotFoundError as err:
        raise NotFoundException("Skill", skill_id) from err
    except Exception as err:
        from fastapi import status

        from ..exceptions import SkillFleetAPIError

        raise SkillFleetAPIError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update skill: {str(err)}",
        ) from err


@router.post("/{skill_id}/validate", response_model=ValidateSkillResponse)
async def validate_skill(
    skill_id: str,
    request: ValidateSkillRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
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
    except FileNotFoundError as err:
        raise NotFoundException("Skill", skill_id) from err

    # Initialize workflow and run validation
    workflow = ValidationWorkflow()

    try:
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            enable_auto_refinement=False,  # Just validate, don't refine
        )

        validation_report = result.get("validation_report", {})
        issues = validation_report.get("issues", [])

        # Build issues list
        formatted_issues = []
        for issue in issues:
            formatted_issues.append(
                {
                    "severity": issue.get("severity", "warning"),
                    "message": issue.get("message", str(issue)),
                }
            )

        return ValidateSkillResponse(
            passed=validation_report.get("passed", False),
            status="passed" if validation_report.get("passed", False) else "failed",
            score=validation_report.get("score", 0.0),
            issues=formatted_issues,
        )

    except Exception as e:
        logger.exception(f"Error in skill validation: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}") from e


@router.post("/{skill_id}/refine", response_model=RefineSkillResponse)
async def refine_skill(
    skill_id: str,
    request: RefineSkillRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
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
    except FileNotFoundError as err:
        raise NotFoundException("Skill", skill_id) from err

    # Initialize workflow
    workflow = ValidationWorkflow()

    try:
        # Run validation with feedback (which triggers refinement in the workflow)
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            enable_auto_refinement=True,
            user_feedback=request.feedback,
        )

        # Check if refinement was successful
        refined_content = result.get("refined_content")
        if refined_content:
            # Save refined content back to skill storage
            try:
                skill_path = skill_service.taxonomy_manager.resolve_skill_location(skill_id)
                skill_md_path = skill_service.skills_root / skill_path / "SKILL.md"
                if skill_md_path.exists():
                    skill_md_path.write_text(refined_content, encoding="utf-8")
                    logger.debug(f"Persisted refined skill to {skill_md_path}")
                else:
                    logger.warning(f"Could not persist refinement: {skill_md_path} not found")
            except Exception as e:
                logger.error(f"Failed to persist refinement: {e}")

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
        raise HTTPException(status_code=500, detail=f"Refinement failed: {e}") from e
