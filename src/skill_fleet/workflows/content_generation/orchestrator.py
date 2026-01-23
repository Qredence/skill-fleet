"""
Content Generation Workflow Orchestrator.

Orchestrates Phase 2 of the skill creation workflow:
- Generating skill content based on the plan
- Supporting different skill styles (navigation_hub, comprehensive, minimal)
- Incorporating user feedback for refinement
- Generating skill sections and capability implementations

This provides a clean interface for content generation that both API and CLI can use.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ...common.async_utils import run_async

if TYPE_CHECKING:
    import dspy
from ...core.dspy.modules.generation import (
    DEFAULT_SKILL_STYLE,
    Phase2GenerationModule,
)
from ...core.tracing.mlflow import (
    end_mlflow_run,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)
from ...core.dspy.signatures.content_generation import SkillStyle

logger = logging.getLogger(__name__)


class ContentGenerationOrchestrator:
    """
    Orchestrator for the Content Generation workflow (Phase 2).

    This orchestrator coordinates the generation of skill content including
    the main SKILL.md file, examples, best practices, and supporting sections.

    Example:
        orchestrator = ContentGenerationOrchestrator()
        result = await orchestrator.generate(
            understanding=...,
            plan=...,
            skill_style="comprehensive",
            user_feedback="",
        )

    """

    def __init__(self, task_lms: dict[str, dspy.LM] | None = None):
        """Initialize the orchestrator."""
        self.task_lms = task_lms or {}
        self.generation_module = Phase2GenerationModule()

    async def generate(
        self,
        understanding: dict[str, Any],
        plan: dict[str, Any],
        skill_style: SkillStyle = DEFAULT_SKILL_STYLE,
        user_feedback: str = "",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate skill content based on the understanding and plan.

        Args:
            understanding: Phase 1 understanding result
            plan: Synthesized plan from Phase 1
            skill_style: Style of skill to generate
            user_feedback: Optional feedback for refinement
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with generated content including:
            - skill_content: Main SKILL.md content
            - extra_files: Supporting files (examples, best_practices, etc.)
            - validation_report: Initial validation results

        """
        if enable_mlflow:
            setup_mlflow_experiment("content-generation-workflow")
            log_parameter("skill_style", skill_style)
            log_parameter("has_user_feedback", len(user_feedback) > 0)

        try:
            # Extract key information from understanding and plan
            task_description = understanding.get("task_description", "")
            taxonomy_path = plan.get("taxonomy_path", "")

            # Generate content
            result = await self.generation_module.aforward(
                understanding=understanding,
                plan=plan,
                skill_style=skill_style,
                user_feedback=user_feedback,
            )

            if enable_mlflow:
                log_phase_metrics("content_generation", {
                    "content_generated": bool(result.get("content")),
                    "extra_files_generated": bool(result.get("extra_files")),
                    "validation_performed": bool(result.get("validation_report")),
                })

            return result

        except Exception as e:
            logger.exception(f"Error in content generation workflow: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    def generate_sync(
        self,
        understanding: dict[str, Any],
        plan: dict[str, Any],
        skill_style: SkillStyle = DEFAULT_SKILL_STYLE,
        user_feedback: str = "",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """Synchronous wrapper for generate method."""
        return run_async(
            lambda: self.generate(
                understanding=understanding,
                plan=plan,
                skill_style=skill_style,
                user_feedback=user_feedback,
                enable_mlflow=enable_mlflow,
            )
        )


__all__ = ["ContentGenerationOrchestrator"]
