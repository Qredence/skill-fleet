"""
Phase 3: Validation Workflow.

Validates generated skill content for compliance and quality.
Can refine content if quality is insufficient.
"""

import logging
from typing import Any

from skill_fleet.core.modules.validation.compliance import (
    AssessQualityModule,
    RefineSkillModule,
    ValidateComplianceModule,
)

logger = logging.getLogger(__name__)


class ValidationWorkflow:
    """
    Phase 3: Validation & Quality Assurance Workflow.

    Validates skill content:
    1. Check agentskills.io compliance
    2. Assess overall quality
    3. Refine if below threshold
    4. Return validation report

    Example:
        workflow = ValidationWorkflow()
        result = await workflow.execute(
            skill_content="# Skill\n...",
            plan={"success_criteria": [...]},
            taxonomy_path="technical/python"
        )

    """

    def __init__(self):
        self.compliance = ValidateComplianceModule()
        self.quality = AssessQualityModule()
        self.refinement = RefineSkillModule()

    async def execute(
        self,
        skill_content: str,
        plan: dict,
        taxonomy_path: str,
        enable_hitl_review: bool = False,
        quality_threshold: float = 0.75,
    ) -> dict[str, Any]:
        """
        Execute validation workflow.

        Args:
            skill_content: Generated SKILL.md content
            plan: Original plan with success criteria
            taxonomy_path: Expected taxonomy path
            enable_hitl_review: Whether to show for human review
            quality_threshold: Minimum quality score

        Returns:
            Validation results

        """
        logger.info("Starting validation workflow")

        # Step 1: Validate compliance
        logger.debug("Checking compliance")
        compliance_result = await self.compliance.aforward(
            skill_content=skill_content, taxonomy_path=taxonomy_path
        )

        # Step 2: Assess quality
        logger.debug("Assessing quality")
        quality_result = await self.quality.aforward(
            skill_content=skill_content,
            plan=plan,
            success_criteria=plan.get("success_criteria", []),
        )

        # Check if HITL review requested
        if enable_hitl_review:
            return self._create_review_checkpoint(
                skill_content=skill_content, compliance=compliance_result, quality=quality_result
            )

        # Step 3: Refine if needed
        final_content = skill_content
        refinements_made = []

        if quality_result["overall_score"] < quality_threshold:
            logger.info(
                f"Quality {quality_result['overall_score']:.2f} below threshold {quality_threshold}"
            )

            if quality_result.get("weaknesses"):
                refine_result = await self.refinement.aforward(
                    current_content=skill_content,
                    weaknesses=quality_result["weaknesses"],
                    target_score=quality_threshold,
                )

                final_content = refine_result.get("refined_content", skill_content)
                refinements_made = refine_result.get("improvements_made", [])

        # Determine final status
        passed = (
            compliance_result.get("passed", False)
            and quality_result.get("overall_score", 0.0) >= quality_threshold
        )

        logger.info(f"Validation completed: passed={passed}")

        return {
            "status": "completed" if passed else "needs_improvement",
            "passed": passed,
            "skill_content": final_content,
            "validation_report": {
                "compliance": compliance_result,
                "quality": quality_result,
                "refinements_made": refinements_made,
            },
        }

    def _create_review_checkpoint(
        self, skill_content: str, compliance: dict, quality: dict
    ) -> dict[str, Any]:
        """
        Create HITL review checkpoint.

        Args:
            skill_content: Content to review
            compliance: Compliance results
            quality: Quality results

        Returns:
            Review checkpoint

        """
        logger.info("Creating review checkpoint")

        return {
            "status": "pending_hitl",
            "hitl_type": "review",
            "hitl_data": {
                "skill_content_preview": skill_content[:2000] + "..."
                if len(skill_content) > 2000
                else skill_content,
                "compliance_score": compliance.get("compliance_score", 0.0),
                "quality_score": quality.get("overall_score", 0.0),
                "strengths": quality.get("strengths", [])[:3],
                "weaknesses": quality.get("weaknesses", [])[:3],
                "issues": compliance.get("issues", []),
            },
            "context": {
                "full_content": skill_content,
                "compliance": compliance,
                "quality": quality,
            },
        }
