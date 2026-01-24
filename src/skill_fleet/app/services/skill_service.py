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

This service uses the workflows layer orchestrators for clean separation of concerns.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...core.models import SkillCreationResult
from ...taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ...workflows import (
        ContentGenerationOrchestrator,
        QualityAssuranceOrchestrator,
        TaskAnalysisOrchestrator,
    )
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
    ) -> SkillCreationResult:
        """
        Create a new skill from a natural language description.

        Uses the workflows layer orchestrators for clean separation of concerns:
        1. TaskAnalysisOrchestrator - Phase 1: Understanding & Planning
        2. ContentGenerationOrchestrator - Phase 2: Content Generation
        3. QualityAssuranceOrchestrator - Phase 3: Validation & Refinement

        Args:
            request: Skill creation request with task description and user ID
            hitl_callback: Optional callback for HITL interactions
            progress_callback: Optional callback for progress updates

        Returns:
            SkillCreationResult: Result of the skill creation workflow

        """
        logger.info("Creating skill for user %s: %s", request.user_id, request.task_description[:100])

        # Provide real taxonomy context
        taxonomy_structure = self.taxonomy_manager.get_relevant_branches(request.task_description)
        mounted_skills = self.taxonomy_manager.get_mounted_skills(request.user_id)

        # Initialize orchestrators
        task_orchestrator = TaskAnalysisOrchestrator()
        content_orchestrator = ContentGenerationOrchestrator()
        qa_orchestrator = QualityAssuranceOrchestrator()

        # Phase 1: Task Analysis & Planning
        if progress_callback:
            progress_callback("phase1", "Analyzing requirements and planning skill structure")

        phase1_result = await task_orchestrator.analyze(
            task_description=request.task_description,
            user_context=request.user_id,
            taxonomy_structure=json.dumps(taxonomy_structure),
            existing_skills=mounted_skills,
            enable_mlflow=True,
        )

        # Phase 2: Content Generation
        if progress_callback:
            progress_callback("phase2", "Generating skill content")

        phase2_result = await content_orchestrator.generate(
            understanding=phase1_result,
            plan=phase1_result.get("plan", {}),
            skill_style="comprehensive",
            enable_mlflow=True,
        )

        # Phase 3: Quality Assurance
        if progress_callback:
            progress_callback("phase3", "Validating and refining skill")

        phase3_result = await qa_orchestrator.validate_and_refine(
            skill_content=phase2_result.get("content", ""),
            skill_metadata=phase1_result.get("plan", {}).get("skill_metadata", {}),
            content_plan=phase1_result.get("plan", {}),
            validation_rules="agentskills.io compliance",
            target_level="intermediate",
            enable_mlflow=True,
        )

        # Construct result from orchestrator outputs
        result = SkillCreationResult(
            status="completed" if phase3_result["validation_report"]["passed"] else "pending_review",
            skill_content=phase2_result.get("content"),
            metadata=phase1_result.get("plan", {}).get("skill_metadata"),
            validation_report=phase3_result.get("validation_report"),
            quality_assessment=phase3_result.get("quality_assessment"),
        )

        return result

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
        from ...api.routes.skills import _save_skill_to_draft

        return _save_skill_to_draft(
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
