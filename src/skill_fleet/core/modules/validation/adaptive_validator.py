"""
Adaptive validation module that adjusts N based on result confidence.

Extends BestOfNValidator with dynamic attempt adjustment based on
confidence levels, balancing latency vs accuracy.
"""

from __future__ import annotations

import logging
import statistics
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dspy

from skill_fleet.core.modules.validation.best_of_n_validator import BestOfNValidator
from skill_fleet.core.modules.validation.validation_reward import ValidationReward

logger = logging.getLogger(__name__)


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
        # Need separate reward function since parent's is tied to self.n
        self._adaptive_reward_fn = ValidationReward()

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
                    scored = [(r, self._adaptive_reward_fn(r)) for r in all_results]
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
        scored_results = [(r, self._adaptive_reward_fn(r)) for r in all_results]
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
