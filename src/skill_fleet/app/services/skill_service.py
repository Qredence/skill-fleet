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

import json
import logging
from typing import TYPE_CHECKING, Any

from ...core.dspy.modules.workflows import (
    ContentGenerationOrchestrator,
    QualityAssuranceOrchestrator,
    TaskAnalysisOrchestrator,
)
from ...core.models import SkillCreationResult
from ...core.tracing.mlflow import (
    end_parent_run,
    log_quality_metrics,
    log_skill_artifacts,
    log_tags,
    log_validation_results,
    start_child_run,
    start_parent_run,
)
from ...taxonomy.manager import TaxonomyManager

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

    async def create_skill(
        self,
        request: CreateSkillRequest,
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
            hitl_callback: Optional callback for HITL interactions
            progress_callback: Optional callback for progress updates
            enable_mlflow: Whether to track with MLflow (default: True)

        Returns:
            SkillCreationResult: Result of the skill creation workflow

        """
        logger.info(
            "Creating skill for user %s: %s", request.user_id, request.task_description[:100]
        )

        # Provide real taxonomy context
        taxonomy_structure = self.taxonomy_manager.get_relevant_branches(request.task_description)
        mounted_skills = self.taxonomy_manager.get_mounted_skills(request.user_id)

        # Initialize orchestrators
        task_orchestrator = TaskAnalysisOrchestrator()
        content_orchestrator = ContentGenerationOrchestrator()
        qa_orchestrator = QualityAssuranceOrchestrator()

        # Start MLflow parent run for hierarchical tracking
        parent_run_id = None
        if enable_mlflow:
            # Extract skill type from request if available, otherwise None
            skill_type = getattr(request, "skill_type", None)
            parent_run_id = start_parent_run(
                run_name=request.task_description[:100],
                user_id=request.user_id,
                job_id=getattr(request, "job_id", None),
                skill_type=skill_type,
                description=f"Skill creation: {request.task_description[:200]}",
            )

        try:
            # Phase 1: Task Analysis & Planning
            if progress_callback:
                progress_callback("phase1", "Analyzing requirements and planning skill structure")

            if enable_mlflow:
                # Use child run for phase 1 - orchestrator will skip setup_mlflow_experiment
                with start_child_run("phase1_task_analysis"):
                    phase1_result = await task_orchestrator.analyze(
                        task_description=request.task_description,
                        user_context=request.user_id,
                        taxonomy_structure=json.dumps(taxonomy_structure),
                        existing_skills=mounted_skills,
                        enable_mlflow=False,  # Don't start separate run, we're in child run
                    )
            else:
                phase1_result = await task_orchestrator.analyze(
                    task_description=request.task_description,
                    user_context=request.user_id,
                    taxonomy_structure=json.dumps(taxonomy_structure),
                    existing_skills=mounted_skills,
                    enable_mlflow=False,
                )

            # Phase 2: Content Generation
            if progress_callback:
                progress_callback("phase2", "Generating skill content")

            if enable_mlflow:
                with start_child_run("phase2_content_generation"):
                    phase2_result = await content_orchestrator.generate(
                        understanding=phase1_result,
                        plan=phase1_result.get("plan", {}),
                        skill_style="comprehensive",
                        enable_mlflow=False,
                    )
            else:
                phase2_result = await content_orchestrator.generate(
                    understanding=phase1_result,
                    plan=phase1_result.get("plan", {}),
                    skill_style="comprehensive",
                    enable_mlflow=False,
                )

            # Phase 3: Quality Assurance
            if progress_callback:
                progress_callback("phase3", "Validating and refining skill")

            if enable_mlflow:
                with start_child_run("phase3_quality_assurance"):
                    phase3_result = await qa_orchestrator.validate_and_refine(
                        skill_content=phase2_result.get("skill_content", ""),
                        skill_metadata=phase1_result.get("plan", {}).get("skill_metadata", {}),
                        content_plan=phase1_result.get("plan", {}),
                        validation_rules="agentskills.io compliance",
                        target_level="intermediate",
                        enable_mlflow=False,
                    )
            else:
                phase3_result = await qa_orchestrator.validate_and_refine(
                    skill_content=phase2_result.get("skill_content", ""),
                    skill_metadata=phase1_result.get("plan", {}).get("skill_metadata", {}),
                    content_plan=phase1_result.get("plan", {}),
                    validation_rules="agentskills.io compliance",
                    target_level="intermediate",
                    enable_mlflow=False,
                )

            # Construct result from orchestrator outputs
            result = SkillCreationResult(
                status="completed"
                if phase3_result["validation_report"]["passed"]
                else "pending_review",
                skill_content=phase2_result.get("skill_content"),
                metadata=phase1_result.get("plan", {}).get("skill_metadata"),
                validation_report=phase3_result.get("validation_report"),
                quality_assessment=phase3_result.get("quality_assessment"),
            )

            # Log final artifacts at parent level
            if enable_mlflow and parent_run_id:
                skill_metadata = phase1_result.get("plan", {}).get("skill_metadata", {})

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
                    content=phase2_result.get("skill_content"),
                    metadata=skill_metadata,
                    validation_report=validation_report,
                    quality_assessment=quality_assessment,
                )

            return result

        finally:
            # End parent run
            if enable_mlflow and parent_run_id:
                end_parent_run()

    def save_skill_to_draft(
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

        return save_skill_to_draft(
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
