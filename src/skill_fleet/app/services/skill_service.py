"""FastAPI service layer for skill creation operations.

This service bridges FastAPI routes to the skill creation workflow orchestrators.
It provides a clean API for skill creation, validation, and refinement operations.

The service layer handles:
- Creating skills from natural language descriptions
- Managing skill creation jobs (async background tasks)
- Saving skills to draft area
- Retrieving skill metadata
- Validating and refining skills
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ...core.dspy import SkillCreationProgram
from ...core.models import SkillCreationResult
from ...taxonomy.manager import TaxonomyManager
from ...common.security import sanitize_taxonomy_path
from ..schemas.skills import CreateSkillRequest, CreateSkillResponse

logger = logging.getLogger(__name__)


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

        Args:
            request: Skill creation request with task description and user ID
            hitl_callback: Optional callback for HITL interactions
            progress_callback: Optional callback for progress updates

        Returns:
            SkillCreationResult: Result of the skill creation workflow
        """
        logger.info("Creating skill for user %s: %s", request.user_id, request.task_description[:100])

        # Provide real taxonomy context to Phase 1 (better path selection + overlap analysis)
        taxonomy_structure = self.taxonomy_manager.get_relevant_branches(request.task_description)
        mounted_skills = self.taxonomy_manager.get_mounted_skills(request.user_id)

        program = SkillCreationProgram()
        result = await program.aforward(
            task_description=request.task_description,
            user_context={"user_id": request.user_id},
            taxonomy_structure=json.dumps(taxonomy_structure),
            existing_skills=json.dumps(mounted_skills),
            hitl_callback=hitl_callback,
            progress_callback=progress_callback,
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
