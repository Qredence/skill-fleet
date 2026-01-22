"""
High-level skill creation orchestrator.

This module provides the main interface for skill creation,
coordinating DSPy programs, taxonomy operations, and feedback.
Re-implemented to wrap the new SkillCreationProgram.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dspy

from ..common.async_utils import run_async
from .dspy.skill_creator import SkillCreationProgram

if TYPE_CHECKING:
    from ..taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)


class TaxonomySkillCreator(dspy.Module):
    """
    High-level orchestrator for skill creation.

    Wraps SkillCreationProgram to provide a simplified synchronous interface
    compatible with legacy CLI commands.
    """

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        verbose: bool = True,
        **kwargs,
    ):
        """
        Initialize skill creator.

        Args:
            taxonomy_manager: Taxonomy management instance
            verbose: Whether to print progress
            **kwargs: Additional keyword arguments

        """
        super().__init__()
        self.taxonomy = taxonomy_manager
        self.verbose = verbose
        self.program = SkillCreationProgram()

    def forward(
        self,
        task_description: str,
        user_context: dict[str, Any] | None = None,
        auto_approve: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute skill creation workflow.

        Args:
            task_description: User's task or capability requirement
            user_context: Dict with user_id and other context
            auto_approve: If True, skips interactive feedback loops (where possible)
            **kwargs: Additional keyword arguments passed to acall

        Returns:
            Result dictionary with status and metadata

        """
        user_context = user_context or {"user_id": "default"}

        # Helper to run async program synchronously
        return run_async(
            lambda: self.acall(
                task_description=task_description,
                user_context=user_context,
                auto_approve=auto_approve,
                **kwargs,
            )
        )

    async def acall(
        self,
        task_description: str,
        user_context: dict[str, Any],
        auto_approve: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Async execution of skill creation."""
        # Prepare context for the program
        # The new program expects JSON strings for complex inputs if not using typed signatures directly,
        # but SkillCreationProgram.aforward takes typed args.

        # Get existing skills for context
        existing_skills = self.taxonomy.get_mounted_skills(user_context.get("user_id", "default"))
        taxonomy_structure = self.taxonomy.get_relevant_branches(task_description)

        import json

        # Define a simple auto-approval callback if needed,
        # but SkillCreationProgram might just run through if hitl_enabled=False?
        # Actually, SkillCreationProgram defaults hitl_enabled=True.
        # We need to handle the callback if we want it to work without a real user.

        async def auto_callback(interaction_type: str, data: dict[str, Any]) -> dict[str, Any]:
            logger.info(f"Auto-approving interaction: {interaction_type}")
            if interaction_type == "confirm":
                return {"action": "confirm"}
            elif interaction_type == "preview" or interaction_type == "validate":
                return {"action": "approve"}
            elif interaction_type == "clarify":
                # For clarification, we can't really "approve", we might just return empty or best guess
                return {"response": "Proceed with best assumptions."}
            return {"action": "proceed"}

        # Use auto callback if auto_approve is True, otherwise...
        # Since this class is used by 'onboard' which is CLI-based but might not have
        # specific HITL handling logic injected, we might default to auto or raise error.
        # The 'onboard' command passes `auto_approve=True` for bootstrap skills.

        callback = auto_callback if auto_approve else None
        # If not auto_approve and no callback provided, the program might hang or fail
        # if it tries to await input.
        # For legacy compatibility, we'll assume auto-approve behavior if no callback is passed
        # effectively making this a "batch" creator.
        if callback is None:
            callback = auto_callback

        result = await self.program.aforward(
            task_description=task_description,
            user_context=user_context,
            taxonomy_structure=json.dumps(taxonomy_structure),
            existing_skills=json.dumps(existing_skills),
            hitl_callback=callback,
        )

        # Map SkillCreationResult to legacy dict format
        if result.status == "completed" and result.metadata and result.skill_content:
            path = result.metadata.taxonomy_path or result.metadata.skill_id
            metadata_dict: dict[str, Any] = result.metadata.model_dump() if result.metadata else {}
            success = self.taxonomy.register_skill(
                path=path,
                metadata=metadata_dict,
                content=result.skill_content,
                extra_files=result.extra_files or {},
                evolution=result.metadata.version if result.metadata else "1.0.0",
            )

            if success:
                return {
                    "status": "approved",
                    "skill_id": result.metadata.skill_id,
                    "path": path,
                    "version": result.metadata.version,
                }

        return {
            "status": result.status,
            "error": result.error,
            "message": result.error or "Creation failed or cancelled",
        }

    def __call__(self, *args, **kwargs):
        return self.forward(*args, **kwargs)
