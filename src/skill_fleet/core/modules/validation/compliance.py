"""
Validation modules for skill quality assurance.

Uses validation signatures to check compliance and assess quality.
"""

from typing import Any

import dspy

from skill_fleet.common.llm_fallback import with_llm_fallback
from skill_fleet.common.utils import timed_execution
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

    @with_llm_fallback(default_return=None)
    async def _call_lm(self, skill_content: str, taxonomy_path: str) -> Any:
        return await self.validate.acall(skill_content=skill_content, taxonomy_path=taxonomy_path)

    @timed_execution()
    async def aforward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Validate skill compliance.

        Args:
            skill_content: SKILL.md content
            taxonomy_path: Expected taxonomy path
            **kwargs: Additional keyword arguments for compatibility.

        Returns:
            dspy.Prediction with validation results (score, issues)

        """
        skill_content: str = kwargs["skill_content"]
        taxonomy_path: str = kwargs["taxonomy_path"]

        result = await self._call_lm(skill_content, taxonomy_path)
        if result is None:
            self.logger.warning("Compliance validation failed. Using lightweight checks.")
            fallback = self._create_fallback_result(skill_content, taxonomy_path)
            return self._to_prediction(**fallback)

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

        return self._to_prediction(**output)

    def _create_fallback_result(self, skill_content: str, taxonomy_path: str) -> dict[str, Any]:
        """
        Lightweight compliance checks when LLM-based validation fails.

        Intended to keep workflows/test runs functional when no LM is configured.
        """
        issues: list[str] = []
        warnings: list[str] = []

        content = skill_content or ""
        passed = True

        if not content.strip().startswith("---"):
            passed = False
            issues.append("Missing YAML frontmatter (--- ... ---) at top of SKILL.md")

        lowered = content.lower()
        if "name:" not in lowered:
            passed = False
            issues.append("Frontmatter missing required field: name")
        if "description:" not in lowered:
            passed = False
            issues.append("Frontmatter missing required field: description")

        # Basic check that taxonomy path is present/valid-ish.
        if not taxonomy_path or "/" not in taxonomy_path:
            warnings.append("Taxonomy path is missing or not in expected 'category/name' format")

        compliance_score = 0.9 if passed else 0.2
        return {
            "passed": passed,
            "compliance_score": compliance_score,
            "issues": issues,
            "critical_issues": [],
            "warnings": warnings,
            "auto_fixable": [],
            "fallback": True,
        }

    def forward(self, **kwargs) -> dspy.Prediction:
        """Synchronous forward - delegates to async."""
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))


class AssessQualityModule(BaseModule):
    """Assess overall skill quality including size and conciseness."""

    def __init__(self):
        super().__init__()
        self.assess = dspy.ChainOfThought(AssessQuality)

    @with_llm_fallback(default_return=None)
    async def _call_lm(self, skill_content: str, plan: dict, success_criteria: list) -> Any:
        return await self.assess.acall(
            skill_content=skill_content, plan=str(plan), success_criteria=success_criteria
        )

    @timed_execution()
    async def aforward(self, **kwargs) -> dspy.Prediction:
        """
        Assess skill quality.

        Performs both LLM-based quality assessment and rule-based checks for:
        - Size (word count)
        - Conciseness (verbosity score)

        Args:
            **kwargs: Keyword arguments containing skill_content, plan, and success_criteria
            skill_content: SKILL.md content
            plan: Original plan
            success_criteria: Criteria to check

        Returns:
            dspy.Prediction with quality assessment (scores and metrics)

        """
        # Extract expected arguments from kwargs for compatibility with BaseModule.aforward
        skill_content: str = kwargs.get("skill_content", "")
        plan: dict = kwargs.get("plan", {})
        success_criteria = kwargs.get("success_criteria")

        # Rule-based size and conciseness checks (always available, even if LLM fails)
        word_count = len(skill_content.split())
        size_assessment = self._assess_size(word_count)
        verbosity_score = self._assess_verbosity(skill_content)

        # LLM-based quality assessment (best-effort)
        result = await self._call_lm(skill_content, plan, success_criteria or [])
        if result is None:
            self.logger.warning("Quality LLM assessment failed. Using rule-based metrics.")

        output = {
            "overall_score": float(getattr(result, "overall_score", 0.0) or 0.0)
            if result is not None
            else 0.0,
            "completeness": float(getattr(result, "completeness", 0.0) or 0.0)
            if result is not None
            else 0.0,
            "clarity": float(getattr(result, "clarity", 0.0) or 0.0) if result is not None else 0.0,
            "usefulness": float(getattr(result, "usefulness", 0.0) or 0.0)
            if result is not None
            else 0.0,
            "accuracy": float(getattr(result, "accuracy", 0.0) or 0.0)
            if result is not None
            else 0.0,
            "strengths": getattr(result, "strengths", []) if result is not None else [],
            "weaknesses": getattr(result, "weaknesses", []) if result is not None else [],
            "feedback": getattr(result, "feedback", "") if result is not None else "",
            "meets_success_criteria": getattr(result, "meets_success_criteria", [])
            if result is not None
            else [],
            "missing_success_criteria": getattr(result, "missing_success_criteria", [])
            if result is not None
            else [],
            # NEW: Size and conciseness metrics
            "word_count": word_count,
            "size_assessment": size_assessment,
            "verbosity_score": verbosity_score,
            "size_recommendations": self._generate_size_recommendations(
                word_count, size_assessment
            ),
            "conciseness_recommendations": self._generate_conciseness_recommendations(
                verbosity_score, skill_content
            ),
        }

        # Validate
        if not self._validate_result(output, ["overall_score"]):
            output["overall_score"] = 0.0

        return self._to_prediction(**output)

    def _assess_size(self, word_count: int) -> str:
        """
        Assess skill size based on word count.

        Args:
            word_count: Number of words in skill content

        Returns:
            Size assessment: 'optimal', 'acceptable', or 'too_large'

        """
        if word_count < 3000:
            return "optimal"
        elif word_count < 5000:
            return "acceptable"
        else:
            return "too_large"

    def _assess_verbosity(self, content: str) -> float:
        """
        Assess content verbosity (0.0 = very concise, 1.0 = very verbose).

        Uses heuristics:
        - Average sentence length
        - Ratio of filler words to content words
        - Section density

        Args:
            content: Skill content

        Returns:
            Verbosity score (0.0 - 1.0)

        """
        import re

        # Split into sentences (rough approximation)
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Calculate average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Count filler words (common verbose phrases)
        filler_patterns = [
            r"\bin order to\b",
            r"\bdue to the fact that\b",
            r"\bat this point in time\b",
            r"\bin the event that\b",
            r"\bfor the purpose of\b",
            r"\bit is important to note that\b",
            r"\bit should be noted that\b",
        ]

        filler_count = sum(
            len(re.findall(pattern, content, re.IGNORECASE)) for pattern in filler_patterns
        )
        filler_ratio = filler_count / max(len(sentences), 1)

        # Calculate verbosity score (0-1)
        # Longer sentences + more filler words = more verbose
        length_score = max(
            0.0, min((avg_sentence_length - 10) / 20, 1.0)
        )  # Normalize: 10 words = 0, 30 words = 1, clamped to [0, 1]
        filler_score = min(filler_ratio * 5, 1.0)  # Scale filler ratio

        verbosity = length_score * 0.6 + filler_score * 0.4
        # Ensure final value is in [0, 1] range
        return max(0.0, min(round(verbosity, 2), 1.0))

    def _generate_size_recommendations(self, word_count: int, size_assessment: str) -> list[str]:
        """Generate recommendations based on skill size."""
        recommendations = []

        if size_assessment == "too_large":
            recommendations.append(
                f"Skill is {word_count} words (recommended: <5000). "
                "Consider moving detailed documentation to references/ folder."
            )
        elif size_assessment == "acceptable":
            recommendations.append(
                f"Skill is {word_count} words. Consider using progressive disclosure "
                "if content continues to grow."
            )

        return recommendations

    def _generate_conciseness_recommendations(
        self, verbosity_score: float, content: str
    ) -> list[str]:
        """Generate recommendations for improving conciseness."""
        recommendations = []

        if verbosity_score > 0.7:
            recommendations.append(
                "Instructions are quite verbose. Consider: "
                "1) Using bullet points, 2) Removing filler phrases, "
                "3) Moving detailed explanations to references/"
            )
        elif verbosity_score > 0.5:
            recommendations.append(
                "Some sections could be more concise. Use bullet points "
                "and numbered lists for clarity."
            )

        # Check for common verbose patterns
        import re

        if re.search(r"\b(it is|there are|there is)\b", content, re.IGNORECASE):
            recommendations.append(
                "Consider removing 'it is/there are' constructions for more direct language."
            )

        return recommendations


class RefineSkillModule(BaseModule):
    """Refine skill based on quality assessment."""

    def __init__(self):
        super().__init__()
        self.refine = dspy.ChainOfThought(RefineSkill)

    @with_llm_fallback(default_return=None)
    async def _call_lm(self, current_content: str, weaknesses: list, target_score: float) -> Any:
        return await self.refine.acall(
            current_content=current_content, weaknesses=weaknesses, target_score=target_score
        )

    @timed_execution()
    async def aforward(
        self, current_content: str, weaknesses: list[str], target_score: float = 0.8
    ) -> dspy.Prediction:
        """
        Refine skill content.

        Args:
            current_content: Current SKILL.md
            weaknesses: List of weaknesses to address
            target_score: Target quality score

        Returns:
            Refined content

        """
        result = await self._call_lm(current_content, weaknesses, target_score)
        if result is None:
            self.logger.warning("Refinement failed. Returning original content.")

        output = {
            "refined_content": getattr(result, "refined_content", None)
            if result is not None
            else None,
            "improvements_made": getattr(result, "improvements_made", [])
            if result is not None
            else [],
            "new_score_estimate": float(getattr(result, "new_score_estimate", 0.0) or 0.0)
            if result is not None
            else 0.0,
            "requires_another_pass": bool(getattr(result, "requires_another_pass", False))
            if result is not None
            else False,
        }

        # Validate
        if not self._validate_result(output, ["refined_content"]):
            output["refined_content"] = current_content

        return self._to_prediction(**output)

    def forward(self, **kwargs) -> dspy.Prediction:
        """Synchronous forward - delegates to async."""
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))
