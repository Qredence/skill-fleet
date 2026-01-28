"""
Signature Optimization Workflow Orchestrator.

Orchestrates signature tuning and optimization workflow.
Provides a clean interface for signature improvement that both API and CLI can use.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from skill_fleet.infrastructure.tracing.mlflow import (
    end_mlflow_run,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)

from .....common.async_utils import run_async
from ..signature_tuner import SignatureTuner

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


class SignatureTuningOrchestrator:
    """
    Orchestrator for the Signature Optimization workflow.

    This orchestrator manages signature tuning to improve skill quality scores.
    It analyzes failures, proposes improvements, and tracks version history.

    Example:
        orchestrator = SignatureTuningOrchestrator()
        result = await orchestrator.tune_signature(
            skill_content=...,
            current_signature=...,
            metric_score=0.65,
        )

    """

    def __init__(
        self,
        task_lms: dict[str, dspy.LM] | None = None,
        improvement_threshold: float = 0.05,
        max_iterations: int = 3,
        quality_threshold: float = 0.75,
    ):
        """
        Initialize orchestrator.

        Args:
            task_lms: Optional task-specific LMs
            improvement_threshold: Minimum improvement required to accept
            max_iterations: Maximum tuning iterations per session
            quality_threshold: Score below which tuning is triggered

        """
        self.task_lms = task_lms or {}
        self.improvement_threshold = improvement_threshold
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.tuner = SignatureTuner(
            improvement_threshold=improvement_threshold,
            max_iterations=max_iterations,
            quality_threshold=quality_threshold,
        )

    async def tune_signature(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float = 0.80,
        skill_type: str = "comprehensive",
        signature_id: str | None = None,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Tune a signature to improve quality scores.

        Args:
            skill_content: The generated skill content
            current_signature: The signature that generated this content
            metric_score: Current quality score (0.0-1.0)
            target_score: Target quality score (default: 0.80)
            skill_type: Type of skill (navigation_hub, comprehensive, minimal)
            signature_id: Optional ID for version tracking
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with tuning results including:
            - tuning_needed: Whether tuning was required
            - proposed_signature: Improved signature (if needed)
            - failure_analysis: Analysis of why tuning was needed
            - version_history: Version tracking information

        """
        if enable_mlflow:
            setup_mlflow_experiment("signature-tuning")
            log_parameter("skill_type", skill_type)
            log_parameter("current_score", metric_score)
            log_parameter("target_score", target_score)

        try:
            result = await self.tuner.acall(
                skill_content=skill_content,
                current_signature=current_signature,
                metric_score=metric_score,
                target_score=target_score,
                skill_type=skill_type,
                signature_id=signature_id,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "signature_tuning",
                    "complete",
                    {
                        "tuning_needed": result.get("tuning_needed", False),
                        "current_score": metric_score,
                        "accept_improvement": result.get("accept_improvement", False),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error in signature tuning workflow: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def tune_iteratively(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float = 0.80,
        skill_type: str = "comprehensive",
        re_evaluate_fn: Any | None = None,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Iteratively tune signature until target score is reached or max iterations.

        Args:
            skill_content: The generated skill content
            current_signature: The signature that generated this content
            metric_score: Current quality score (0.0-1.0)
            target_score: Target quality score (default: 0.80)
            skill_type: Type of skill for context
            re_evaluate_fn: Optional function to re-evaluate after tuning
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with final tuning results and iteration history

        """
        if enable_mlflow:
            setup_mlflow_experiment("signature-tuning-iterative")
            log_parameter("max_iterations", self.max_iterations)

        try:
            result = await self.tuner.aforward_iterative(
                skill_content=skill_content,
                current_signature=current_signature,
                metric_score=metric_score,
                target_score=target_score,
                skill_type=skill_type,
                re_evaluate_fn=re_evaluate_fn,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "iterative_tuning",
                    "complete",
                    {
                        "iterations_used": result.get("iterations_used", 0),
                        "target_reached": result.get("target_reached", False),
                        "total_improvement": result.get("total_improvement", 0.0),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error in iterative signature tuning: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    def get_version_history(
        self,
        signature_id: str,
    ) -> dict[str, Any] | None:
        """
        Get version history for a signature.

        Args:
            signature_id: ID of the signature

        Returns:
            Version history dictionary or None if not found

        """
        history = self.tuner._version_histories.get(signature_id)
        return history.to_dict() if history else None

    # Synchronous wrappers
    def tune_signature_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for tune_signature."""
        return run_async(lambda: self.tune_signature(*args, **kwargs))

    def tune_iteratively_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for tune_iteratively."""
        return run_async(lambda: self.tune_iteratively(*args, **kwargs))


__all__ = ["SignatureTuningOrchestrator"]
