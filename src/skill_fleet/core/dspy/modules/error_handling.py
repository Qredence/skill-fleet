"""
Error handling wrappers for DSPy modules.

Provides robust error handling, fallbacks, and retry logic for production use.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

import dspy

logger = logging.getLogger(__name__)


class RobustModule(dspy.Module):
    """
    Wrapper for DSPy modules with error handling and fallbacks.

    Features:
    - Automatic retry with exponential backoff
    - Fallback to default values on failure
    - Detailed error logging
    - Graceful degradation

    Example:
        module = dspy.ChainOfThought("task -> output")
        robust = RobustModule(
            module,
            name="generator",
            max_retries=3,
            fallback_fn=lambda **kwargs: dspy.Prediction(output="Error: generation failed"),
        )

        result = robust(task="Create skill")  # Handles errors gracefully

    """

    def __init__(
        self,
        module: dspy.Module,
        name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        fallback_fn: Callable[..., dspy.Prediction] | None = None,
        log_errors: bool = True,
    ) -> None:
        """
        Initialize robust module wrapper.

        Args:
            module: DSPy module to wrap
            name: Name for logging
            max_retries: Maximum retry attempts on failure
            retry_delay: Initial retry delay in seconds (exponential backoff)
            fallback_fn: Function to call if all retries fail
            log_errors: Whether to log errors

        """
        super().__init__()
        self.module = module
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.fallback_fn = fallback_fn
        self.log_errors = log_errors

        # Error tracking
        self.error_count = 0
        self.last_error: str | None = None

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Execute module with retry logic and fallback.

        Args:
            **kwargs: Module input parameters

        Returns:
            Module output or fallback result

        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Execute module
                result = self.module(**kwargs)

                # Success - reset error count
                if attempt > 0:
                    logger.info(f"{self.name} succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_exception = e
                self.error_count += 1
                self.last_error = str(e)

                if self.log_errors:
                    logger.warning(
                        f"{self.name} failed on attempt {attempt + 1}/{self.max_retries}: "
                        f"{type(e).__name__}: {str(e)}"
                    )

                # Don't retry on final attempt
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)

        # All retries failed
        error_msg = f"All {self.max_retries} attempts failed: {last_exception}"
        logger.error(f"{self.name}: {error_msg}")

        # Try fallback if available
        if self.fallback_fn:
            try:
                logger.info(f"{self.name}: Using fallback function")
                return self.fallback_fn(**kwargs)
            except Exception as fallback_error:
                logger.error(f"{self.name}: Fallback also failed: {fallback_error}")

        # Re-raise original exception if no fallback worked
        raise last_exception  # type: ignore


class ValidatedModule(dspy.Module):
    """
    Wrapper for DSPy modules with output validation.

    Validates module output against expected schema/constraints before returning.

    Example:
        def validate_output(result):
            if not hasattr(result, "answer"):
                raise ValueError("Missing answer field")
            if len(result.answer) < 10:
                raise ValueError("Answer too short")
            return True

        module = dspy.ChainOfThought("question -> answer")
        validated = ValidatedModule(module, validator=validate_output)

        result = validated(question="What is DSPy?")  # Validates before returning

    """

    def __init__(
        self,
        module: dspy.Module,
        validator: Callable[[dspy.Prediction], bool],
        name: str = "validated_module",
        raise_on_invalid: bool = True,
    ) -> None:
        """
        Initialize validated module wrapper.

        Args:
            module: DSPy module to wrap
            validator: Function that validates output (raises on invalid)
            name: Name for logging
            raise_on_invalid: Whether to raise exception on validation failure

        """
        super().__init__()
        self.module = module
        self.validator = validator
        self.name = name
        self.raise_on_invalid = raise_on_invalid

        self.validation_failures = 0

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Execute module and validate output.

        Args:
            **kwargs: Module input parameters

        Returns:
            Validated module output

        Raises:
            ValueError: If validation fails and raise_on_invalid=True

        """
        result = self.module(**kwargs)

        try:
            # Validate output
            self.validator(result)
            return result

        except Exception as e:
            self.validation_failures += 1
            logger.error(f"{self.name} validation failed: {e}")

            if self.raise_on_invalid:
                raise ValueError(f"Output validation failed: {e}") from e

            # Return result anyway if not raising
            return result


def create_fallback_for_phase(phase: str) -> Callable[..., dspy.Prediction]:
    """
    Create appropriate fallback function for a workflow phase.

    Args:
        phase: Phase name ('understanding', 'generation', 'validation')

    Returns:
        Fallback function that returns safe default

    """
    if phase == "understanding":

        def understanding_fallback(**kwargs):
            return dspy.Prediction(
                task_intent="Unable to analyze task - please provide more details",
                taxonomy_path="general/unknown",
                confidence_score=0.0,
                parent_skills=[],
                dependency_analysis={
                    "required": [],
                    "recommended": [],
                    "conflicts": [],
                    "rationale": "Analysis failed",
                },
            )

        return understanding_fallback

    elif phase == "generation":

        def generation_fallback(**kwargs):
            return dspy.Prediction(
                skill_content="# Error\n\nSkill generation failed. Please try again with more specific requirements.",
                usage_examples=[],
                best_practices=[],
                test_cases=[],
                estimated_reading_time=1,
                reference_files={},
                guide_files={},
                template_files={},
                script_files={},
            )

        return generation_fallback

    elif phase == "validation":

        def validation_fallback(**kwargs):
            return dspy.Prediction(
                validation_report={
                    "passed": False,
                    "checks": [],
                    "issues": ["Validation failed due to system error"],
                    "warnings": [],
                },
                critical_issues=[],
                warnings=[],
                suggestions=["Re-run validation after fixing system issues"],
                overall_score=0.0,
            )

        return validation_fallback

    else:
        # Generic fallback
        def generic_fallback(**kwargs):
            return dspy.Prediction(error="Phase execution failed")

        return generic_fallback
