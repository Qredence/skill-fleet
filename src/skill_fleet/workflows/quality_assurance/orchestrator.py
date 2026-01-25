"""
Quality Assurance Workflow Orchestrator.

Orchestrates Phase 3 of the skill creation workflow:
- Validating skill content against quality rules
- Refining based on validation feedback
- Assessing overall quality and audience alignment

This provides a clean interface for quality assurance that both API and CLI can use.
"""

from __future__ import annotations

import logging
from typing import Any

import dspy

from ...common.async_utils import run_async
from ...core.dspy.modules.validation import Phase3ValidationModule
from ...core.tracing.mlflow import (
    end_mlflow_run,
    get_mlflow_run_id,
    log_lm_usage,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)

logger = logging.getLogger(__name__)


class QualityAssuranceOrchestrator:
    """
    Orchestrator for the Quality Assurance workflow (Phase 3).

    This orchestrator coordinates validation, refinement, and quality assessment
    of skill content. It ensures generated skills meet quality standards and
    handles iterative refinement when needed.

    Example:
        orchestrator = QualityAssuranceOrchestrator()
        result = await orchestrator.validate_and_refine(
            skill_content=...,
            skill_metadata=...,
            content_plan=...,
            validation_rules=...,
        )

    """

    def __init__(self, task_lms: dict[str, dspy.LM] | None = None):
        """Initialize the orchestrator."""
        self.task_lms = task_lms or {}
        self.validation_module = Phase3ValidationModule()

    async def validate_and_refine(
        self,
        skill_content: str,
        skill_metadata: Any,
        content_plan: str,
        validation_rules: str,
        user_feedback: str = "",
        target_level: str = "intermediate",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Validate and refine skill content.

        Args:
            skill_content: The SKILL.md content to validate
            skill_metadata: Skill metadata for context
            content_plan: Original content plan for comparison
            validation_rules: Validation rules and criteria
            user_feedback: Optional user feedback for refinement
            target_level: Target complexity level (beginner, intermediate, advanced)
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with validation results including:
            - validation_report: Detailed validation report
            - refined_content: Refined skill content
            - critical_issues: List of critical issues
            - warnings: List of warnings
            - quality_assessment: Quality assessment results

        """
        # Check if we're in child run mode (parent already started MLflow run)
        is_child_run = get_mlflow_run_id() is not None if enable_mlflow else False

        if enable_mlflow and not is_child_run:
            setup_mlflow_experiment("quality-assurance-workflow")
            log_parameter("target_level", target_level)
            log_parameter("has_user_feedback", len(user_feedback) > 0)
        elif enable_mlflow and is_child_run:
            # In child mode, just log parameters to the active child run
            log_parameter("target_level", target_level)
            log_parameter("has_user_feedback", len(user_feedback) > 0)

        try:
            result = await self.validation_module.aforward(
                skill_content=skill_content,
                skill_metadata=skill_metadata,
                content_plan=content_plan,
                validation_rules=validation_rules,
                user_feedback=user_feedback,
                target_level=target_level,
            )

            if enable_mlflow:
                validation_passed = result.get("validation_report", {}).get("passed", False)
                quality_score = result.get("quality_assessment", {}).get("calibrated_score", 0.0)
                log_phase_metrics("quality_assurance", "complete", {
                    "validation_passed": float(validation_passed),
                    "quality_score": quality_score,
                    "issues_count": float(len(result.get("critical_issues", []))),
                    "refinement_performed": float("refined_content" in result),
                })

                # Log LM usage from the prediction
                log_lm_usage(result, prefix="phase3_lm")

            return result

        except Exception as e:
            logger.exception(f"Error in quality assurance workflow: {e}")
            raise

        finally:
            if enable_mlflow and not is_child_run:
                end_mlflow_run()

    def validate_and_refine_sync(
        self,
        skill_content: str,
        skill_metadata: Any,
        content_plan: str,
        validation_rules: str,
        user_feedback: str = "",
        target_level: str = "intermediate",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """Synchronous wrapper for validate_and_refine method."""
        return run_async(
            lambda: self.validate_and_refine(
                skill_content=skill_content,
                skill_metadata=skill_metadata,
                content_plan=content_plan,
                validation_rules=validation_rules,
                user_feedback=user_feedback,
                target_level=target_level,
                enable_mlflow=enable_mlflow,
            )
        )


__all__ = ["QualityAssuranceOrchestrator"]
