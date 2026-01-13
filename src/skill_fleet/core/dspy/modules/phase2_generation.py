"""DSPy modules for Phase 2: Content Generation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dspy

from ....common.async_utils import run_async
from ..signatures.phase2_generation import (
    GenerateSkillContent,
    IncorporateFeedback,
)

logger = logging.getLogger(__name__)


class ContentGeneratorModule(dspy.Module):
    """Generate initial skill content from the Phase 1 plan."""

    def __init__(self, quality_assured: bool = True):
        super().__init__()
        # For simplicity, using ChainOfThought. BestOfN requires a reward function.
        self.quality_assured = quality_assured
        self.generate = dspy.ChainOfThought(GenerateSkillContent)

    def forward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
    ) -> dict[str, Any]:
        """Generate skill content based on metadata and planning.

        Args:
            skill_metadata: Skill metadata including name, description, etc.
            content_plan: Structured plan for the skill content
            generation_instructions: Specific instructions for content generation
            parent_skills_content: Content from parent skills in taxonomy
            dependency_summaries: Summaries of skill dependencies

        Returns:
            dict: Generated content including skill_content, usage_examples,
                  best_practices, test_cases, estimated_reading_time, and rationale
        """
        result = self.generate(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=generation_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )
        return {
            "skill_content": result.skill_content,
            "usage_examples": result.usage_examples,
            "best_practices": result.best_practices,
            "test_cases": result.test_cases,
            "estimated_reading_time": result.estimated_reading_time,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async wrapper for content generation.

        Args:
            *args: Positional arguments passed to forward method
            **kwargs: Keyword arguments passed to forward method

        Returns:
            dict: Generated content from async execution
        """
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class FeedbackIncorporatorModule(dspy.Module):
    """Apply user feedback and change requests to draft content."""

    def __init__(self):
        super().__init__()
        self.incorporate = dspy.ChainOfThought(IncorporateFeedback)

    def forward(
        self,
        current_content: str,
        user_feedback: str,
        change_requests: str,
        skill_metadata: Any,
    ) -> dict[str, Any]:
        """Incorporate user feedback into existing skill content.

        Args:
            current_content: Current skill content to be refined
            user_feedback: User's feedback and comments
            change_requests: Specific change requests from user
            skill_metadata: Skill metadata for context

        Returns:
            dict: Refined content including refined_content, changes_made, and rationale
        """
        result = self.incorporate(
            current_content=current_content,
            user_feedback=user_feedback,
            change_requests=change_requests,
            skill_metadata=skill_metadata,
        )
        return {
            "refined_content": result.refined_content,
            "changes_made": result.changes_made,
            "unaddressed_feedback": result.unaddressed_feedback,
            "improvement_score": result.improvement_score,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async wrapper for feedback incorporation."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class Phase2GenerationModule(dspy.Module):
    """Phase 2 orchestrator: generate content and optionally incorporate feedback."""

    def __init__(self, quality_assured: bool = True):
        super().__init__()
        self.generate_content = ContentGeneratorModule(quality_assured=quality_assured)
        self.incorporate_feedback = FeedbackIncorporatorModule()

    async def aforward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
        user_feedback: str = "",
        change_requests: str = "",
    ) -> dict[str, Any]:
        """Async orchestration of Phase 2 content generation and feedback incorporation.

        Args:
            skill_metadata: Skill metadata including name, description, etc.
            content_plan: Structured plan for the skill content
            generation_instructions: Specific instructions for content generation
            parent_skills_content: Content from parent skills in taxonomy
            dependency_summaries: Summaries of skill dependencies
            user_feedback: Optional user feedback for refinement
            change_requests: Optional specific change requests

        Returns:
            dict: Final generated content with all metadata
        """
        content_result = await self.generate_content.aforward(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=generation_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )
        if user_feedback or change_requests:
            refinement_result = await self.incorporate_feedback.aforward(
                current_content=content_result["skill_content"],
                user_feedback=user_feedback,
                change_requests=change_requests,
                skill_metadata=skill_metadata,
            )
            content_result["skill_content"] = refinement_result["refined_content"]
            content_result["changes_made"] = refinement_result["changes_made"]
            content_result["improvement_score"] = refinement_result["improvement_score"]
        return content_result

    def forward(self, *args, **kwargs) -> dict[str, Any]:
        """Sync version of Phase 2 content generation orchestration.

        Args:
            *args: Positional arguments passed to aforward method
            **kwargs: Keyword arguments passed to aforward method

        Returns:
            dict: Final generated content with all metadata
        """
        return run_async(lambda: self.aforward(*args, **kwargs))
