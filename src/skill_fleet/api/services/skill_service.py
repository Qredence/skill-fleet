"""
FastAPI service layer for skill creation operations.

This service bridges FastAPI routes to the skill creation workflow orchestrators.
It provides a clean API for skill creation, validation, and refinement operations.

The service layer handles:
- Creating skills from natural language descriptions
- Managing skill creation jobs (async background tasks)
- Saving skills to draft area
- Retrieving skill metadata
- Validating and refining skills
- Hierarchical MLflow tracking with parent runs and child runs for each phase

This service uses the workflows layer orchestrators for clean separation of concerns.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from skill_fleet.core.workflows.skill_creation.generation import GenerationWorkflow
from skill_fleet.core.workflows.skill_creation.understanding import UnderstandingWorkflow
from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow
from skill_fleet.core.workflows.streaming import StreamingWorkflowManager
from skill_fleet.infrastructure.tracing.mlflow import (
    end_parent_run,
    log_quality_metrics,
    log_skill_artifacts,
    log_tags,
    log_validation_results,
    start_child_run,
    start_parent_run,
)
from skill_fleet.taxonomy.manager import TaxonomyManager

from ...core.models import SkillCreationResult, ValidationReport
from ..schemas.models import JobState
from ..services.jobs import wait_for_hitl_response
from .event_registry import get_event_registry
from .job_manager import get_job_manager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pathlib import Path

    from ..schemas.skills import CreateSkillRequest


class SkillService:
    """Service for managing skill creation operations."""

    def __init__(
        self,
        skills_root: Path,
        drafts_root: Path,
    ):
        """
        Initialize skill service.

        Args:
            skills_root: Root directory for skills taxonomy
            drafts_root: Root directory for draft skills

        """
        self.skills_root = skills_root
        self.drafts_root = drafts_root
        self.taxonomy_manager = TaxonomyManager(skills_root)
        self.understanding_workflow = UnderstandingWorkflow()
        self.generation_workflow = GenerationWorkflow()
        self.validation_workflow = ValidationWorkflow()

    async def create_skill(
        self,
        request: CreateSkillRequest,
        existing_job_id: str | None = None,
        hitl_callback: Any | None = None,
        progress_callback: Any | None = None,
        enable_mlflow: bool = True,
    ) -> SkillCreationResult:
        """
        Create a new skill from a natural language description.

        Uses the workflows layer orchestrators for clean separation of concerns:
        1. TaskAnalysisOrchestrator - Phase 1: Understanding & Planning
        2. ContentGenerationOrchestrator - Phase 2: Content Generation
        3. QualityAssuranceOrchestrator - Phase 3: Validation & Refinement

        This method creates a hierarchical MLflow structure with:
        - Parent run for the entire skill creation workflow
        - Child runs for each phase (task analysis, content generation, quality assurance)
        - Complete artifacts logged at the parent level

        Args:
            request: Skill creation request with task description and user ID
            existing_job_id: Optional ID of existing job to resume
            hitl_callback: Optional callback for HITL interactions
            progress_callback: Optional callback for progress updates
            enable_mlflow: Whether to track with MLflow (default: True)

        Returns:
            SkillCreationResult: Result of the skill creation workflow

        """
        job_manager = get_job_manager()

        if existing_job_id:
            job_id = existing_job_id
            job = await job_manager.get_job(job_id)
            if not job:
                # Should not happen in resume flow
                job_id = existing_job_id
        else:
            job_id = str(uuid.uuid4())
            # Create job state
            job_state = JobState(
                job_id=job_id,
                task_description=request.task_description,
                user_id=request.user_id,
                status="running",
            )
            await job_manager.create_job(job_state)

        logger.info(
            "Creating skill for user %s: %s (Job ID: %s)",
            request.user_id,
            request.task_description[:100],
            job_id,
        )

        # Register event queue for real-time streaming
        event_registry = get_event_registry()
        event_queue = await event_registry.register(job_id)
        streaming_manager = StreamingWorkflowManager(event_queue=event_queue)
        logger.debug(f"Registered event queue for job {job_id}")

        async def _set_hitl_state(
            *,
            status: str,
            hitl_type: str,
            hitl_data: dict[str, Any],
        ) -> None:
            job_local = await job_manager.get_job(job_id)
            if not job_local:
                return
            job_local.status = status
            job_local.hitl_type = hitl_type
            job_local.hitl_data = hitl_data
            await job_manager.update_job(
                job_id,
                {
                    "status": status,
                    "hitl_type": hitl_type,
                    "hitl_data": hitl_data,
                    "current_phase": job_local.current_phase,
                },
            )

        async def _clear_hitl_state() -> None:
            job_local = await job_manager.get_job(job_id)
            if not job_local:
                return
            if isinstance(job_local.hitl_data, dict):
                job_local.hitl_data["_resolved"] = True
            job_local.status = "running"
            await job_manager.update_job(
                job_id, {"status": "running", "hitl_data": job_local.hitl_data}
            )

        # Check for previous answers to inject into context
        previous_answers: dict[str, Any] = {}
        job = await job_manager.get_job(job_id)
        if job and job.deep_understanding.answers:
            previous_answers = {"prior_clarifications": job.deep_understanding.answers}

        # Provide real taxonomy context
        taxonomy_structure = self.taxonomy_manager.get_relevant_branches(request.task_description)
        mounted_skills = self.taxonomy_manager.get_mounted_skills(request.user_id)

        # Use workflows initialized in __init__
        understanding_workflow = self.understanding_workflow
        generation_workflow = self.generation_workflow
        validation_workflow = self.validation_workflow

        # Start MLflow parent run for hierarchical tracking
        parent_run_id = None
        if enable_mlflow:
            # Extract skill type from request if available, otherwise None
            skill_type = getattr(request, "skill_type", None)
            parent_run_id = start_parent_run(
                run_name=request.task_description[:100],
                user_id=request.user_id,
                job_id=job_id,
                skill_type=skill_type,
                description=f"Skill creation: {request.task_description[:200]}",
            )

        try:
            # Build user context dict (persist structure_fix overrides in job.user_context).
            job = await job_manager.get_job(job_id)
            base_context = (job.user_context if job else {}) or {}
            user_context = {"user_id": request.user_id, **base_context, **previous_answers}

            # Track whether we should auto-save a draft at the end.
            save_draft_requested = False

            # ------------------------------------------------------------------
            # Phase 1: Understanding (+ optional clarify/structure_fix + confirm)
            # ------------------------------------------------------------------
            if progress_callback:
                progress_callback("phase1", "Analyzing requirements and planning skill structure")

            user_confirmation = ""
            phase1_result: dict[str, Any] | None = None

            while True:
                if enable_mlflow:
                    with start_child_run("phase1_task_analysis"):
                        phase1_result = await understanding_workflow.execute(
                            task_description=request.task_description,
                            user_context=user_context,
                            taxonomy_structure=taxonomy_structure,
                            existing_skills=mounted_skills,
                            enable_hitl_confirm=bool(
                                getattr(request, "enable_hitl_confirm", False)
                            ),
                            user_confirmation=user_confirmation,
                            manager=streaming_manager,
                        )
                else:
                    phase1_result = await understanding_workflow.execute(
                        task_description=request.task_description,
                        user_context=user_context,
                        taxonomy_structure=taxonomy_structure,
                        existing_skills=mounted_skills,
                        enable_hitl_confirm=bool(getattr(request, "enable_hitl_confirm", False)),
                        user_confirmation=user_confirmation,
                        manager=streaming_manager,
                    )

                status = phase1_result.get("status")
                if status not in {"pending_user_input", "pending_hitl"}:
                    break

                hitl_type = str(phase1_result.get("hitl_type") or "clarify")
                raw_hitl_data = phase1_result.get("hitl_data")
                hitl_data: dict[str, Any] = raw_hitl_data if isinstance(raw_hitl_data, dict) else {}

                pending_status = (
                    "pending_user_input"
                    if hitl_type in {"clarify", "structure_fix"}
                    else "pending_hitl"
                )
                await _set_hitl_state(
                    status=pending_status, hitl_type=hitl_type, hitl_data=hitl_data
                )

                response = await wait_for_hitl_response(job_id)
                await _clear_hitl_state()

                # Apply response depending on HITL type.
                action = str(response.get("action") or "").strip().lower()
                if action == "cancel":
                    return SkillCreationResult(
                        job_id=job_id, status="cancelled", message="Cancelled by user"
                    )

                if hitl_type == "confirm":
                    if action in {"", "proceed", "accept", "ok", "okay", "yes"}:
                        break
                    if action == "revise":
                        user_confirmation = str(response.get("feedback") or "")
                        continue
                    # Unknown -> proceed
                    break

                if hitl_type == "structure_fix":
                    # Store structure overrides for future requirements runs.
                    fixed_name = response.get("skill_name")
                    fixed_desc = response.get("description")
                    if job:
                        override = dict(job.user_context or {})
                        override["structure_fix"] = {
                            "skill_name": fixed_name or "",
                            "description": fixed_desc or "",
                        }
                        job.user_context = override
                        await job_manager.update_job(job_id, {"user_context": override})
                        user_context = {"user_id": request.user_id, **override, **previous_answers}
                    continue

                # clarify: append response to deep_understanding.answers for future context
                if job:
                    job.deep_understanding.answers.append(response)
                    await job_manager.update_job(
                        job_id, {"deep_understanding": job.deep_understanding}
                    )
                    user_context = {
                        "user_id": request.user_id,
                        **(job.user_context or {}),
                        "prior_clarifications": job.deep_understanding.answers,
                    }
                continue

            assert phase1_result is not None

            # ------------------------------------------------------------------
            # Phase 2: Generation (+ optional preview/refine)
            # ------------------------------------------------------------------
            if progress_callback:
                progress_callback("phase2", "Generating skill content")

            plan = (
                phase1_result.get("plan", {}) if isinstance(phase1_result.get("plan"), dict) else {}
            )
            understanding_payload = phase1_result
            current_content: str = ""

            while True:
                if enable_mlflow:
                    with start_child_run("phase2_content_generation"):
                        phase2_result = await generation_workflow.execute(
                            plan=plan,
                            understanding=understanding_payload,
                            enable_hitl_preview=bool(
                                getattr(request, "enable_hitl_preview", False)
                            ),
                            enable_token_streaming=bool(
                                getattr(request, "enable_token_streaming", False)
                            ),
                            manager=streaming_manager,
                        )
                else:
                    phase2_result = await generation_workflow.execute(
                        plan=plan,
                        understanding=understanding_payload,
                        enable_hitl_preview=bool(getattr(request, "enable_hitl_preview", False)),
                        enable_token_streaming=bool(
                            getattr(request, "enable_token_streaming", False)
                        ),
                        manager=streaming_manager,
                    )

                status = phase2_result.get("status")
                if status == "completed":
                    current_content = str(phase2_result.get("skill_content") or "")
                    break

                if status == "pending_hitl" and phase2_result.get("hitl_type") == "preview":
                    hitl_data = phase2_result.get("hitl_data", {})
                    if isinstance(hitl_data, dict):
                        # Ensure expected shape for API clients.
                        hitl_data.setdefault(
                            "content", current_content or hitl_data.get("content") or ""
                        )
                        hitl_data.setdefault("highlights", hitl_data.get("highlights") or [])

                    await _set_hitl_state(
                        status="pending_hitl", hitl_type="preview", hitl_data=hitl_data
                    )
                    response = await wait_for_hitl_response(job_id)
                    await _clear_hitl_state()

                    action = str(response.get("action") or "proceed").strip().lower()
                    if action == "cancel":
                        return SkillCreationResult(
                            job_id=job_id, status="cancelled", message="Cancelled by user"
                        )
                    if action == "refine":
                        feedback = str(response.get("feedback") or "").strip()
                        if feedback and isinstance(hitl_data, dict):
                            base = str(hitl_data.get("content") or current_content or "")
                            incorporated = await generation_workflow.incorporate_feedback(
                                base, feedback, [feedback]
                            )
                            current_content = str(incorporated.get("skill_content") or base)
                        # Re-show preview by looping generation with enable_hitl_preview=True but without regenerating:
                        # To keep things simple, directly re-suspend with updated content.
                        preview_data = {
                            "content": current_content,
                            "highlights": generation_workflow.extract_highlights(current_content),
                        }
                        await _set_hitl_state(
                            status="pending_hitl", hitl_type="preview", hitl_data=preview_data
                        )
                        response2 = await wait_for_hitl_response(job_id)
                        await _clear_hitl_state()
                        action2 = str(response2.get("action") or "proceed").strip().lower()
                        if action2 == "cancel":
                            return SkillCreationResult(
                                job_id=job_id, status="cancelled", message="Cancelled by user"
                            )
                        if action2 == "refine":
                            # Keep looping; feedback handled on next iteration.
                            continue
                        if bool(getattr(request, "auto_save_draft_on_preview_confirm", False)):
                            save_draft_requested = True
                        break
                    # proceed
                    if bool(getattr(request, "auto_save_draft_on_preview_confirm", False)):
                        save_draft_requested = True
                    current_content = str(hitl_data.get("content") or current_content or "")
                    break

                # Unknown state; break and treat as failure.
                break

            # ------------------------------------------------------------------
            # Phase 3: Validation (+ optional validate/refine)
            # ------------------------------------------------------------------
            if progress_callback:
                progress_callback("phase3", "Validating and refining skill")

            taxonomy_path = str(plan.get("taxonomy_path") or "")
            final_content = current_content
            phase3_result: dict[str, Any] = {}

            while True:
                if enable_mlflow:
                    with start_child_run("phase3_quality_assurance"):
                        phase3_result = await validation_workflow.execute(
                            skill_content=final_content,
                            plan=plan,
                            taxonomy_path=taxonomy_path,
                            enable_hitl_review=bool(getattr(request, "enable_hitl_review", False)),
                            manager=streaming_manager,
                        )
                else:
                    phase3_result = await validation_workflow.execute(
                        skill_content=final_content,
                        plan=plan,
                        taxonomy_path=taxonomy_path,
                        enable_hitl_review=bool(getattr(request, "enable_hitl_review", False)),
                        manager=streaming_manager,
                    )

                if (
                    phase3_result.get("status") == "pending_hitl"
                    and phase3_result.get("hitl_type") == "validate"
                ):
                    hitl_data = phase3_result.get("hitl_data", {})
                    if not isinstance(hitl_data, dict):
                        hitl_data = {}
                    await _set_hitl_state(
                        status="pending_hitl", hitl_type="validate", hitl_data=hitl_data
                    )
                    response = await wait_for_hitl_response(job_id)
                    await _clear_hitl_state()

                    action = str(response.get("action") or "proceed").strip().lower()
                    if action == "cancel":
                        return SkillCreationResult(
                            job_id=job_id, status="cancelled", message="Cancelled by user"
                        )
                    if action == "refine":
                        feedback = str(response.get("feedback") or "").strip()
                        if feedback:
                            incorporated = await generation_workflow.incorporate_feedback(
                                final_content, feedback, [feedback]
                            )
                            final_content = str(incorporated.get("skill_content") or final_content)
                        continue
                    break

                break

            # Construct result from workflow outputs
            raw_validation_report = (
                phase3_result.get("validation_report") if isinstance(phase3_result, dict) else None
            )
            validation_report: ValidationReport | None = None
            passed = False
            if isinstance(raw_validation_report, dict):
                try:
                    validation_report = ValidationReport.model_validate(
                        raw_validation_report, strict=False
                    )
                    passed = validation_report.passed
                except Exception as exc:
                    logger.warning("Invalid validation report format for job %s: %s", job_id, exc)
                    # Fall back to dict's passed field if available
                    passed = raw_validation_report.get("passed", False)

            result = SkillCreationResult(
                job_id=job_id,
                status="completed" if passed else "pending_review",
                skill_content=final_content,
                metadata=plan.get("skill_metadata"),
                validation_report=validation_report,
                quality_assessment=phase3_result.get("quality_assessment")
                if isinstance(phase3_result, dict)
                else None,
            )

            # Save to draft if requested
            if save_draft_requested and result.status in {"completed", "pending_review"}:
                draft_path = await self.save_skill_to_draft(job_id, result)
                if draft_path:
                    job = await job_manager.get_job(job_id)
                    if job:
                        job.draft_path = draft_path
                        job.intended_taxonomy_path = taxonomy_path
                        await job_manager.update_job(
                            job_id,
                            {
                                "draft_path": draft_path,
                                "intended_taxonomy_path": taxonomy_path,
                            },
                        )

            # Log final artifacts at parent level
            if enable_mlflow and parent_run_id:
                skill_metadata = plan.get("skill_metadata", {})

                # Log skill type tag if available
                if skill_metadata.get("type"):
                    log_tags({"skill_type": skill_metadata["type"]})

                # Log validation results as metrics and artifact
                validation_report = phase3_result.get("validation_report", {})
                if validation_report:
                    log_validation_results(validation_report)

                # Log quality assessment metrics
                quality_assessment = phase3_result.get("quality_assessment", {})
                if quality_assessment:
                    log_quality_metrics(quality_assessment)

                # Log complete skill artifacts
                log_skill_artifacts(
                    content=final_content,
                    metadata=skill_metadata,
                    validation_report=validation_report,
                    quality_assessment=quality_assessment,
                )

            # Persist terminal job state for callers that invoke SkillService directly
            # (the API route also does this, but keeping it here avoids hanging streams
            # if a caller forgets to update JobState after awaiting create_skill()).
            await job_manager.update_job(
                job_id,
                {
                    "status": result.status,
                    "result": result,
                    "progress_percent": 100.0,
                    "progress_message": "Skill creation completed",
                    "validation_passed": passed,
                    "validation_score": (
                        validation_report.get("score")
                        if isinstance(validation_report, dict)
                        and validation_report.get("score") is not None
                        else None
                    ),
                },
            )

            return result

        finally:
            # Unregister event queue
            await event_registry.unregister(job_id)
            # End parent run
            if enable_mlflow and parent_run_id:
                end_parent_run()

    async def resume_skill_creation(
        self, job_id: str, answers: dict[str, Any]
    ) -> SkillCreationResult:
        """
        Resume skill creation with HITL answers.

        Args:
            job_id: ID of the suspended job
            answers: User answers to clarification questions

        Returns:
            SkillCreationResult

        """
        job_manager = get_job_manager()
        job = await job_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Update answers in DeepUnderstandingState (append as record)
        job.deep_understanding.answers.append(answers)

        job.status = "running"
        await job_manager.update_job(
            job_id, {"status": "running", "deep_understanding": job.deep_understanding}
        )

        # Re-construct request from stored job state
        from ..schemas.skills import CreateSkillRequest

        request = CreateSkillRequest(task_description=job.task_description, user_id=job.user_id)

        try:
            result = await self.create_skill(request, existing_job_id=job_id)
        except Exception as exc:
            await job_manager.update_job(job_id, {"status": "failed", "error": str(exc)})
            raise

        if result.status in {"completed", "pending_review"}:
            await job_manager.update_job(
                job_id,
                {
                    "status": result.status,
                    "result": result,
                    "progress_percent": 100.0,
                    "progress_message": "Skill creation completed",
                },
            )
        elif result.status in {"failed", "cancelled"}:
            await job_manager.update_job(
                job_id,
                {"status": result.status, "error": result.error or result.message},
            )

        return result

    async def save_skill_to_draft(
        self,
        job_id: str,
        result: SkillCreationResult,
    ) -> str | None:
        """
        Save a completed skill to the draft area.

        Args:
            job_id: Unique job identifier
            result: SkillCreationResult from workflow

        Returns:
            Path where draft skill was saved, or None if save failed

        """
        from ..utils.draft_save import save_skill_to_draft

        return await save_skill_to_draft(
            drafts_root=self.drafts_root,
            job_id=job_id,
            result=result,
        )

    def get_skill_by_path(self, path: str) -> dict[str, Any]:
        """
        Get details for a skill by its path or ID.

        Args:
            path: Skill path or ID

        Returns:
            Dictionary with skill details

        Raises:
            FileNotFoundError: If skill not found

        """
        # Resolve location (handles aliases + legacy paths via manager)
        canonical_path = self.taxonomy_manager.resolve_skill_location(path)

        # Load metadata
        meta = self.taxonomy_manager.get_skill_metadata(canonical_path)
        if not meta:
            meta = self.taxonomy_manager._try_load_skill_by_id(canonical_path)

        if not meta:
            raise FileNotFoundError(f"Skill not found: {path}")

        # Load content
        content = None
        if meta.path.name == "metadata.json":
            md_path = meta.path.parent / "SKILL.md"
            if md_path.exists():
                content = md_path.read_text(encoding="utf-8")

        # Convert dataclass to dict for response
        return {
            "skill_id": meta.skill_id,
            "name": meta.name,
            "description": meta.description,
            "version": meta.version,
            "type": meta.type,
            "metadata": {
                "weight": meta.weight,
                "load_priority": meta.load_priority,
                "dependencies": meta.dependencies,
                "capabilities": meta.capabilities,
                "always_loaded": meta.always_loaded,
            },
            "content": content,
        }
