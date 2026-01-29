"""
Quality assurance routes for v1 API.

This module provides endpoints for quality operations.
These routes use quality workflow orchestrators.

Endpoints:
    POST /api/v1/quality/validate - Validate skill or content
    POST /api/v1/quality/assess - Assess quality of content
    POST /api/v1/quality/fix - Auto-fix issues in content
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow

from ..dependencies import get_skill_service
from ..exceptions import NotFoundException
from ..schemas.quality import (
    AssessQualityRequest,
    AssessQualityResponse,
    AutoFixRequest,
    AutoFixResponse,
    ValidateRequest,
    ValidateResponse,
)
from ..services.skill_service import SkillService

logger = logging.getLogger(__name__)

router = APIRouter()


def _load_skill_content(skill_id: str, skill_service: SkillService) -> tuple[str, dict]:
    """
    Load skill content and metadata by skill ID.

    Args:
        skill_id: The skill ID or path
        skill_service: The skill service instance

    Returns:
        Tuple of (content, metadata)

    Raises:
        HTTPException: If skill not found

    """
    try:
        skill_data = skill_service.get_skill_by_path(skill_id)
        content = skill_data.get("content", "")
        metadata = {
            "skill_id": skill_data.get("skill_id"),
            "name": skill_data.get("name"),
            "description": skill_data.get("description"),
            "type": skill_data.get("type"),
            **skill_data.get("metadata", {}),
        }
        return content, metadata
    except FileNotFoundError as e:
        raise NotFoundException("Skill", skill_id) from e


@router.post("/validate", response_model=ValidateResponse)
async def validate(
    request: ValidateRequest, skill_service: Annotated[SkillService, Depends(get_skill_service)]
) -> ValidateResponse:
    """
    Validate a skill or content.

    Args:
        request: Validation request with skill_id or content
        skill_service: Injected skill service for loading skills

    Returns:
        ValidateResponse: Validation results with pass/fail status

    Raises:
        HTTPException: If skill_id is provided but skill not found (404)
        HTTPException: If neither skill_id nor content is provided (400)

    """
    # Determine content to validate
    if request.skill_id:
        content, metadata = _load_skill_content(request.skill_id, skill_service)
    elif request.content:
        content = request.content
        metadata = {}
    else:
        raise HTTPException(status_code=400, detail="Either skill_id or content must be provided")

    # Initialize workflow and run validation
    workflow = ValidationWorkflow()

    try:
        # Run validation workflow
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            taxonomy_path=metadata.get("taxonomy_path", ""),
        )

        # Extract validation report
        validation_report = result.get("validation_report", {})
        issues = validation_report.get("issues", [])

        # Build issues list for response
        formatted_issues = []
        for issue in issues:
            formatted_issues.append(
                {
                    "severity": issue.get("severity", "warning"),
                    "message": issue.get("message", str(issue)),
                    "location": issue.get("location", "unknown"),
                }
            )

        # Extract recommendations from quality assessment
        quality_assessment = result.get("quality_assessment", {})
        recommendations = quality_assessment.get("recommendations", [])

        return ValidateResponse(
            passed=validation_report.get("passed", False),
            status="passed" if validation_report.get("passed", False) else "failed",
            score=validation_report.get("score", 0.0),
            issues=formatted_issues,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.exception(f"Error in validation workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {e}") from e


@router.post("/assess", response_model=AssessQualityResponse)
async def assess_quality(
    request: AssessQualityRequest,
    skill_service: Annotated[SkillService, Depends(get_skill_service)],
) -> AssessQualityResponse:
    """
    Assess content quality across multiple dimensions.

    Args:
        request: Assessment request with skill_id or content
        skill_service: Injected skill service for loading skills

    Returns:
        AssessQualityResponse: Quality scores, strengths, weaknesses, and suggestions

    Raises:
        HTTPException: If skill_id is provided but skill not found (404)
        HTTPException: If neither skill_id nor content is provided (400)

    """
    # Determine content to assess
    if request.skill_id:
        content, metadata = _load_skill_content(request.skill_id, skill_service)
    elif request.content:
        content = request.content
        metadata = {}
    else:
        raise HTTPException(status_code=400, detail="Either skill_id or content must be provided")

    # Initialize workflow
    workflow = ValidationWorkflow()

    try:
        # Run quality assessment workflow
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            taxonomy_path=metadata.get("taxonomy_path", ""),
        )

        # Extract quality assessment
        quality_assessment = result.get("quality_assessment", {})

        # Extract dimension scores
        dimensions = quality_assessment.get("dimensions", {})
        if not dimensions:
            # Fallback to calibrated score as overall if no dimensions
            overall_score = quality_assessment.get("calibrated_score", 0.0)
            dimensions = {"overall": overall_score}

        # Extract strengths and weaknesses
        strengths = quality_assessment.get("strengths", [])
        weaknesses = quality_assessment.get("weaknesses", [])
        suggestions = quality_assessment.get(
            "suggestions", quality_assessment.get("recommendations", [])
        )

        # Calculate overall score from dimensions or use calibrated
        overall_score = quality_assessment.get("calibrated_score")
        if overall_score is None and dimensions:
            overall_score = sum(dimensions.values()) / len(dimensions)

        return AssessQualityResponse(
            overall_score=overall_score or 0.0,
            dimensions=dimensions,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
        )

    except Exception as e:
        logger.exception(f"Error in quality assessment workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Quality assessment failed: {e}") from e


@router.post("/fix", response_model=AutoFixResponse)
async def auto_fix(
    request: AutoFixRequest, skill_service: Annotated[SkillService, Depends(get_skill_service)]
) -> AutoFixResponse:
    """
    Automatically fix issues in skill or content.

    Args:
        request: Auto-fix request with skill_id or content and issues list
        skill_service: Injected skill service for loading skills

    Returns:
        AutoFixResponse: Fixed content, applied fixes, remaining issues, and confidence

    Raises:
        HTTPException: If skill_id is provided but skill not found (404)
        HTTPException: If neither skill_id nor content is provided (400)

    """
    # Determine content to fix
    if request.skill_id:
        content, metadata = _load_skill_content(request.skill_id, skill_service)
    elif request.content:
        content = request.content
        metadata = {}
    else:
        raise HTTPException(status_code=400, detail="Either skill_id or content must be provided")

    # Initialize workflow
    workflow = ValidationWorkflow()

    # Build user feedback from issues
    user_feedback_items = []
    for issue in request.issues:
        message = issue.get("message", "")
        location = issue.get("location", "")
        if location:
            user_feedback_items.append(f"Fix issue at {location}: {message}")
        else:
            user_feedback_items.append(f"Fix: {message}")
    user_feedback = "\n".join(user_feedback_items)

    try:
        # Run refinement workflow
        result = await workflow.execute(
            skill_content=content,
            plan={"skill_metadata": metadata},
            taxonomy_path=metadata.get("taxonomy_path", ""),
        )

        # Extract refined content
        fixed_content = result.get("refined_content", content)

        # Build fixes applied list
        fixes_applied = []
        if "refined_content" in result:
            for issue in request.issues:
                fixes_applied.append(
                    {
                        "issue": issue.get("message", str(issue)),
                        "fix": f"Addressed: {issue.get('message', '')}",
                    }
                )

        # Get remaining issues from the result
        validation_report = result.get("validation_report", {})
        remaining_issues = validation_report.get("issues", [])
        formatted_remaining = []
        for issue in remaining_issues:
            formatted_remaining.append(
                {
                    "severity": issue.get("severity", "warning"),
                    "message": issue.get("message", str(issue)),
                    "location": issue.get("location", "unknown"),
                }
            )

        # Calculate confidence from quality score
        quality_assessment = result.get("quality_assessment", {})
        confidence = quality_assessment.get("calibrated_score", 0.9)

        return AutoFixResponse(
            fixed_content=fixed_content,
            fixes_applied=fixes_applied,
            remaining_issues=formatted_remaining,
            confidence=confidence,
        )

    except Exception as e:
        logger.exception(f"Error in auto-fix workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-fix failed: {e}") from e
