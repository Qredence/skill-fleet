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

from skill_fleet.common.security import resolve_path_within_root
from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow
from skill_fleet.core.workflows.streaming import WorkflowEventType
from skill_fleet.validators import SkillValidator

from ..dependencies import get_skill_service
from ..exceptions import NotFoundException
from ..schemas.skills import (
    CreateSkillRequest,
    CreateSkillResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    SkillDetailResponse,
    SkillListItem,
    UpdateSkillResponse,
    ValidateSkillRequest,
    ValidateSkillResponse,
)
from ..services.skill_service import SkillService

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get(
    "/",
    response_model=list[SkillListItem],
    responses={
        500: {"description": "Internal server error during skill discovery"},
    },
)
async def list_skills(
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
    status: str | None = None,
    search: str | None = None,
) -> list[SkillListItem]:
    """
    List skills in the taxonomy.

    Query params are best-effort filters; currently they are applied client-side.
    """
    # Load all skills (metadata_cache may be incomplete until discovery runs).
    try:
        from skill_fleet.taxonomy.discovery import ensure_all_skills_loaded

        ensure_all_skills_loaded(
            skill_service.taxonomy_manager.skills_root,
            skill_service.taxonomy_manager.metadata_cache,
            skill_service.taxonomy_manager._load_skill_dir_metadata,
        )
    except Exception as exc:
        # If discovery fails, fall back to whatever is already cached.
        logger.debug("Skill discovery failed; using cached metadata: %s", exc)

    items = [
        SkillListItem(skill_id=skill_id, name=meta.name, description=meta.description)
        for skill_id, meta in skill_service.taxonomy_manager.metadata_cache.items()
    ]

    # Apply simple filters.
    if search:
        q = search.lower()
        items = [i for i in items if q in i.name.lower()]
    if status:
        # Status isn't tracked in metadata today; placeholder for future filtering.
        # Currently, status is accepted but not used to filter items.
        pass

    return sorted(items, key=lambda x: x.skill_id)


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

    job_id = await create_job(
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

            # Update job status and result upon completion
            # This ensures the job moves to a terminal state (completed or pending_review)
            if result.status in ("completed", "pending_review"):
                from ..services.jobs import update_job

                await update_job(
                    job_id,
                    {
                        "status": result.status,
                        "result": result,
                        "progress_percent": 100.0,
                        "progress_message": "Skill creation completed",
                    },
                )

            logger.info(f"Skill creation job {job_id} completed with status: {result.status}")
        except Exception as e:
            logger.error(f"Skill creation job {job_id} failed: {e}")
            # Update job status to failed
            job = await get_job(job_id)
            if job:
                from ..services.jobs import update_job

                await update_job(job_id, {"status": "failed", "error": str(e)})

    # Add workflow to background tasks and return immediately
    background_tasks.add_task(run_workflow)

    return CreateSkillResponse(job_id=job_id, status="pending")


@router.post("/validate", response_model=ValidateSkillResponse)
async def validate_skill_by_path(
    request: ValidateSkillRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
) -> ValidateSkillResponse:
    """
    Validate a skill by path (for drafts or existing skills).

    This endpoint enables CLI validation without requiring a skill_id.
    Supports both published skills and draft skills in _drafts/.
    Uses modern ValidationWorkflow from core for comprehensive validation.

    Args:
        request: Validation request with skill_path and use_llm flag
        skill_service: Injected SkillService for data access

    Returns:
        ValidateSkillResponse: Validation results with detailed feedback

    Raises:
        HTTPException: If skill path not found or validation fails

    """
    from ...core.models import ValidationReport

    try:
        # Resolve skill path safely within skills root
        skills_root = skill_service.taxonomy_manager.skills_root
        try:
            skill_path = resolve_path_within_root(skills_root, request.skill_path)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid skill path: {request.skill_path}",
            ) from e

        if not skill_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Skill path not found: {request.skill_path}",
            )
        if not skill_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Skill path must be a directory: {request.skill_path}",
            )

        # Read SKILL.md content
        skill_md_path = skill_path / "SKILL.md"
        if not skill_md_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"SKILL.md not found in {request.skill_path}",
            )

        skill_content = skill_md_path.read_text(encoding="utf-8")

        # Rule-based validation path for offline/no-LLM mode
        if not request.use_llm:
            validator = SkillValidator(
                skills_root=skills_root,
                taxonomy_manager=skill_service.taxonomy_manager,
            )
            rule_results = validator.validate_complete(skill_path)
            passed = bool(rule_results.get("passed", False))
            raw_checks = rule_results.get("checks", [])
            checks: list[dict[str, str | bool]] = []
            for check in raw_checks if isinstance(raw_checks, list) else []:
                if isinstance(check, dict):
                    checks.append(
                        {
                            "check": str(check.get("name", "")),
                            "passed": check.get("status", "fail") == "pass",
                            "message": "; ".join(check.get("messages", []))
                            if isinstance(check.get("messages"), list)
                            else "",
                        }
                    )

            return ValidateSkillResponse(
                passed=passed,
                status="passed" if passed else "failed",
                score=1.0 if passed else 0.0,
                errors=rule_results.get("errors", []),
                warnings=rule_results.get("warnings", []),
                checks=checks,
            )

        # Use modern ValidationWorkflow
        workflow = ValidationWorkflow()

        # Collect validation events
        validation_report: ValidationReport | None = None
        errors_list: list[str] = []

        async for event in workflow.execute_streaming(
            skill_content=skill_content,
            plan={},  # No plan needed for direct validation
            taxonomy_path=request.skill_path,
            enable_hitl_review=False,
            quality_threshold=0.7,
        ):
            if event.event_type == WorkflowEventType.COMPLETED:
                result = event.data.get("result", {})
                if isinstance(result, dict):
                    report_data = result.get("validation_report", {})
                    if isinstance(report_data, dict):
                        validation_report = ValidationReport.model_validate(report_data)
            elif event.event_type == WorkflowEventType.ERROR:
                errors_list.append(event.data.get("error") or event.message or "Unknown error")

        # If no report generated, create a failure report
        if validation_report is None:
            validation_report = ValidationReport(
                passed=False,
                status="failed",
                score=0.0,
                errors=errors_list or ["Validation workflow did not complete"],
                warnings=[],
                checks=[],
            )

        # Extract validation data from report
        passed = validation_report.passed
        errors = validation_report.errors
        warnings = validation_report.warnings
        checks = [
            {"check": check.check, "passed": check.passed, "message": check.message}
            for check in validation_report.checks
        ]
        score = validation_report.score
        status = validation_report.status

        return ValidateSkillResponse(
            passed=passed,
            status=status,
            score=max(0.0, score),
            errors=errors,
            warnings=warnings,
            checks=checks,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Validation failed for {request.skill_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}") from e


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


@router.put(
    "/{skill_id}",
    response_model=UpdateSkillResponse,
    responses={
        404: {"description": "Skill not found"},
        500: {"description": "Failed to update skill"},
    },
)
async def update_skill(
    skill_id: str,
    request: UpdateSkillRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
) -> UpdateSkillResponse:
    """
    Update an existing skill.

    Args:
        skill_id: Unique skill identifier
        request: Update request with content and/or metadata
        skill_service: Injected SkillService for data access

    Returns:
        UpdateSkillResponse with skill_id and status

    Raises:
        HTTPException: If skill not found (404)

    """
    try:
        # Verify skill exists
        skill_service.get_skill_by_path(skill_id)

        # Resolve the actual filesystem path
        relative_path = skill_service.taxonomy_manager.resolve_skill_location(skill_id)
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

        return UpdateSkillResponse(skill_id=skill_id, status="updated")
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
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
) -> ValidateSkillResponse:
    """
    Validate a skill.

    Args:
        skill_id: Unique skill identifier
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
        taxonomy_path = metadata.get("taxonomy_path") or "general"
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            taxonomy_path=taxonomy_path,
        )

        validation_report = result.get("validation_report", {})

        return ValidateSkillResponse(
            passed=validation_report.get("passed", False),
            status="passed" if validation_report.get("passed", False) else "failed",
            score=validation_report.get("score", 0.0),
            errors=validation_report.get("errors", []),
            warnings=validation_report.get("warnings", []),
            checks=validation_report.get("checks", []),
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
        taxonomy_path = metadata.get("taxonomy_path") or "general"
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            taxonomy_path=taxonomy_path,
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
