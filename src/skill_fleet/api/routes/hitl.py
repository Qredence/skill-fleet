"""HITL interaction routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..jobs import get_job, notify_hitl_response

router = APIRouter()


@router.get("/{job_id}/prompt")
async def get_prompt(job_id: str):
    """Retrieve the current HITL prompt for a job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Extract all possible HITL data fields
    hitl_data = job.hitl_data or {}

    response = {
        "status": job.status,
        "type": job.hitl_type,
        # Phase 1: Clarification
        "questions": hitl_data.get("questions"),
        "rationale": hitl_data.get("rationale"),
        # Phase 1: Confirmation
        "summary": hitl_data.get("summary"),
        "path": hitl_data.get("path"),
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

    return response


@router.post("/{job_id}/response")
async def post_response(job_id: str, response: dict):
    """Submit a response to an HITL prompt."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Only accept responses when the job is actively waiting for HITL. This avoids
    # late/stale responses accidentally being consumed by a *future* HITL prompt.
    if job.status != "pending_hitl":
        return {"status": "ignored", "detail": f"No HITL prompt pending (status={job.status})"}

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

    return {"status": "accepted"}
