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

from ....api.job_manager import get_job_manager
from ....api.jobs import notify_hitl_response
from ....api.schemas import StructuredQuestion, normalize_questions
from ....api.exceptions import NotFoundException

router = APIRouter()


class HITLConfigResponse:
    """
    Response model for HITL configuration endpoint.

    Contains the accepted keywords and patterns for intent detection.
    Enables UI clients to stay in sync with backend HITL configuration.
    """
    def __init__(self, action_keywords: dict[str, list[str]]):
        self.action_keywords = action_keywords


class HITLPromptResponse:
    """
    Response model for HITL prompt endpoint.

    This model contains all possible fields across different interaction types.
    Fields are optional since different interaction types use different subsets.
    """
    def __init__(
        self,
        status: str,
        type: str | None = None,
        current_phase: str | None = None,
        progress_message: str | None = None,
        questions: list[StructuredQuestion] | None = None,
        rationale: str | None = None,
        summary: str | None = None,
        path: str | None = None,
        key_assumptions: list[str] | None = None,
        content: str | None = None,
        highlights: list[str] | None = None,
        report: str | None = None,
        passed: bool | None = None,
        skill_content: str | None = None,
        intended_taxonomy_path: str | None = None,
        draft_path: str | None = None,
        final_path: str | None = None,
        promoted: bool | None = None,
        saved_path: str | None = None,
        validation_passed: bool | None = None,
        validation_status: str | None = None,
        validation_score: float | None = None,
        error: str | None = None,
        # Deep understanding fields
        question: str | None = None,
        research_performed: list[Any] | None = None,
        current_understanding: str | None = None,
        readiness_score: float | None = None,
        questions_asked: list[Any] | None = None,
    ):
        self.status = status
        self.type = type
        self.current_phase = current_phase
        self.progress_message = progress_message
        self.questions = questions
        self.rationale = rationale
        self.summary = summary
        self.path = path
        self.key_assumptions = key_assumptions
        self.content = content
        self.highlights = highlights
        self.report = report
        self.passed = passed
        self.skill_content = skill_content
        self.intended_taxonomy_path = intended_taxonomy_path
        self.draft_path = draft_path
        self.final_path = final_path
        self.promoted = promoted
        self.saved_path = saved_path
        self.validation_passed = validation_passed
        self.validation_status = validation_status
        self.validation_score = validation_score
        self.error = error
        self.question = question
        self.research_performed = research_performed
        self.current_understanding = current_understanding
        self.readiness_score = readiness_score
        self.questions_asked = questions_asked


class HITLResponseResult:
    """Response model for HITL response submission."""
    def __init__(self, status: str, detail: str | None = None):
        self.status = status
        self.detail = detail


@router.get("/config")
async def get_hitl_config() -> HITLConfigResponse:
    """
    Retrieve the HITL configuration for intent detection.

    This endpoint provides the keywords and patterns used to detect user intent
    in HITL prompts (proceed, revise, cancel). UI clients should fetch this
    to stay in sync with the backend if configuration changes.

    Returns:
        HITLConfigResponse with action keywords for intent detection

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
    """Retrieve the current HITL prompt for a job."""
    manager = get_job_manager()
    job = manager.get_job(job_id)
    if not job:
        raise NotFoundException("Job", job_id)

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    # Normalize questions server-side (API-first: CLI is a thin client)
    raw_questions = hitl_data.get("questions")
    normalized_questions = normalize_questions(raw_questions) if raw_questions else None

    response = HITLPromptResponse(
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

    return response


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
        HITLResponseResult indicating if response was accepted or ignored

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
    from ....api.jobs import save_job_session

    save_job_session(job_id)

    return HITLResponseResult(status="accepted")
