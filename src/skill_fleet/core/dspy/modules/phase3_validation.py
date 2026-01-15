"""DSPy modules for Phase 3: Validation & Refinement."""

from __future__ import annotations

import logging
from typing import Any

import dspy
import yaml

from ....common.async_utils import run_async
from ..metrics import assess_skill_quality
from ..signatures.phase3_validation import (
    AssessSkillQuality,
    RefineSkillFromFeedback,
    ValidateSkill,
)

logger = logging.getLogger(__name__)


def _canonicalize_skill_md_frontmatter(skill_content: str, skill_metadata: Any) -> str:
    """Rebuild YAML frontmatter from SkillMetadata, stripping any existing frontmatter.

    Why: the LLM sometimes edits frontmatter fields (notably version), causing
    validation drift (content != metadata.json/SkillMetadata). We treat
    `skill_metadata` as source-of-truth so validation matches what we will
    later write to disk during registration.
    """

    if not skill_content or not skill_content.strip():
        return skill_content

    meta: dict[str, Any] = {}
    if isinstance(skill_metadata, dict):
        meta = skill_metadata
    elif hasattr(skill_metadata, "model_dump"):
        # Pydantic v2 BaseModel
        meta = skill_metadata.model_dump()  # type: ignore[assignment]
    elif hasattr(skill_metadata, "dict"):
        # Pydantic v1 BaseModel
        meta = skill_metadata.dict()  # type: ignore[assignment]

    name = str(meta.get("name", "")).strip()
    description = str(meta.get("description", "")).strip()
    if not name or not description:
        return skill_content

    # Strip existing frontmatter if present
    content = skill_content.lstrip("\ufeff")
    body_content = content
    if content.startswith("---"):
        lines = content.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            closing_index = None
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    closing_index = i
                    break
            if closing_index is not None:
                body_content = "".join(lines[closing_index + 1 :]).lstrip("\n")
            else:
                # Invalid frontmatter (no closing marker) — drop the opening delimiter.
                body_content = "".join(lines[1:]).lstrip("\n")

    # Build frontmatter (keep in sync with TaxonomyManager._generate_skill_md_with_frontmatter)
    frontmatter: dict[str, Any] = {
        "name": name,
        "description": description[:1024],
    }

    extended_meta: dict[str, Any] = {}
    skill_id = str(meta.get("skill_id", "")).strip()
    if skill_id:
        extended_meta["skill_id"] = skill_id
    version = str(meta.get("version", "")).strip()
    if version:
        extended_meta["version"] = version
    skill_type = str(meta.get("type", "")).strip()
    if skill_type:
        extended_meta["type"] = skill_type
    weight = str(meta.get("weight", "")).strip()
    if weight:
        extended_meta["weight"] = weight

    if extended_meta:
        frontmatter["metadata"] = extended_meta

    yaml_content = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{yaml_content}---\n\n{body_content}"


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

    async def aforward(
        self,
        skill_content: str,
        skill_metadata: Any,
        content_plan: str,
        validation_rules: str,
    ) -> dict[str, Any]:
        """Async wrapper for skill validation (preferred)."""
        result = await self.validate.acall(
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

    async def aforward(
        self,
        current_content: str,
        validation_issues: str,
        user_feedback: str,
        fix_strategies: str,
        iteration_number: int = 1,
    ) -> dict[str, Any]:
        """Async wrapper for skill refinement (preferred)."""
        result = await self.refine.acall(
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


class QualityAssessorModule(dspy.Module):
    """Assess skill quality and audience alignment.

    Combines LLM-based assessment with deterministic metrics from the
    skill_quality module for more consistent and calibrated scoring.
    """

    def __init__(self, use_deterministic_metrics: bool = True):
        super().__init__()
        self.assess = dspy.ChainOfThought(AssessSkillQuality)
        self.use_deterministic_metrics = use_deterministic_metrics

    def _get_deterministic_assessment(self, skill_content: str) -> dict[str, Any]:
        """Get deterministic quality metrics for skill content.

        Args:
            skill_content: The SKILL.md content to assess

        Returns:
            dict: Deterministic quality metrics
        """
        scores = assess_skill_quality(skill_content)
        return {
            "deterministic_score": scores.overall_score,
            "pattern_count": scores.pattern_count,
            "has_core_principle": scores.has_core_principle,
            "has_strong_guidance": scores.has_strong_guidance,
            "has_good_bad_contrast": scores.has_good_bad_contrast,
            "code_examples_count": scores.code_examples_count,
            "deterministic_issues": scores.issues,
            "deterministic_strengths": scores.strengths,
        }

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

        assessment = {
            "quality_score": result.quality_score,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": result.recommendations,
            "audience_alignment": result.audience_alignment,
            "rationale": getattr(result, "rationale", ""),
        }

        # Add deterministic metrics if enabled
        if self.use_deterministic_metrics:
            deterministic = self._get_deterministic_assessment(skill_content)
            assessment["deterministic_metrics"] = deterministic
            # Use deterministic score as the primary score (more consistent)
            assessment["calibrated_score"] = deterministic["deterministic_score"]

        return assessment

    async def aforward(
        self, skill_content: str, skill_metadata: Any, target_level: str
    ) -> dict[str, Any]:
        """Async wrapper for quality assessment (preferred)."""
        result = await self.assess.acall(
            skill_content=skill_content,
            skill_metadata=skill_metadata,
            target_level=target_level,
        )

        assessment = {
            "quality_score": result.quality_score,
            "strengths": result.strengths,
            "weaknesses": result.weaknesses,
            "recommendations": result.recommendations,
            "audience_alignment": result.audience_alignment,
            "rationale": getattr(result, "rationale", ""),
        }

        # Add deterministic metrics if enabled
        if self.use_deterministic_metrics:
            deterministic = self._get_deterministic_assessment(skill_content)
            assessment["deterministic_metrics"] = deterministic
            # Use deterministic score as the primary score (more consistent)
            assessment["calibrated_score"] = deterministic["deterministic_score"]

        return assessment


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
        skill_content = _canonicalize_skill_md_frontmatter(skill_content, skill_metadata)

        validation_result = await self.validator.aforward(
            skill_content=skill_content,
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            validation_rules=validation_rules,
        )

        refined_content = skill_content
        if not validation_result["validation_report"].passed or user_feedback:
            refinement_result = await self.refiner.aforward(
                current_content=skill_content,
                validation_issues=str(validation_result["validation_report"]),
                user_feedback=user_feedback,
                fix_strategies="{}",
            )
            refined_content = refinement_result.get("refined_content") or refined_content
            refined_content = _canonicalize_skill_md_frontmatter(refined_content, skill_metadata)

            # Re-run validation after refinement so the reported status/score matches
            # the final content we return to callers.
            validation_result = await self.validator.aforward(
                skill_content=refined_content,
                skill_metadata=skill_metadata,
                content_plan=content_plan,
                validation_rules=validation_rules,
            )

        validation_result["refined_content"] = refined_content
        quality_result = await self.quality_assessor.aforward(
            skill_content=refined_content,
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
