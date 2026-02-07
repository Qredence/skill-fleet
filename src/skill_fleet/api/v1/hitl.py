"""
HITL (Human-in-the-Loop) routes for v1 API.

This module provides endpoints for human-in-the-loop interaction during
skill creation workflow. These endpoints work with the jobs module
which is shared across API versions.

Endpoints:
    GET  /api/v1/hitl/config - Get HITL configuration for intent detection
    GET  /api/v1/hitl/{job_id}/prompt - Get current HITL prompt for a job
    POST /api/v1/hitl/{job_id}/response - Submit response to HITL prompt
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from skill_fleet.common.logging_utils import sanitize_for_log

from ..dependencies import SkillServiceDep
from ..exceptions import ForbiddenException, NotFoundException
from ..schemas import (
    StructuredQuestion,
    StructureFixSuggestion,
    normalize_questions,
)
from ..services.job_manager import get_job_manager
from ..services.jobs import notify_hitl_response, save_job_session_async

router = APIRouter()

logger = logging.getLogger(__name__)

# Rate limiting for HITL responses (best-effort): prevent duplicate rapid submits.
MIN_HITL_INTERVAL = 1.0  # Minimum seconds between identical responses


def _fingerprint_payload(payload: dict) -> str:
    """Create a stable fingerprint for HITL payloads to detect duplicates."""
    try:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))
    except Exception:
        return repr(payload)


class HITLConfigResponse(BaseModel):
    """
    Response model for HITL configuration endpoint.

    Contains the accepted keywords and patterns for intent detection.
    Enables UI clients to stay in sync with backend HITL configuration.
    """

    action_keywords: dict[str, list[str]] = Field(
        ...,
        description="Keywords for detecting user intent (proceed, revise, cancel)",
    )


class HITLPromptResponse(BaseModel):
    """
    Response model for HITL prompt endpoint.

    This model contains all possible fields across different interaction types.
    Fields are optional since different interaction types use different subsets.
    """

    status: str = Field(..., description="Job status")
    type: str | None = Field(None, description="HITL interaction type")
    current_phase: str | None = Field(None, description="Current workflow phase")
    progress_message: str | None = Field(None, description="Progress message")
    questions: list[StructuredQuestion] | None = Field(None, description="Clarifying questions")
    rationale: str | None = Field(None, description="Rationale for questions")
    summary: str | None = Field(None, description="Understanding summary")
    path: str | None = Field(None, description="Proposed taxonomy path")
    key_assumptions: list[str] | None = Field(None, description="Key assumptions")
    content: str | None = Field(None, description="Preview content")
    highlights: list[str] | None = Field(None, description="Content highlights")
    report: str | None = Field(None, description="Validation report")
    passed: bool | None = Field(None, description="Validation passed")
    skill_content: str | None = Field(None, description="Generated skill content")
    intended_taxonomy_path: str | None = Field(None, description="Intended path")
    draft_path: str | None = Field(None, description="Draft path")
    final_path: str | None = Field(None, description="Final path")
    promoted: bool | None = Field(None, description="Whether promoted")
    saved_path: str | None = Field(None, description="Saved path")
    validation_passed: bool | None = Field(None, description="Validation passed")
    validation_status: str | None = Field(None, description="Validation status")
    validation_score: float | None = Field(None, description="Validation score")
    error: str | None = Field(None, description="Error message")
    question: str | None = Field(None, description="Deep understanding question")
    research_performed: list[Any] | None = Field(None, description="Research performed")
    current_understanding: str | None = Field(None, description="Current understanding")
    readiness_score: float | None = Field(None, description="Readiness score")
    questions_asked: list[Any] | None = Field(None, description="Questions asked")
    # Structure fix fields
    structure_issues: list[str] | None = Field(None, description="Structure validation issues")
    structure_warnings: list[str] | None = Field(
        None, description="Structure improvement suggestions"
    )
    suggested_fixes: list[StructureFixSuggestion] | None = Field(
        None, description="Suggested structure fixes"
    )
    current_skill_name: str | None = Field(None, description="Current skill name")
    current_description: str | None = Field(None, description="Current skill description")


class HITLResponseResult(BaseModel):
    """Response model for HITL response submission."""

    status: str = Field(..., description="Response status (accepted, ignored)")
    detail: str | None = Field(None, description="Additional details")


@router.get("/config")
async def get_hitl_config() -> HITLConfigResponse:
    """
    Retrieve the HITL configuration for intent detection.

    This endpoint provides the keywords and patterns used to detect user intent
    in HITL prompts (proceed, revise, cancel). UI clients should fetch this
    to stay in sync with the backend if configuration changes.

    Returns:
        HITLConfigResponse: Action keywords for intent detection (proceed, revise, cancel)

    """
    return HITLConfigResponse(
        action_keywords={
            "proceed": [
                "proceed",
                "yes",
                "ok",
                "okay",
                "continue",
                "approve",
                "accept",
                "save",
                "y",
            ],
            "revise": ["revise", "change", "edit", "modify", "fix", "update"],
            "cancel": ["cancel", "abort", "stop", "quit", "no", "n"],
        }
    )


@router.get("/{job_id}/prompt")
async def get_prompt(
    job_id: str,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> HITLPromptResponse:
    """
    Retrieve the current HITL prompt for a job.

    Args:
        job_id: The job ID to retrieve the prompt for
        x_user_id: Optional user ID header for ownership verification

    Returns:
        HITLPromptResponse: Current HITL prompt data including questions, content, and status

    Raises:
        NotFoundException: If job not found (404)
        ForbiddenException: If user_id doesn't match the job creator (403)

    """
    manager = get_job_manager()
    job = await manager.get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    # Ownership verification: if a user_id header is provided, it must match
    if isinstance(x_user_id, str) and x_user_id and job.user_id and x_user_id != job.user_id:
        logger.warning(
            "HITL prompt access denied for job %s: user %s != owner %s",
            sanitize_for_log(job_id),
            sanitize_for_log(x_user_id),
            sanitize_for_log(job.user_id),
        )
        raise ForbiddenException(detail=f"User '{x_user_id}' is not the owner of job '{job_id}'")

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    def _get_result_field(result: Any, key: str) -> Any:
        if result is None:
            return None
        if isinstance(result, dict):
            return result.get(key)
        return getattr(result, key, None)

    # Self-heal: some older code paths populate `hitl_type`/`hitl_data` but forget
    # to move the job into a pending-HITL state. Clients rely on status to know
    # when to collect user input, so infer + persist a pending status when we
    # clearly have an unresolved prompt payload.
    def _looks_like_prompt_payload(data: dict[str, Any]) -> bool:
        return any(
            key in data
            for key in (
                "questions",
                "summary",
                "content",
                "highlights",
                "report",
                "issues",
                "warnings",
                "suggested_fixes",
            )
        )

    if (
        job.hitl_type
        and job.status in {"pending", "running"}
        and isinstance(hitl_data, dict)
        and hitl_data
        and _looks_like_prompt_payload(hitl_data)
        and not hitl_data.get("_resolved", False)
    ):
        inferred = (
            "pending_user_input"
            if job.hitl_type in {"clarify", "structure_fix", "deep_understanding"}
            else "pending_hitl"
        )
        if inferred != job.status:
            job.status = inferred
            await manager.update_job(job_id, {"status": inferred})

    # Normalize questions server-side (API-first: CLI is a thin client)
    raw_questions = hitl_data.get("questions")
    normalized_questions = normalize_questions(raw_questions) if raw_questions else None

    # Extract structure fix data if present
    suggested_fixes = hitl_data.get("suggested_fixes", [])
    current_values = hitl_data.get("current_values", {})

    return HITLPromptResponse(
        status=job.status,
        type=job.hitl_type,
        # Progress tracking for CLI display
        current_phase=job.current_phase,
        progress_message=job.progress_message,
        # Phase 1: Clarification (pre-structured for CLI consumption)
        questions=normalized_questions,
        rationale=hitl_data.get("rationale"),
        # Phase 1: Confirmation
        summary=hitl_data.get("summary"),
        path=hitl_data.get("path"),
        key_assumptions=hitl_data.get("key_assumptions"),
        # Phase 2: Preview
        content=hitl_data.get("content"),
        highlights=hitl_data.get("highlights"),
        # Phase 3: Validation
        report=hitl_data.get("report"),
        passed=hitl_data.get("passed"),
        # Result data
        skill_content=_get_result_field(job.result, "skill_content"),
        # Draft-first lifecycle
        intended_taxonomy_path=job.intended_taxonomy_path,
        draft_path=job.draft_path,
        final_path=job.final_path,
        promoted=job.promoted,
        saved_path=job.saved_path,  # Alias of final_path after promotion
        # Validation summary
        validation_passed=job.validation_passed,
        validation_status=job.validation_status,
        validation_score=hitl_data.get("validation_score")
        if isinstance(hitl_data, dict) and hitl_data.get("validation_score") is not None
        else job.validation_score,
        error=job.error,
        # Structure fix fields
        structure_issues=hitl_data.get("issues"),
        structure_warnings=hitl_data.get("warnings"),
        suggested_fixes=suggested_fixes,
        current_skill_name=current_values.get("skill_name"),
        current_description=current_values.get("description"),
    )


@router.post("/{job_id}/response")
async def post_response(
    job_id: str,
    response: dict,
    skill_service: SkillServiceDep,  # noqa: ARG001 - retained for backward compatibility
    x_user_id: str | None = Header(None, alias="X-User-Id"),
) -> HITLResponseResult:
    """
    Submit a response to an HITL prompt.

    The response format depends on the interaction type:
    - clarify: {"answers": {"response": "..."}}
    - confirm/preview/validate: {"action": "proceed|revise|cancel", "feedback": "..."}
    - deep_understanding: {"action": "proceed|cancel", "answer": "...", "problem": "...", "goals": [...]}
    - structure_fix: {"skill_name": "...", "description": "...", "accept_suggestions": true}
    - tdd_*: {"action": "proceed|revise|cancel", "feedback": "..."}

    Args:
        job_id: The job ID to respond to
        response: Response data (format depends on interaction type)
        x_user_id: Optional user ID header for ownership verification

    Returns:
        HITLResponseResult: Response status (accepted/ignored) with optional detail

    Raises:
        NotFoundException: If job not found (404)
        ForbiddenException: If user_id doesn't match the job creator (403)

    """
    manager = get_job_manager()
    job = await manager.get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    # Ownership verification: if a user_id header is provided, it must match
    if isinstance(x_user_id, str) and x_user_id and job.user_id and x_user_id != job.user_id:
        logger.warning(
            "HITL response access denied for job %s: user %s != owner %s",
            sanitize_for_log(job_id),
            sanitize_for_log(x_user_id),
            sanitize_for_log(job.user_id),
        )
        raise ForbiddenException(detail=f"User '{x_user_id}' is not the owner of job '{job_id}'")

    # Ensure lock is initialized (handles loaded sessions)
    if job.hitl_lock is None:
        job.hitl_lock = asyncio.Lock()

    # Use lock to make status check and response assignment atomic
    # This prevents race conditions where status changes between check and assignment
    async with job.hitl_lock:
        # Only accept responses when the job is actively waiting for input. This avoids
        # late/stale responses accidentally being consumed by a future HITL prompt.
        if job.status not in {"pending_user_input", "pending_hitl", "pending_review"}:
            return HITLResponseResult(
                status="ignored", detail=f"No HITL prompt pending (status={job.status})"
            )

        payload = response

        # Duplicate-submit guard: only block identical payloads for the same prompt
        now = datetime.now(UTC).timestamp()
        hitl_data = job.hitl_data or {}
        if isinstance(hitl_data, dict):
            last_fp = hitl_data.get("_last_response_fingerprint")
            last_at = hitl_data.get("_last_response_at", 0.0)
            current_fp = _fingerprint_payload(payload)
            if (
                last_fp == current_fp
                and isinstance(last_at, (int, float))
                and now - float(last_at) < MIN_HITL_INTERVAL
            ):
                logger.warning(
                    "Duplicate HITL response throttled for job %s",
                    sanitize_for_log(job_id),
                )
                return HITLResponseResult(
                    status="ignored",
                    detail=f"Duplicate response ignored. Please wait {MIN_HITL_INTERVAL}s.",
                )

        # Normalize structure_fix responses to ensure skill_name/description are always present
        # when the user chooses "accept suggestions".
        if job.hitl_type == "structure_fix":
            accept_suggestions = bool(payload.get("accept_suggestions", False))
            skill_name = payload.get("skill_name")
            description = payload.get("description")

            if accept_suggestions:
                hitl_data = job.hitl_data or {}
                if isinstance(hitl_data, dict):
                    suggested_fixes = hitl_data.get("suggested_fixes", []) or []
                    for fix in suggested_fixes:
                        if not isinstance(fix, dict):
                            continue
                        if fix.get("field") == "skill_name" and not skill_name:
                            skill_name = fix.get("suggested")
                        if fix.get("field") == "description" and not description:
                            description = fix.get("suggested")

            payload = {
                "skill_name": skill_name,
                "description": description,
                "accept_suggestions": accept_suggestions,
            }

        # Store the response (also used by session persistence)
        job.hitl_response = payload

        # Immediately release any in-flight waiter so the background job can resume.
        await notify_hitl_response(job_id, payload)

        # Update status eagerly so polling clients don't re-render the same prompt.
        job.status = "running"

        # Mark prompt as resolved for self-heal logic in GET /prompt.
        hitl_data = job.hitl_data or {}
        if isinstance(hitl_data, dict):
            hitl_data["_resolved"] = True
            hitl_data["_resolved_at"] = datetime.now(UTC).isoformat()
            hitl_data["_last_response_fingerprint"] = _fingerprint_payload(payload)
            hitl_data["_last_response_at"] = now
            job.hitl_data = hitl_data

        await manager.update_job(
            job_id,
            {"status": "running", "hitl_data": job.hitl_data, "hitl_response": payload},
        )

    # Auto-save session on each HITL response
    try:
        success = await save_job_session_async(job_id)
        if not success:
            logger.warning("Failed to save session for job %s", sanitize_for_log(job_id))
    except Exception:
        logger.exception("Unexpected error saving session for job %s", sanitize_for_log(job_id))

    return HITLResponseResult(status="accepted")
