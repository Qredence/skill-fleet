"""
Validation reward function for BestOfN validation.

Provides scoring mechanisms to select the best validation result
based on confidence, completeness, and actionability.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


class ValidationReward:
    """
    Reward function for selecting best validation result.

    Evaluates validation results based on:
    - Confidence (clear pass/fail vs ambiguous)
    - Completeness (number of checks performed)
    - Actionability (specific, fixable issues)
    - Consistency (low variance across runs)

    Returns a score between 0.0 and 1.0.

    """

    # Scoring weights
    CONFIDENCE_WEIGHT = 0.40
    COMPLETENESS_WEIGHT = 0.35
    ACTIONABILITY_WEIGHT = 0.25

    def __init__(self):
        """Initialize the reward function."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, result: dspy.Prediction | dict[str, Any]) -> float:
        """
        Calculate reward score for a validation result.

        Args:
            result: Validation result (Prediction or dict)

        Returns:
            Reward score between 0.0 and 1.0

        """
        result_dict = self._to_dict(result)

        scores = {
            "confidence": self._score_confidence(result_dict),
            "completeness": self._score_completeness(result_dict),
            "actionability": self._score_actionability(result_dict),
        }

        total_score = (
            scores["confidence"] * self.CONFIDENCE_WEIGHT
            + scores["completeness"] * self.COMPLETENESS_WEIGHT
            + scores["actionability"] * self.ACTIONABILITY_WEIGHT
        )

        self.logger.debug(f"Validation reward scores: {scores}, Total: {total_score:.3f}")

        return round(total_score, 3)

    def _to_dict(self, result: dspy.Prediction | dict[str, Any]) -> dict[str, Any]:
        """Convert Prediction-like outputs to a plain dict without relying on `__dict__`."""
        if isinstance(result, dict):
            return result  # type: ignore[return-value]

        # Many DSPy objects are mapping-like.
        try:
            as_dict = dict(result)
            if isinstance(as_dict, dict) and as_dict:
                return as_dict
        except Exception:
            pass  # nosec B110

        # Fall back to attribute access for known fields.
        fields = (
            "passed",
            "compliance_score",
            "issues",
            "critical_issues",
            "warnings",
            "auto_fixable",
            "rationale",
            "reasoning",
        )
        extracted: dict[str, Any] = {}
        for field in fields:
            if hasattr(result, field):
                extracted[field] = getattr(result, field)
        if extracted:
            return extracted

        # Last resort.
        if hasattr(result, "__dict__") and isinstance(getattr(result, "__dict__", None), dict):
            return dict(result.__dict__)

        return {}

    def _score_confidence(self, result: dict[str, Any]) -> float:
        """Score based on confidence of the result."""
        score = 0.0

        # Clear pass/fail is better than borderline
        compliance_score = result.get("compliance_score", 0.5)
        if compliance_score >= 0.9 or compliance_score <= 0.1:
            score += 0.5  # Clear decision
        elif compliance_score >= 0.7 or compliance_score <= 0.3:
            score += 0.3  # Moderately clear
        else:
            score += 0.1  # Ambiguous

        # Passed/failed status available
        if "passed" in result:
            score += 0.3

        # Has rationale/explanation
        if result.get("rationale") or result.get("reasoning"):
            score += 0.2

        return min(score, 1.0)

    def _score_completeness(self, result: dict[str, Any]) -> float:
        """Score based on completeness of checks."""
        score = 0.0

        # Count available fields
        fields = ["passed", "compliance_score", "issues", "critical_issues", "warnings"]
        present = sum(1 for f in fields if f in result)
        score += (present / len(fields)) * 0.5

        # Has specific issues listed
        issues = result.get("issues", [])
        if isinstance(issues, list) and len(issues) > 0:
            score += 0.25
        elif isinstance(issues, list) and len(issues) == 0 and result.get("passed"):
            score += 0.25  # Empty issues with passed=True is valid

        # Has warnings
        warnings = result.get("warnings", [])
        if isinstance(warnings, list):
            score += 0.25

        return min(score, 1.0)

    def _score_actionability(self, result: dict[str, Any]) -> float:
        """Score based on how actionable the feedback is."""
        passed = bool(result.get("passed", False))

        issues = result.get("issues", [])
        if not isinstance(issues, list):
            issues = []

        critical_issues = result.get("critical_issues", [])
        if not isinstance(critical_issues, list):
            critical_issues = []

        auto_fixable = result.get("auto_fixable", [])
        if not isinstance(auto_fixable, list):
            auto_fixable = []

        # For passed results, prefer "clean" passes with no issues.
        if passed:
            score = 1.0
            score -= min(0.4, 0.1 * len(issues))
            score -= min(0.6, 0.2 * len(critical_issues))
            # Missing key fields means the "pass" is less reliable.
            if "compliance_score" not in result:
                score -= 0.2
            if "issues" not in result:
                score -= 0.1
            return max(0.0, min(1.0, score))

        # For failed results, reward detailed, fixable feedback.
        score = 0.0
        if issues:
            score += 0.3
            detailed = sum(1 for i in issues if len(str(i)) > 20)
            if detailed >= max(1, len(issues) // 2):
                score += 0.3
        if auto_fixable:
            score += 0.2
        if "critical_issues" in result:
            score += 0.2

        return min(score, 1.0)
