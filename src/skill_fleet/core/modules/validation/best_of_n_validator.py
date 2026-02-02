"""
BestOfN validation module for high-confidence validation decisions.

Uses multiple validation attempts and selects the best result based on
a reward function. Useful for critical validation decisions where
accuracy is more important than latency.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
from typing import Any, cast

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.validation.validation_reward import ValidationReward
from skill_fleet.core.signatures.validation.compliance import ValidateCompliance

logger = logging.getLogger(__name__)


class BestOfNValidator(BaseModule):
    """
    Validator that runs multiple attempts and selects the best result.

    Uses dspy.BestOfN pattern to generate N validation results and
    selects the one with the highest reward score. This provides
    higher confidence validation decisions at the cost of increased
    latency.

    Example:
        >>> validator = BestOfNValidator(n=5)
        >>> result = await validator.aforward(
        ...     skill_content="# My Skill\n\n...",
        ...     taxonomy_path="technical/react"
        ... )
        >>> print(result.passed)
        True
        >>> print(result.confidence)
        0.92
        >>> print(result.attempts_made)
        5

    """

    def __init__(self, n: int = 3, temperature: float = 0.7):
        """
        Initialize BestOfN validator.

        Args:
            n: Number of validation attempts to make
            temperature: Temperature for generation diversity

        """
        super().__init__()
        self.n = n
        self.temperature = temperature
        self.validator = dspy.ChainOfThought(ValidateCompliance)
        self.reward_fn = ValidationReward()

    async def aforward(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> dspy.Prediction:
        """
        Validate with multiple attempts and select best result.

        Args:
            *args: Positional arguments (skill_content, taxonomy_path, use_reward_consensus)
            **kwargs: Keyword arguments for validation parameters
            skill_content: SKILL.md content to validate
            taxonomy_path: Expected taxonomy path
            use_reward_consensus: If True, use reward-weighted consensus
                instead of just selecting highest reward

        Returns:
            dspy.Prediction with:
            - passed: Whether skill passes validation
            - compliance_score: Best/average compliance score
            - issues: Issues from best result
            - critical_issues, warnings: Additional details
            - attempts_made: Number of attempts
            - confidence: Confidence in result (based on reward score)
            - all_results: All validation results for inspection

        """
        # Support both keyword and positional calling conventions to remain
        # compatible with BaseModule.aforward while preserving existing usage.
        if "skill_content" in kwargs:
            skill_content = cast(str, kwargs["skill_content"])
        elif len(args) >= 1:
            skill_content = cast(str, args[0])
        else:
            raise TypeError("aforward() missing required argument: 'skill_content'")

        if "taxonomy_path" in kwargs:
            taxonomy_path = cast(str, kwargs["taxonomy_path"])
        elif len(args) >= 2:
            taxonomy_path = cast(str, args[1])
        else:
            raise TypeError("aforward() missing required argument: 'taxonomy_path'")

        if "use_reward_consensus" in kwargs:
            use_reward_consensus = bool(kwargs["use_reward_consensus"])
        elif len(args) >= 3:
            use_reward_consensus = bool(args[2])
        else:
            use_reward_consensus = True

        start_time = time.time()

        # Run N validation attempts in parallel
        tasks = [
            asyncio.create_task(
                self._single_validation_attempt(skill_content, taxonomy_path, i),
                name=f"validation_attempt_{i}",
            )
            for i in range(self.n)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results: list[dspy.Prediction] = []
        for result in results:
            if isinstance(result, BaseException):
                continue
            valid_results.append(cast(dspy.Prediction, result))

        if not valid_results:
            logger.error("All validation attempts failed")
            return self._create_error_prediction("All validation attempts failed")

        # Score each result
        scored_results = [(result, self.reward_fn(result)) for result in valid_results]

        # Sort by reward score
        scored_results.sort(key=lambda x: x[1], reverse=True)

        if use_reward_consensus and len(scored_results) >= 3:
            best_result = self._compute_consensus(scored_results)
        else:
            best_result = scored_results[0][0]

        # Calculate confidence metrics
        all_scores = [s for _, s in scored_results]
        score_variance = statistics.variance(all_scores) if len(all_scores) > 1 else 0.0
        confidence = 1.0 - score_variance  # Lower variance = higher confidence

        # Build output using helper to avoid repetition
        output = self._build_output_from_result(
            best_result, scored_results, confidence, len(valid_results)
        )

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "content_length": len(skill_content),
                "taxonomy_path": taxonomy_path,
            },
            outputs={
                "passed": output["passed"],
                "compliance_score": output["compliance_score"],
                "confidence": output["confidence"],
                "attempts": output["attempts_made"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _build_output_from_result(
        self,
        best_result: dspy.Prediction,
        scored_results: list[tuple[dspy.Prediction, float]],
        confidence: float,
        attempts_made: int,
    ) -> dict[str, Any]:
        """Build output dict from best result and metadata."""
        return {
            "passed": getattr(best_result, "passed", False),
            "compliance_score": getattr(best_result, "compliance_score", 0.0),
            "issues": getattr(best_result, "issues", []),
            "critical_issues": getattr(best_result, "critical_issues", []),
            "warnings": getattr(best_result, "warnings", []),
            "auto_fixable": getattr(best_result, "auto_fixable", []),
            "attempts_made": attempts_made,
            "confidence": round(confidence, 3),
            "reward_score": round(scored_results[0][1], 3),
            "all_results": [
                {
                    "passed": getattr(r, "passed", False),
                    "compliance_score": getattr(r, "compliance_score", 0.0),
                    "reward_score": s,
                }
                for r, s in scored_results
            ],
        }

    async def _single_validation_attempt(
        self,
        skill_content: str,
        taxonomy_path: str,
        attempt_number: int,
    ) -> dspy.Prediction:
        """
        Run a single validation attempt.

        Args:
            skill_content: SKILL.md content
            taxonomy_path: Expected taxonomy path
            attempt_number: Which attempt this is (for logging)

        Returns:
            Validation result Prediction

        """
        try:
            # Note: DSPy doesn't directly support per-call temperature
            # In a full implementation, you'd configure different LMs
            # or use different prompt variations
            result = await self.validator.acall(
                skill_content=skill_content,
                taxonomy_path=taxonomy_path,
            )
            return result
        except Exception as e:
            logger.warning(f"Validation attempt {attempt_number} failed: {e}")
            raise

    def _compute_consensus(
        self,
        scored_results: list[tuple[dspy.Prediction, float]],
    ) -> dspy.Prediction:
        """
        Compute consensus result from multiple validations.

        Uses reward-weighted voting to combine results.

        Args:
            scored_results: List of (result, reward_score) tuples

        Returns:
            Consensus prediction

        """
        if not scored_results:
            return dspy.Prediction()

        # Use top 3 results for consensus
        top_results = scored_results[:3]
        total_reward = sum(s for _, s in top_results)

        if total_reward == 0:
            return top_results[0][0]

        # Weighted average of compliance scores
        weighted_score = (
            sum(getattr(r, "compliance_score", 0.0) * s for r, s in top_results) / total_reward
        )

        # Majority vote for pass/fail
        pass_votes = sum(s for r, s in top_results if getattr(r, "passed", False))
        consensus_passed = pass_votes / total_reward > 0.5

        # Merge issues (union of all unique issues)
        all_issues: set[str] = set()
        for r, _ in top_results:
            issues = getattr(r, "issues", [])
            if isinstance(issues, list):
                all_issues.update(str(i) for i in issues)

        # Merge critical issues
        all_critical: set[str] = set()
        for r, _ in top_results:
            critical = getattr(r, "critical_issues", [])
            if isinstance(critical, list):
                all_critical.update(str(i) for i in critical)

        # Create consensus prediction
        return dspy.Prediction(
            passed=consensus_passed,
            compliance_score=round(weighted_score, 3),
            issues=list(all_issues)[:10],  # Limit to top 10
            critical_issues=list(all_critical)[:5],
            warnings=getattr(top_results[0][0], "warnings", []),
            auto_fixable=getattr(top_results[0][0], "auto_fixable", []),
            consensus=True,
        )

    def _create_error_prediction(self, error_message: str) -> dspy.Prediction:
        """Create an error prediction when all attempts fail."""
        return self._to_prediction(
            passed=False,
            compliance_score=0.0,
            issues=[error_message],
            critical_issues=[error_message],
            warnings=[],
            auto_fixable=[],
            attempts_made=0,
            confidence=0.0,
            error=True,
        )


def validate_with_best_of_n(
    skill_content: str,
    taxonomy_path: str,
    n: int = 3,
    use_consensus: bool = True,
) -> dspy.Prediction:
    """
    Convenience function for BestOfN validation.

    Args:
        skill_content: SKILL.md content to validate
        taxonomy_path: Expected taxonomy path
        n: Number of validation attempts
        use_consensus: Use reward-weighted consensus

    Returns:
        dspy.Prediction with validation results

    Example:
        >>> result = validate_with_best_of_n(
        ...     skill_content="# My Skill\n...",
        ...     taxonomy_path="technical/react",
        ...     n=5
        ... )
        >>> print(result.passed, result.confidence)

    """
    validator = BestOfNValidator(n=n)
    return validator.forward(
        skill_content=skill_content,
        taxonomy_path=taxonomy_path,
        use_reward_consensus=use_consensus,
    )
