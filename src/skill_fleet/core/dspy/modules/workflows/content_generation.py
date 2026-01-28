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

from skill_fleet.infrastructure.tracing.mlflow import (
    end_mlflow_run,
    get_mlflow_run_id,
    log_lm_usage,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)

from .....common.async_utils import run_async
from ..generation import (
    DEFAULT_SKILL_STYLE,
    Phase2GenerationModule,
)

if TYPE_CHECKING:
    import dspy

    from .....core.dspy.signatures.content_generation import SkillStyle

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
        # Check if we're in child run mode (parent already started MLflow run)
        is_child_run = get_mlflow_run_id() is not None if enable_mlflow else False

        if enable_mlflow and not is_child_run:
            setup_mlflow_experiment("content-generation-workflow")
            log_parameter("skill_style", skill_style)
            log_parameter("has_user_feedback", len(user_feedback) > 0)
        elif enable_mlflow and is_child_run:
            # In child mode, just log parameters to the active child run
            log_parameter("skill_style", skill_style)
            log_parameter("has_user_feedback", len(user_feedback) > 0)

        try:
            # Extract and map arguments to Phase2GenerationModule expectations
            skill_metadata = plan.get("skill_metadata")
            content_plan = plan.get("content_plan", "")
            generation_instructions = plan.get("generation_instructions", "")

            # Get dependency information from understanding
            dependencies = understanding.get("dependencies", {})
            # The dependency_analysis field contains the actual analysis text
            dependency_summaries = str(dependencies.get("dependency_analysis", ""))
            if not dependency_summaries or dependency_summaries == "None":
                # Fallback: build a summary from prerequisite/complementary skills
                prereqs = dependencies.get("prerequisite_skills", [])
                complementary = dependencies.get("complementary_skills", [])
                parts = []
                if prereqs:
                    parts.append(f"Prerequisites: {', '.join(prereqs)}")
                if complementary:
                    parts.append(f"Complementary: {', '.join(complementary)}")
                dependency_summaries = "\n".join(parts) if parts else "No specific dependencies"

            # Get parent skills content from taxonomy (if available)
            taxonomy = understanding.get("taxonomy", {})
            parent_skills_content = ""
            if taxonomy.get("parent_skills_content"):
                parent_skills_content = str(taxonomy.get("parent_skills_content", ""))
            elif taxonomy.get("recommended_path"):
                # Could load parent skills here, but for now use empty string
                parent_skills_content = ""

            # Generate content with correct argument mapping
            result = await self.generation_module.acall(
                skill_metadata=skill_metadata,
                content_plan=content_plan,
                generation_instructions=generation_instructions,
                parent_skills_content=parent_skills_content,
                dependency_summaries=dependency_summaries,
                skill_style=skill_style,
                user_feedback=user_feedback,
                change_requests="",
            )

            if enable_mlflow:
                log_phase_metrics(
                    "content_generation",
                    "complete",
                    {
                        "content_generated": float(bool(result.get("skill_content"))),
                        "extra_files_generated": float(bool(result.get("subdirectory_files"))),
                        "validation_performed": 0.0,  # Phase 2 doesn't perform validation
                    },
                )

                # Log LM usage from the prediction
                log_lm_usage(result, prefix="phase2_lm")

            return result

        except Exception as e:
            logger.exception(f"Error in content generation workflow: {e}")
            raise

        finally:
            if enable_mlflow and not is_child_run:
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
