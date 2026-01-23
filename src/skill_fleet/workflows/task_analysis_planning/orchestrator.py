"""
Task Analysis & Planning Workflow Orchestrator.

This orchestrator coordinates Phase 1 of the skill creation workflow:
1. Gather requirements from user task description
2. Analyze user intent and task goals
3. Find optimal taxonomy path
4. Analyze dependencies (prerequisites, complementary skills)
5. Synthesize a coherent execution plan

This orchestrator provides a clean interface that both the FastAPI app and CLI
can use, delegating to the underlying DSPy modules.
"""

from __future__ import annotations

import logging
from typing import Any

import dspy

from ...common.async_utils import run_async
from ...core.dspy.modules.phase1_understanding import Phase1UnderstandingModule
from ...core.tracing.mlflow import (
    end_mlflow_run,
    log_parameter,
    log_phase_artifact,
    log_phase_metrics,
    setup_mlflow_experiment,
)

logger = logging.getLogger(__name__)


class TaskAnalysisOrchestrator:
    """
    Orchestrator for the Task Analysis & Planning workflow (Phase 1).

    This class provides a high-level interface for coordinating the Phase 1 workflow,
    which includes gathering requirements, analyzing intent, finding taxonomy paths,
    analyzing dependencies, and synthesizing a plan.

    The orchestrator supports both synchronous and asynchronous execution, and
    integrates with MLflow for tracking and observability.

    Example:
        orchestrator = TaskAnalysisOrchestrator()
        result = await orchestrator.analyze(
            task_description="Create a Python decorators skill",
            user_context="I want to teach about @property and class decorators",
            taxonomy_structure="...",
            existing_skills=["python/async", "python/type-hints"],
        )

    """

    def __init__(self, task_lms: dict[str, dspy.LM] | None = None):
        """
        Initialize the Task Analysis orchestrator.

        Args:
            task_lms: Optional dictionary of task-specific LMs for different steps

        """
        self.task_lms = task_lms or {}
        self.understanding_module = Phase1UnderstandingModule()

    async def analyze(
        self,
        task_description: str,
        user_context: str = "",
        taxonomy_structure: str = "",
        existing_skills: list[str] | None = None,
        user_confirmation: str = "",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze the task and create a comprehensive understanding and plan.

        This method coordinates all Phase 1 activities:
        1. Gather requirements from the task description
        2. Analyze user intent and task goals
        3. Find the optimal taxonomy path for the skill
        4. Analyze dependencies and skill relationships
        5. Synthesize all findings into a coherent plan

        Args:
            task_description: User's task description (what they want to create)
            user_context: Additional context about the user's goals
            taxonomy_structure: Current taxonomy structure for path finding
            existing_skills: List of existing skill paths for dependency analysis
            user_confirmation: User's confirmation if this is a refinement
            enable_mlflow: Whether to track with MLflow (default: True)

        Returns:
            Dictionary containing:
                - requirements: Gathered requirements with domain, topics, constraints
                - intent: Analyzed task intent and success criteria
                - taxonomy: Recommended taxonomy path
                - dependencies: Prerequisite and complementary skills
                - plan: Synthesized skill creation plan with metadata

        """
        # Start MLflow run if enabled
        if enable_mlflow:
            setup_mlflow_experiment("task-analysis-workflow")
            log_parameter("task_description", task_description[:500])  # Truncate for logging
            log_parameter("user_context_length", len(user_context))
            log_parameter("existing_skills_count", len(existing_skills or []))

        # Normalize existing_skills to JSON string format expected by modules
        existing_skills_json = str(existing_skills or [])

        try:
            # Execute the Phase 1 understanding workflow
            result = await self.understanding_module.aforward(
                task_description=task_description,
                user_context=user_context,
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills_json,
                user_confirmation=user_confirmation,
            )

            # Log phase metrics if MLflow is enabled
            if enable_mlflow:
                log_phase_metrics("task_analysis", {
                    "requirements_gathered": bool(result.get("requirements")),
                    "intent_analyzed": bool(result.get("intent")),
                    "taxonomy_found": bool(result.get("taxonomy")),
                    "dependencies_analyzed": bool(result.get("dependencies")),
                    "plan_synthesized": bool(result.get("plan")),
                })

                # Log the plan as an artifact for review
                plan = result.get("plan", {})
                if plan:
                    skill_metadata = plan.get("skill_metadata")
                    if skill_metadata:
                        log_phase_artifact(
                            "skill_metadata",
                            f"Skill: {skill_metadata.get('name', 'N/A')}\n"
                            f"Type: {skill_metadata.get('type', 'N/A')}\n"
                            f"Path: {skill_metadata.get('taxonomy_path', 'N/A')}"
                        )

            return result

        except Exception as e:
            logger.exception(f"Error in task analysis workflow: {e}")
            raise

        finally:
            # End MLflow run
            if enable_mlflow:
                end_mlflow_run()

    def analyze_sync(
        self,
        task_description: str,
        user_context: str = "",
        taxonomy_structure: str = "",
        existing_skills: list[str] | None = None,
        user_confirmation: str = "",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Synchronous wrapper for analyze method.

        This provides a blocking interface for synchronous contexts,
        running the async analysis in the event loop.

        Args:
            Same as analyze() method

        Returns:
            Same as analyze() method

        """
        return run_async(
            lambda: self.analyze(
                task_description=task_description,
                user_context=user_context,
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
                user_confirmation=user_confirmation,
                enable_mlflow=enable_mlflow,
            )
        )

    def get_requirements(
        self,
        task_description: str,
        enable_mlflow: bool = False,
    ) -> dict[str, Any]:
        """
        Quick requirements gathering without full analysis.

        This is a lightweight method for scenarios where you only need
        to understand the requirements (domain, topics, constraints) without
        the full planning workflow.

        Args:
            task_description: User's task description
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with requirements information

        """
        # Use only the gather requirements step
        from ...core.dspy.modules.phase1_understanding import RequirementsGathererModule

        gatherer = RequirementsGathererModule()

        if enable_mlflow:
            setup_mlflow_experiment("task-analysis-workflow")

        try:
            result = gatherer.forward(task_description=task_description)
            return result
        finally:
            if enable_mlflow:
                end_mlflow_run()

    def get_taxonomy_path(
        self,
        task_description: str,
        taxonomy_structure: str,
        existing_skills: list[str] | None = None,
        enable_mlflow: bool = False,
    ) -> dict[str, Any]:
        """
        Get the recommended taxonomy path for a skill.

        This is a lightweight method for scenarios where you only need to find
        where in the taxonomy a skill should be placed.

        Args:
            task_description: User's task description
            taxonomy_structure: Current taxonomy structure
            existing_skills: List of existing skill paths
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with recommended taxonomy path

        """
        from ...core.dspy.modules.phase1_understanding import TaxonomyPathFinderModule

        finder = TaxonomyPathFinderModule()
        existing_skills_json = str(existing_skills or [])
        existing_skill_paths = [str(s) for s in existing_skills_json]

        if enable_mlflow:
            setup_mlflow_experiment("task-analysis-workflow")

        try:
            result = finder.forward(
                task_description=task_description,
                taxonomy_structure=taxonomy_structure,
                existing_skills=str(existing_skill_paths),
            )
            return result
        finally:
            if enable_mlflow:
                end_mlflow_run()


# Export main orchestrator class
__all__ = ["TaskAnalysisOrchestrator"]
