"""
Validation modules for skill quality assurance.

Uses validation signatures to check compliance and assess quality.
"""

import time
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.validation.compliance import (
    AssessQuality,
    RefineSkill,
    ValidateCompliance,
)


class ValidateComplianceModule(BaseModule):
    """
    Validate agentskills.io compliance.

    Checks YAML frontmatter, structure, and naming conventions.
    """

    def __init__(self):
        super().__init__()
        self.validate = dspy.ChainOfThought(ValidateCompliance)

    async def aforward(self, **kwargs: Any) -> dict[str, Any]:
        """
        Validate skill compliance.

        Args:
            skill_content: SKILL.md content
            taxonomy_path: Expected taxonomy path

        Returns:
            Validation results with score and issues

        """
        skill_content: str = kwargs["skill_content"]
        taxonomy_path: str = kwargs["taxonomy_path"]

        start_time = time.time()

        result = await self.validate.acall(skill_content=skill_content, taxonomy_path=taxonomy_path)

        output = {
            "passed": bool(result.passed) if hasattr(result, "passed") else False,
            "compliance_score": float(result.compliance_score)
            if hasattr(result, "compliance_score")
            else 0.0,
            "issues": result.issues if isinstance(result.issues, list) else [],
            "critical_issues": result.critical_issues
            if isinstance(result.critical_issues, list)
            else [],
            "warnings": result.warnings if isinstance(result.warnings, list) else [],
            "auto_fixable": result.auto_fixable if isinstance(result.auto_fixable, list) else [],
        }

        # Validate
        if not self._validate_result(output, ["passed", "compliance_score"]):
            output["passed"] = False
            output["compliance_score"] = 0.0

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"content_length": len(skill_content), "path": taxonomy_path},
            outputs={"passed": output["passed"], "score": output["compliance_score"]},
            duration_ms=duration_ms,
        )

        return output

    def forward(self, **kwargs) -> dict[str, Any]:
        """Synchronous forward - delegates to async."""
        import asyncio

        return asyncio.run(self.aforward(**kwargs))


class AssessQualityModule(BaseModule):
    """Assess overall skill quality."""

    def __init__(self):
        super().__init__()
        self.assess = dspy.ChainOfThought(AssessQuality)

    async def aforward(  # type: ignore[override]
        self, skill_content: str, plan: dict, success_criteria: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Assess skill quality.

        Args:
            skill_content: SKILL.md content
            plan: Original plan
            success_criteria: Criteria to check

        Returns:
            Quality assessment with scores

        """
        start_time = time.time()

        result = await self.assess.acall(
            skill_content=skill_content, plan=str(plan), success_criteria=success_criteria or []
        )

        output = {
            "overall_score": float(result.overall_score)
            if hasattr(result, "overall_score")
            else 0.0,
            "completeness": float(result.completeness) if hasattr(result, "completeness") else 0.0,
            "clarity": float(result.clarity) if hasattr(result, "clarity") else 0.0,
            "usefulness": float(result.usefulness) if hasattr(result, "usefulness") else 0.0,
            "accuracy": float(result.accuracy) if hasattr(result, "accuracy") else 0.0,
            "strengths": result.strengths if isinstance(result.strengths, list) else [],
            "weaknesses": result.weaknesses if isinstance(result.weaknesses, list) else [],
            "meets_success_criteria": result.meets_success_criteria
            if isinstance(result.meets_success_criteria, list)
            else [],
            "missing_success_criteria": result.missing_success_criteria
            if isinstance(result.missing_success_criteria, list)
            else [],
        }

        # Validate
        if not self._validate_result(output, ["overall_score"]):
            output["overall_score"] = 0.0

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"content_length": len(skill_content)},
            outputs={"overall_score": output["overall_score"]},
            duration_ms=duration_ms,
        )

        return output

    def forward(self, **kwargs) -> dict[str, Any]:
        """Synchronous forward - delegates to async."""
        import asyncio

        return asyncio.run(self.aforward(**kwargs))


class RefineSkillModule(BaseModule):
    """Refine skill based on quality assessment."""

    def __init__(self):
        super().__init__()
        self.refine = dspy.ChainOfThought(RefineSkill)

    async def aforward(  # type: ignore[override]
        self, current_content: str, weaknesses: list[str], target_score: float = 0.8
    ) -> dict[str, Any]:
        """
        Refine skill content.

        Args:
            current_content: Current SKILL.md
            weaknesses: List of weaknesses to address
            target_score: Target quality score

        Returns:
            Refined content

        """
        start_time = time.time()

        result = await self.refine.acall(
            current_content=current_content, weaknesses=weaknesses, target_score=target_score
        )

        output = {
            "refined_content": result.refined_content
            if hasattr(result, "refined_content")
            else current_content,
            "improvements_made": result.improvements_made
            if isinstance(result.improvements_made, list)
            else [],
            "new_score_estimate": float(result.new_score_estimate)
            if hasattr(result, "new_score_estimate")
            else 0.0,
            "requires_another_pass": bool(result.requires_another_pass)
            if hasattr(result, "requires_another_pass")
            else False,
        }

        # Validate
        if not self._validate_result(output, ["refined_content"]):
            output["refined_content"] = current_content

        # Log
        duration_ms = (time.time() - start_time) * 1000
        improvements_list = output.get("improvements_made", [])
        if not isinstance(improvements_list, list):
            improvements_list = []
        self._log_execution(
            inputs={"weaknesses_count": len(weaknesses), "target": target_score},
            outputs={"improvements": len(improvements_list)},
            duration_ms=duration_ms,
        )

        return output

    def forward(self, **kwargs) -> dict[str, Any]:
        """Synchronous forward - delegates to async."""
        import asyncio

        return asyncio.run(self.aforward(**kwargs))
