"""DSPy modules for Phase 3: Validation & Refinement."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import dspy

from ....common.async_utils import run_async
from ..signatures.phase3_validation import (
    AssessSkillQuality,
    RefineSkillFromFeedback,
    ValidateSkill,
)

logger = logging.getLogger(__name__)


class SkillValidatorModule(dspy.Module):
    """Validate a draft skill against quality and compliance rules."""

    def __init__(self):
        super().__init__()
        self.validate = dspy.Predict(ValidateSkill)

    def forward(
        self,
        skill_content: str,
        skill_metadata: Any,
        content_plan: str,
        validation_rules: str,
    ) -> dict[str, Any]:
        """Validate skill content against rules and requirements.

        Args:
            skill_content: The SKILL.md content to validate
            skill_metadata: Skill metadata for context
            content_plan: Original content plan for comparison
            validation_rules: Validation rules and criteria

        Returns:
            dict: Validation report with issues, warnings, suggestions, and score
        """
        result = self.validate(
            skill_content=skill_content,
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            validation_rules=validation_rules,
        )
        return {
            "validation_report": result.validation_report,
            "critical_issues": result.critical_issues,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "overall_score": result.overall_score,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async wrapper for skill validation.

        Args:
            *args: Positional arguments passed to forward method
            **kwargs: Keyword arguments passed to forward method

        Returns:
            dict: Validation report from async execution
        """
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class SkillRefinerModule(dspy.Module):
    """Refine a draft skill based on validation feedback."""

    def __init__(self):
        super().__init__()
        self.refine = dspy.ChainOfThought(RefineSkillFromFeedback)

    def forward(
        self,
        current_content: str,
        validation_issues: str,
        user_feedback: str,
        fix_strategies: str,
        iteration_number: int = 1,
    ) -> dict[str, Any]:
        """Refine skill content based on validation feedback.

        Args:
            current_content: Current skill content to refine
            validation_issues: Issues identified during validation
            user_feedback: User feedback for improvement
            fix_strategies: Suggested strategies for fixing issues
            iteration_number: Current refinement iteration

        Returns:
            dict: Refined content with improvements and change summary
        """
        result = self.refine(
            current_content=current_content,
            validation_issues=validation_issues,
            user_feedback=user_feedback,
            fix_strategies=fix_strategies,
            iteration_number=iteration_number,
        )
        return {
            "refined_content": result.refined_content,
            "issues_resolved": result.issues_resolved,
            "issues_remaining": result.issues_remaining,
            "changes_summary": result.changes_summary,
            "ready_for_acceptance": result.ready_for_acceptance,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async wrapper for skill refinement."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class QualityAssessorModule(dspy.Module):
    """Assess skill quality and audience alignment."""

    def __init__(self):
        super().__init__()
        self.assess = dspy.ChainOfThought(AssessSkillQuality)

    def forward(self, skill_content: str, skill_metadata: Any, target_level: str) -> dict[str, Any]:
        """Assess the overall quality of skill content.

        Args:
            skill_content: The SKILL.md content to assess
            skill_metadata: Skill metadata for context
            target_level: Target complexity level (beginner, intermediate, advanced)

        Returns:
            dict: Quality assessment with score, level, strengths, and areas for improvement
        """
        result = self.assess(
            skill_content=skill_content,
            skill_metadata=skill_metadata,
            target_level=target_level,
        )
        return {
            "quality_score": result.quality_score,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": result.recommendations,
            "audience_alignment": result.audience_alignment,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async wrapper for quality assessment."""
        return await asyncio.to_thread(self.forward, *args, **kwargs)


class Phase3ValidationModule(dspy.Module):
    """Phase 3 orchestrator: validate, refine, and assess quality."""

    def __init__(self):
        super().__init__()
        self.validator = SkillValidatorModule()
        self.refiner = SkillRefinerModule()
        self.quality_assessor = QualityAssessorModule()

    async def aforward(
        self,
        skill_content: str,
        skill_metadata: Any,
        content_plan: str,
        validation_rules: str,
        user_feedback: str = "",
        target_level: str = "intermediate",
    ) -> dict[str, Any]:
        """Async orchestration of Phase 3 validation, refinement, and quality assessment.

        Args:
            skill_content: The SKILL.md content to validate and refine
            skill_metadata: Skill metadata for context
            content_plan: Original content plan for comparison
            validation_rules: Validation rules and criteria
            user_feedback: Optional user feedback for refinement
            target_level: Target complexity level (beginner, intermediate, advanced)

        Returns:
            dict: Comprehensive validation results with quality assessment
        """
        validation_result = await self.validator.aforward(
            skill_content=skill_content,
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            validation_rules=validation_rules,
        )
        if not validation_result["validation_report"].passed or user_feedback:
            refinement_result = await self.refiner.aforward(
                current_content=skill_content,
                validation_issues=str(validation_result["validation_report"]),
                user_feedback=user_feedback,
                fix_strategies="{}",
            )
            validation_result["refined_content"] = refinement_result["refined_content"]
        else:
            validation_result["refined_content"] = skill_content
        quality_result = await self.quality_assessor.aforward(
            skill_content=validation_result["refined_content"],
            skill_metadata=skill_metadata,
            target_level=target_level,
        )
        return {
            **validation_result,
            "quality_assessment": quality_result,
        }

    def forward(self, *args, **kwargs) -> dict[str, Any]:
        """Sync version of Phase 3 validation orchestration.

        Args:
            *args: Positional arguments passed to aforward method
            **kwargs: Keyword arguments passed to aforward method

        Returns:
            dict: Comprehensive validation results with quality assessment
        """
        return run_async(lambda: self.aforward(*args, **kwargs))
