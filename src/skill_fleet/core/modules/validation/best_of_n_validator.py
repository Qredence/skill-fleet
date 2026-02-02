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
from skill_fleet.core.signatures.validation.compliance import ValidateCompliance

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

        # Weights
        weights = {
            "confidence": 0.40,
            "completeness": 0.35,
            "actionability": 0.25,
        }

        total_score = sum(scores[k] * weights[k] for k in scores)

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

    async def aforward(  # type: ignore[override]
        self,
        skill_content: str,
        taxonomy_path: str,
        use_reward_consensus: bool = True,
    ) -> dspy.Prediction:
        """
        Validate with multiple attempts and select best result.

        Args:
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

        # Extract best result data
        output = {
            "passed": getattr(best_result, "passed", False),
            "compliance_score": getattr(best_result, "compliance_score", 0.0),
            "issues": getattr(best_result, "issues", []),
            "critical_issues": getattr(best_result, "critical_issues", []),
            "warnings": getattr(best_result, "warnings", []),
            "auto_fixable": getattr(best_result, "auto_fixable", []),
            "attempts_made": len(valid_results),
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

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Sync version - delegates to async."""
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))


class AdaptiveValidator(BestOfNValidator):
    """
    Adaptive validator that adjusts N based on result confidence.

    Starts with fewer attempts and increases if confidence is low.
    Balances latency vs confidence dynamically.

    Example:
        >>> validator = AdaptiveValidator(
        ...     min_attempts=2,
        ...     max_attempts=7,
        ...     confidence_threshold=0.8
        ... )
        >>> result = validator.forward(skill_content="...", taxonomy_path="...")
        >>> # May have used 2-7 attempts depending on result clarity

    """

    def __init__(
        self,
        min_attempts: int = 2,
        max_attempts: int = 7,
        confidence_threshold: float = 0.8,
        temperature: float = 0.7,
    ):
        """
        Initialize adaptive validator.

        Args:
            min_attempts: Minimum number of validation attempts
            max_attempts: Maximum number of validation attempts
            confidence_threshold: Stop if confidence reaches this level
            temperature: Temperature for generation diversity

        """
        super().__init__(n=min_attempts, temperature=temperature)
        self.min_attempts = min_attempts
        self.max_attempts = max_attempts
        self.confidence_threshold = confidence_threshold

    async def aforward(  # type: ignore[override]
        self,
        skill_content: str,
        taxonomy_path: str,
    ) -> dspy.Prediction:
        """
        Validate with adaptive number of attempts.

        Args:
            skill_content: SKILL.md content
            taxonomy_path: Expected taxonomy path

        Returns:
            dspy.Prediction with validation results

        """
        start_time = time.time()
        all_results: list[dspy.Prediction] = []

        # Start with minimum attempts
        for attempt in range(self.max_attempts):
            try:
                result = await self._single_validation_attempt(
                    skill_content, taxonomy_path, attempt
                )
                all_results.append(result)

                # Check if we have enough results and confidence
                if len(all_results) >= self.min_attempts:
                    scored = [(r, self.reward_fn(r)) for r in all_results]
                    scored.sort(key=lambda x: x[1], reverse=True)

                    # Calculate current confidence
                    rewards = [s for _, s in scored]
                    if len(rewards) > 1:
                        variance = statistics.variance(rewards)
                        confidence = 1.0 - min(variance, 1.0)
                    else:
                        confidence = 0.5

                    # Stop if confident enough
                    if confidence >= self.confidence_threshold:
                        logger.info(
                            f"Early stopping at attempt {attempt + 1}, "
                            f"confidence {confidence:.3f} >= {self.confidence_threshold}"
                        )
                        break

            except Exception as e:
                logger.warning(f"Adaptive attempt {attempt} failed: {e}")
                continue

        if not all_results:
            return self._create_error_prediction("All validation attempts failed")

        # Score and select best result
        scored_results = [(r, self.reward_fn(r)) for r in all_results]
        scored_results.sort(key=lambda x: x[1], reverse=True)
        best_result = self._compute_consensus(scored_results)

        # Calculate final metrics
        all_scores = [s for _, s in scored_results]
        score_variance = statistics.variance(all_scores) if len(all_scores) > 1 else 0.0
        confidence = 1.0 - score_variance

        output = {
            "passed": getattr(best_result, "passed", False),
            "compliance_score": getattr(best_result, "compliance_score", 0.0),
            "issues": getattr(best_result, "issues", []),
            "critical_issues": getattr(best_result, "critical_issues", []),
            "warnings": getattr(best_result, "warnings", []),
            "auto_fixable": getattr(best_result, "auto_fixable", []),
            "attempts_made": len(all_results),
            "confidence": round(confidence, 3),
            "adaptive_stop": len(all_results) < self.max_attempts,
        }

        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"content_length": len(skill_content)},
            outputs={
                "passed": output["passed"],
                "confidence": output["confidence"],
                "attempts": output["attempts_made"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)


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
