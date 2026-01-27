"""
Human-in-the-Loop Checkpoint Manager.

Manages HITL checkpoints throughout the skill creation workflow.
Provides a clean interface for checkpoint interactions that both API and CLI can use.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from .....common.async_utils import run_async
from .....core.tracing.mlflow import (
    end_mlflow_run,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)
from ..hitl import (
    ClarifyingQuestionsModule,
    ConfirmUnderstandingModule,
    FeedbackAnalyzerModule,
    HITLStrategyModule,
    PreviewGeneratorModule,
    ReadinessAssessorModule,
    RefinementPlannerModule,
    ValidationFormatterModule,
)

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


class CheckpointPhase(Enum):
    """Phases where HITL checkpoints can occur."""

    PHASE1_UNDERSTANDING = "phase1_understanding"
    PHASE2_CONTENT_GENERATION = "phase2_content_generation"
    PHASE3_VALIDATION = "phase3_validation"


@dataclass
class Checkpoint:
    """Represents a single HITL checkpoint."""

    checkpoint_id: str
    phase: CheckpointPhase
    checkpoint_type: str
    status: str = "pending"  # pending, waiting, approved, rejected
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: dict[str, Any] = field(default_factory=dict)
    user_response: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "phase": self.phase.value,
            "checkpoint_type": self.checkpoint_type,
            "status": self.status,
            "created_at": self.created_at,
            "data": self.data,
            "user_response": self.user_response,
            "metadata": self.metadata,
        }


class HITLCheckpointManager:
    """
    Manager for Human-in-the-Loop checkpoints.

    This orchestrator handles all HITL interactions including:
    - Determining optimal HITL strategy for a task
    - Generating clarifying questions
    - Creating previews for user review
    - Processing user feedback
    - Formatting validation results
    - Managing checkpoint state

    Example:
        manager = HITLCheckpointManager()
        strategy = await manager.determine_strategy(task_description, complexity)
        questions = await manager.generate_clarifying_questions(...)

    """

    def __init__(self, task_lms: dict[str, dspy.LM] | None = None):
        """Initialize the checkpoint manager."""
        self.task_lms = task_lms or {}
        self.checkpoints: dict[str, Checkpoint] = {}

        # Initialize HITL modules
        self.strategy_module = HITLStrategyModule()
        self.clarifying_questions_module = ClarifyingQuestionsModule()
        self.confirm_understanding_module = ConfirmUnderstandingModule()
        self.preview_generator_module = PreviewGeneratorModule()
        self.feedback_analyzer_module = FeedbackAnalyzerModule()
        self.validation_formatter_module = ValidationFormatterModule()
        self.refinement_planner_module = RefinementPlannerModule()
        self.readiness_assessor_module = ReadinessAssessorModule()

    async def determine_strategy(
        self,
        task_description: str,
        task_complexity: str = "intermediate",
        user_preferences: str = "",
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Determine optimal HITL strategy for a task.

        Args:
            task_description: Description of the task
            task_complexity: Complexity level (beginner, intermediate, advanced)
            user_preferences: User preferences for HITL
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with strategy and recommended checkpoints

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-strategy")
            log_parameter("task_complexity", task_complexity)

        try:
            result = await self.strategy_module.acall(
                task_description=task_description,
                task_complexity=task_complexity,
                user_preferences=user_preferences,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "hitl_strategy",
                    {
                        "strategy": result.get("strategy", ""),
                        "checkpoint_count": len(result.get("checkpoints", [])),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error determining HITL strategy: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def generate_clarifying_questions(
        self,
        task_description: str,
        initial_analysis: str,
        ambiguities: list[str],
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate clarifying questions to understand user intent.

        Args:
            task_description: User's task description
            initial_analysis: Initial analysis of the task
            ambiguities: List of identified ambiguities
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with questions, priority, and rationale

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-clarifying-questions")
            log_parameter("ambiguity_count", len(ambiguities))

        try:
            result = await self.clarifying_questions_module.acall(
                task_description=task_description,
                initial_analysis=initial_analysis,
                ambiguities=ambiguities,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "clarifying_questions",
                    {
                        "question_count": len(result.get("questions", [])),
                        "priority": result.get("priority", ""),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error generating clarifying questions: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def confirm_understanding(
        self,
        task_description: str,
        user_clarifications: str,
        intent_analysis: str,
        taxonomy_path: str,
        dependencies: list[str],
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate confirmation summary for user.

        Args:
            task_description: Original task description
            user_clarifications: User's clarifications
            intent_analysis: Analysis of user intent
            taxonomy_path: Determined taxonomy path
            dependencies: List of identified dependencies
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with summary, assumptions, and confidence

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-confirm-understanding")
            log_parameter("has_dependencies", len(dependencies) > 0)

        try:
            result = await self.confirm_understanding_module.acall(
                task_description=task_description,
                user_clarifications=user_clarifications,
                intent_analysis=intent_analysis,
                taxonomy_path=taxonomy_path,
                dependencies=dependencies,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "confirm_understanding",
                    {
                        "confidence": result.get("confidence", 0.0),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error confirming understanding: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def generate_preview(
        self,
        skill_content: str,
        metadata: str,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate preview of skill content for user review.

        Args:
            skill_content: Generated skill content
            metadata: Skill metadata
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with preview, highlights, and potential issues

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-preview")

        try:
            result = await self.preview_generator_module.acall(
                skill_content=skill_content,
                metadata=metadata,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "preview_generation",
                    {
                        "has_issues": len(result.get("potential_issues", [])) > 0,
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error generating preview: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def analyze_feedback(
        self,
        user_feedback: str,
        current_content: str,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze user feedback and determine changes needed.

        Args:
            user_feedback: User's feedback on the content
            current_content: Current content being reviewed
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with change requests and estimated effort

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-analyze-feedback")

        try:
            result = await self.feedback_analyzer_module.acall(
                user_feedback=user_feedback,
                current_content=current_content,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "feedback_analysis",
                    {
                        "change_count": len(result.get("change_requests", [])),
                        "scope_change": result.get("scope_change", ""),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error analyzing feedback: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def format_validation_results(
        self,
        validation_report: str,
        skill_content: str,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Format validation results for human-readable display.

        Args:
            validation_report: Validation report
            skill_content: Skill content that was validated
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with formatted report and categorized issues

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-format-validation")

        try:
            result = await self.validation_formatter_module.acall(
                validation_report=validation_report,
                skill_content=skill_content,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "validation_formatting",
                    {
                        "critical_issues": len(result.get("critical_issues", [])),
                        "warnings": len(result.get("warnings", [])),
                        "auto_fixable": len(result.get("auto_fixable", [])),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error formatting validation results: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def plan_refinement(
        self,
        validation_issues: str,
        user_feedback: str,
        current_skill: str,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate refinement plan based on validation and feedback.

        Args:
            validation_issues: Issues from validation
            user_feedback: User feedback for refinement
            current_skill: Current skill content
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with refinement plan and estimated iterations

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-refinement-planning")

        try:
            result = await self.refinement_planner_module.acall(
                validation_issues=validation_issues,
                user_feedback=user_feedback,
                current_skill=current_skill,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "refinement_planning",
                    {
                        "estimated_iterations": result.get("estimated_iterations", 0),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error planning refinement: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def assess_readiness(
        self,
        phase: str,
        collected_info: str,
        min_requirements: str,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Assess readiness to proceed to next phase.

        Args:
            phase: Current phase
            collected_info: Information collected so far
            min_requirements: Minimum requirements to proceed
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with readiness assessment and missing info

        """
        if enable_mlflow:
            setup_mlflow_experiment("hitl-readiness-assessment")
            log_parameter("phase", phase)

        try:
            result = await self.readiness_assessor_module.acall(
                phase=phase,
                collected_info=collected_info,
                min_requirements=min_requirements,
            )

            if enable_mlflow:
                log_phase_metrics(
                    "readiness_assessment",
                    {
                        "ready": result.get("ready", False),
                        "readiness_score": result.get("readiness_score", 0.0),
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"Error assessing readiness: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    def create_checkpoint(
        self,
        phase: CheckpointPhase,
        checkpoint_type: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> Checkpoint:
        """
        Create a new checkpoint.

        Args:
            phase: Phase where checkpoint occurs
            checkpoint_type: Type of checkpoint
            data: Data associated with checkpoint
            metadata: Optional metadata

        Returns:
            Created checkpoint

        """
        import uuid

        checkpoint_id = str(uuid.uuid4())[:12]
        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            phase=phase,
            checkpoint_type=checkpoint_type,
            data=data,
            metadata=metadata or {},
        )
        self.checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> Checkpoint | None:
        """Get checkpoint by ID."""
        return self.checkpoints.get(checkpoint_id)

    def update_checkpoint_status(
        self,
        checkpoint_id: str,
        status: str,
        user_response: dict[str, Any] | None = None,
    ) -> bool:
        """
        Update checkpoint status.

        Args:
            checkpoint_id: Checkpoint ID
            status: New status
            user_response: Optional user response

        Returns:
            True if updated, False if checkpoint not found

        """
        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint:
            checkpoint.status = status
            checkpoint.user_response = user_response
            return True
        return False

    # Synchronous wrappers
    def determine_strategy_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for determine_strategy."""
        return run_async(lambda: self.determine_strategy(*args, **kwargs))

    def generate_clarifying_questions_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for generate_clarifying_questions."""
        return run_async(lambda: self.generate_clarifying_questions(*args, **kwargs))

    def confirm_understanding_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for confirm_understanding."""
        return run_async(lambda: self.confirm_understanding(*args, **kwargs))

    def generate_preview_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for generate_preview."""
        return run_async(lambda: self.generate_preview(*args, **kwargs))

    def analyze_feedback_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for analyze_feedback."""
        return run_async(lambda: self.analyze_feedback(*args, **kwargs))

    def format_validation_results_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for format_validation_results."""
        return run_async(lambda: self.format_validation_results(*args, **kwargs))

    def plan_refinement_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for plan_refinement."""
        return run_async(lambda: self.plan_refinement(*args, **kwargs))

    def assess_readiness_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for assess_readiness."""
        return run_async(lambda: self.assess_readiness(*args, **kwargs))


__all__ = ["HITLCheckpointManager", "Checkpoint", "CheckpointPhase"]
