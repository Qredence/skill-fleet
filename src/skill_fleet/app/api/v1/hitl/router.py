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
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ....exceptions import NotFoundException
from ....schemas import StructuredQuestion, normalize_questions
from ....services.job_manager import get_job_manager
from ....services.jobs import notify_hitl_response

router = APIRouter()


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
async def get_prompt(job_id: str) -> HITLPromptResponse:
    """
    Retrieve the current HITL prompt for a job.

    Args:
        job_id: The job ID to retrieve the prompt for

    Returns:
        HITLPromptResponse: Current HITL prompt data including questions, content, and status

    Raises:
        NotFoundException: If job not found (404)

    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    # Normalize questions server-side (API-first: CLI is a thin client)
    raw_questions = hitl_data.get("questions")
    normalized_questions = normalize_questions(raw_questions) if raw_questions else None

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
        skill_content=job.result.skill_content if job.result else None,
        # Draft-first lifecycle
        intended_taxonomy_path=job.intended_taxonomy_path,
        draft_path=job.draft_path,
        final_path=job.final_path,
        promoted=job.promoted,
        saved_path=job.saved_path,  # Alias of final_path after promotion
        # Validation summary
        validation_passed=job.validation_passed,
        validation_status=job.validation_status,
        validation_score=job.validation_score,
        error=job.error,
    )


@router.post("/{job_id}/response")
async def post_response(job_id: str, response: dict) -> HITLResponseResult:
    """
    Submit a response to an HITL prompt.

    The response format depends on the interaction type:
    - clarify: {"answers": {"response": "..."}}
    - confirm/preview/validate: {"action": "proceed|revise|cancel", "feedback": "..."}
    - deep_understanding: {"action": "proceed|cancel", "answer": "...", "problem": "...", "goals": [...]}
    - tdd_*: {"action": "proceed|revise|cancel", "feedback": "..."}

    Args:
        job_id: The job ID to respond to
        response: Response data (format depends on interaction type)

    Returns:
        HITLResponseResult: Response status (accepted/ignored) with optional detail

    Raises:
        NotFoundException: If job not found (404)

    """
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    # Ensure lock is initialized (handles loaded sessions)
    if job.hitl_lock is None:
        job.hitl_lock = asyncio.Lock()

    # Use lock to make status check and response assignment atomic
    # This prevents race conditions where status changes between check and assignment
    async with job.hitl_lock:
        # Only accept responses when the job is actively waiting for HITL. This avoids
        # late/stale responses accidentally being consumed by a *future* HITL prompt.
        if job.status != "pending_hitl":
            return HITLResponseResult(
                status="ignored", detail=f"No HITL prompt pending (status={job.status})"
            )

        # Store the response
        job.hitl_response = response

        # Immediately release any in-flight waiter so the background job can resume.
        notify_hitl_response(job_id, response)

        # Update status eagerly so polling clients don't re-render the same prompt.
        job.status = "running"

    # Auto-save session on each HITL response
    from ....services.jobs import save_job_session

    save_job_session(job_id)

    return HITLResponseResult(status="accepted")
