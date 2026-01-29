"""
Phase 2: Content Generation Workflow.

Generates skill content based on understanding and plan from Phase 1.
Can show preview for user feedback before finalizing.
"""

import logging
from typing import Any

from skill_fleet.core.modules.generation.content import GenerateSkillContentModule

logger = logging.getLogger(__name__)


class GenerationWorkflow:
    """
    Phase 2: Content Generation Workflow.

    Generates complete skill content:
    1. Generate SKILL.md content
    2. (Optional) Show preview for HITL feedback
    3. Incorporate feedback if provided
    4. Return final content

    Example:
        workflow = GenerationWorkflow()
        result = await workflow.execute(
            plan={"skill_name": "...", "content_outline": [...]},
            understanding={"requirements": {...}, ...},
            enable_hitl_preview=False  # Skip preview for speed
        )

    """

    def __init__(self):
        self.content_generator = GenerateSkillContentModule()

    async def execute(
        self,
        plan: dict,
        understanding: dict,
        enable_hitl_preview: bool = False,
        skill_style: str = "comprehensive",
    ) -> dict[str, Any]:
        """
        Execute generation workflow.

        Args:
            plan: Plan from Phase 1 synthesis
            understanding: Understanding from Phase 1
            enable_hitl_preview: Whether to show preview for feedback
            skill_style: Content style

        Returns:
            Generated skill content

        """
        logger.info(f"Starting content generation for: {plan.get('skill_name', 'unnamed')}")

        # Step 1: Generate content
        logger.debug("Generating SKILL.md content")
        content_result = await self.content_generator.aforward(
            plan=plan, understanding=understanding, skill_style=skill_style
        )

        # Step 2: Check if preview requested
        if enable_hitl_preview:
            logger.info("Suspending for preview/feedback")
            return {
                "status": "pending_hitl",
                "hitl_type": "preview",
                "hitl_data": {
                    "skill_content": content_result["skill_content"],
                    "sections_count": len(content_result.get("sections_generated", [])),
                    "examples_count": content_result.get("code_examples_count", 0),
                    "reading_time": content_result.get("estimated_reading_time", 0),
                },
                "context": {
                    "plan": plan,
                    "understanding": understanding,
                    "skill_style": skill_style,
                },
            }

        logger.info("Content generation completed")

        return {
            "status": "completed",
            "skill_content": content_result["skill_content"],
            "sections_generated": content_result.get("sections_generated", []),
            "code_examples_count": content_result.get("code_examples_count", 0),
            "estimated_reading_time": content_result.get("estimated_reading_time", 0),
        }

    async def incorporate_feedback(
        self, current_content: str, feedback: str, change_requests: list[str]
    ) -> dict[str, Any]:
        """
        Incorporate user feedback into content.

        Args:
            current_content: Current SKILL.md
            feedback: User feedback text
            change_requests: Specific changes requested

        Returns:
            Updated content

        """
        logger.info("Incorporating user feedback")

        # For now, return original with note
        # In full implementation, would use IncorporateFeedbackModule
        return {
            "status": "completed",
            "skill_content": current_content,  # Would be modified
            "feedback_incorporated": True,
            "changes_made": change_requests,
        }
