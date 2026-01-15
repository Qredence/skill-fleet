"""HITL interaction routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..jobs import get_job, notify_hitl_response
from ..schemas import StructuredQuestion, normalize_questions

router = APIRouter()


class HITLPromptResponse(BaseModel):
    """Response model for HITL prompt endpoint.

    This model contains all possible fields across different interaction types.
    Fields are optional since different interaction types use different subsets.
    """

    # Core status fields
    status: str = Field(
        ..., description="Job status (pending, running, pending_hitl, completed, failed)"
    )
    type: str | None = Field(
        default=None,
        description="HITL interaction type (clarify, confirm, preview, validate, etc.)",
    )

    # Progress tracking for CLI display
    current_phase: str | None = Field(
        default=None, description="Current workflow phase (understanding, generation, validation)"
    )
    progress_message: str | None = Field(
        default=None, description="Detailed progress message for CLI display"
    )

    # Phase 1: Clarification (questions are normalized server-side for thin client)
    questions: list[StructuredQuestion] | None = Field(
        default=None,
        description="Clarifying questions for the user (pre-structured for CLI consumption)",
    )
    rationale: str | None = Field(default=None, description="Rationale for asking questions")

    # Phase 1: Confirmation
    summary: str | None = Field(default=None, description="Understanding summary for confirmation")
    path: str | None = Field(default=None, description="Proposed taxonomy path")
    key_assumptions: list[str] | None = Field(
        default=None, description="Key assumptions made during understanding"
    )

    # Phase 2: Preview
    content: str | None = Field(default=None, description="Preview content")
    highlights: list[str] | None = Field(default=None, description="Content highlights")

    # Phase 3: Validation
    report: str | None = Field(default=None, description="Validation report")
    passed: bool | None = Field(default=None, description="Whether validation passed")

    # Result data
    skill_content: str | None = Field(default=None, description="Generated skill content")

    # Draft-first lifecycle
    intended_taxonomy_path: str | None = Field(
        default=None, description="Intended path in taxonomy"
    )
    draft_path: str | None = Field(default=None, description="Path to draft skill")
    final_path: str | None = Field(default=None, description="Final path after promotion")
    promoted: bool | None = Field(default=None, description="Whether draft was promoted")
    saved_path: str | None = Field(default=None, description="Alias of final_path")

    # Validation summary
    validation_passed: bool | None = Field(default=None, description="Overall validation result")
    validation_status: str | None = Field(default=None, description="Validation status string")
    validation_score: float | None = Field(default=None, description="Validation score")
    error: str | None = Field(default=None, description="Error message if failed")

    # Deep understanding fields
    question: str | None = Field(default=None, description="Current deep understanding question")
    research_performed: list[Any] | None = Field(default=None, description="Research performed")
    current_understanding: str | None = Field(
        default=None, description="Current understanding summary"
    )
    readiness_score: float | None = Field(default=None, description="Readiness score")
    questions_asked: list[Any] | None = Field(default=None, description="Questions already asked")

    # TDD red phase fields
    test_requirements: str | None = Field(default=None, description="Test requirements")
    acceptance_criteria: list[str] | None = Field(default=None, description="Acceptance criteria")
    checklist_items: list[Any] | None = Field(default=None, description="TDD checklist items")
    rationalizations_identified: list[str] | None = Field(
        default=None, description="Identified rationalizations"
    )

    # TDD green phase fields
    failing_test: str | None = Field(default=None, description="Currently failing test")
    test_location: str | None = Field(default=None, description="Test file location")
    minimal_implementation_hint: str | None = Field(default=None, description="Implementation hint")
    phase: str | None = Field(default=None, description="Current TDD phase")

    # TDD refactor phase fields
    refactor_opportunities: list[str] | None = Field(
        default=None, description="Refactoring opportunities"
    )
    code_smells: list[str] | None = Field(default=None, description="Detected code smells")
    coverage_report: str | None = Field(default=None, description="Test coverage report")


class HITLResponseResult(BaseModel):
    """Response model for HITL response submission."""

    status: str = Field(..., description="Response status (accepted, ignored)")
    detail: str | None = Field(default=None, description="Additional details")


@router.get("/{job_id}/prompt", response_model=HITLPromptResponse)
async def get_prompt(job_id: str) -> HITLPromptResponse:
    """Retrieve the current HITL prompt for a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    # Normalize questions server-side (API-first: CLI is a thin client)
    raw_questions = hitl_data.get("questions")
    normalized_questions = normalize_questions(raw_questions) if raw_questions else None

    response = {
        "status": job.status,
        "type": job.hitl_type,
        # Progress tracking for CLI display
        "current_phase": job.current_phase,
        "progress_message": job.progress_message,
        # Phase 1: Clarification (pre-structured for CLI consumption)
        "questions": normalized_questions,
        "rationale": hitl_data.get("rationale"),
        # Phase 1: Confirmation
        "summary": hitl_data.get("summary"),
        "path": hitl_data.get("path"),
        "key_assumptions": hitl_data.get("key_assumptions"),
        # Phase 2: Preview
        "content": hitl_data.get("content"),
        "highlights": hitl_data.get("highlights"),
        # Phase 3: Validation
        "report": hitl_data.get("report"),
        "passed": hitl_data.get("passed"),
        # Result data
        "skill_content": job.result.skill_content if job.result else None,
        # Draft-first lifecycle
        "intended_taxonomy_path": job.intended_taxonomy_path,
        "draft_path": job.draft_path,
        "final_path": job.final_path,
        "promoted": job.promoted,
        "saved_path": job.saved_path,  # Alias of final_path after promotion
        # Validation summary
        "validation_passed": job.validation_passed,
        "validation_status": job.validation_status,
        "validation_score": job.validation_score,
        "error": job.error,
    }

    # Add deep_understanding interaction type data
    if job.hitl_type == "deep_understanding":
        response.update(
            {
                "question": hitl_data.get("question"),
                "research_performed": job.deep_understanding.research_performed,
                "current_understanding": job.deep_understanding.understanding_summary,
                "readiness_score": job.deep_understanding.readiness_score,
                "questions_asked": job.deep_understanding.questions_asked,
            }
        )

    # Add TDD red phase interaction type data
    if job.hitl_type == "tdd_red":
        response.update(
            {
                "test_requirements": hitl_data.get("test_requirements"),
                "acceptance_criteria": hitl_data.get("acceptance_criteria"),
                "checklist_items": hitl_data.get("checklist_items"),
                "rationalizations_identified": job.tdd_workflow.rationalizations_identified,
            }
        )

    # Add TDD green phase interaction type data
    if job.hitl_type == "tdd_green":
        response.update(
            {
                "failing_test": hitl_data.get("failing_test"),
                "test_location": hitl_data.get("test_location"),
                "minimal_implementation_hint": hitl_data.get("minimal_implementation_hint"),
                "phase": job.tdd_workflow.phase,
            }
        )

    # Add TDD refactor phase interaction type data
    if job.hitl_type == "tdd_refactor":
        response.update(
            {
                "refactor_opportunities": hitl_data.get("refactor_opportunities"),
                "code_smells": hitl_data.get("code_smells"),
                "coverage_report": hitl_data.get("coverage_report"),
                "phase": job.tdd_workflow.phase,
            }
        )

    return HITLPromptResponse(**response)


@router.post("/{job_id}/response", response_model=HITLResponseResult)
async def post_response(job_id: str, response: dict) -> HITLResponseResult:
    """Submit a response to an HITL prompt.

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
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

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

    # Update deep_understanding state if provided
    if job.hitl_type == "deep_understanding":
        if "answer" in response:
            job.deep_understanding.answers.append(
                {
                    "question_id": response.get("question_id"),
                    "answer": response["answer"],
                }
            )
        if "problem" in response:
            job.deep_understanding.user_problem = response["problem"]
        if "goals" in response:
            job.deep_understanding.user_goals = response["goals"]
        if "readiness_score" in response:
            job.deep_understanding.readiness_score = response["readiness_score"]
        if "complete" in response:
            job.deep_understanding.complete = response["complete"]
        if "understanding_summary" in response:
            job.deep_understanding.understanding_summary = response["understanding_summary"]

    # Update TDD workflow state if provided
    if job.hitl_type in ("tdd_red", "tdd_green", "tdd_refactor"):
        if "phase" in response:
            job.tdd_workflow.phase = response["phase"]
        if "rationalizations" in response:
            job.tdd_workflow.rationalizations_identified = response["rationalizations"]
        if "baseline_tests_run" in response:
            job.tdd_workflow.baseline_tests_run = response["baseline_tests_run"]
        if "compliance_tests_run" in response:
            job.tdd_workflow.compliance_tests_run = response["compliance_tests_run"]

    # Auto-save session on each HITL response
    from ..jobs import save_job_session

    save_job_session(job_id)

    return HITLResponseResult(status="accepted")
