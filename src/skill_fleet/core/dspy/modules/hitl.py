"""DSPy modules for Human-in-the-Loop (HITL) interactions.

These modules wrap HITL signatures with appropriate DSPy module types:
- Predict: For straightforward transformations
- ChainOfThought: For reasoning-heavy tasks

All modules support async execution via aforward().

Note:
    DSPy discourages calling `.forward(...)` directly. For async execution we
    prefer awaiting `.acall(...)` on the underlying DSPy primitives.
"""

from __future__ import annotations

import logging
from typing import Any

import dspy

from ..signatures.hitl import (
    AnalyzeFeedback,
    AssessReadiness,
    DetermineHITLStrategy,
    FormatValidationResults,
    GenerateClarifyingQuestions,
    GeneratePreview,
    GenerateRefinementPlan,
    SummarizeUnderstanding,
)

logger = logging.getLogger(__name__)


def _get_arg(kwargs: dict[str, Any], args: tuple, key: str, index: int) -> Any:
    """Helper to extract argument from kwargs or positional args safely.

    Prevents "tuple index out of range" when a falsy kwarg (e.g. empty string)
    causes fallback to a non-existent positional arg.
    """
    if key in kwargs:
        return kwargs[key]
    if len(args) > index:
        return args[index]
    return None


# =============================================================================
# Phase 1 HITL Modules
# =============================================================================


class ClarifyingQuestionsModule(dspy.Module):
    """Generate clarifying questions to understand user intent better.

    Uses ChainOfThought for reasoning about what questions are most valuable.
    """

    def __init__(self):
        super().__init__()
        self.generate_questions = dspy.ChainOfThought(GenerateClarifyingQuestions)

    def forward(
        self, task_description: str, initial_analysis: str, ambiguities: list[str]
    ) -> dict[str, Any]:
        """Generate 2-3 focused clarifying questions.

        Returns:
            Dict with: questions, priority, rationale
        """
        result = self.generate_questions(
            task_description=task_description,
            initial_analysis=initial_analysis,
            ambiguities=ambiguities,
        )

        return {
            "questions": result.questions,
            "priority": result.priority,
            "rationale": getattr(result, "rationale", ""),  # From ChainOfThought
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        task_description = _get_arg(kwargs, args, "task_description", 0)
        initial_analysis = _get_arg(kwargs, args, "initial_analysis", 1)
        ambiguities = _get_arg(kwargs, args, "ambiguities", 2)

        result = await self.generate_questions.acall(
            task_description=task_description,
            initial_analysis=initial_analysis,
            ambiguities=ambiguities,
        )
        return {
            "questions": result.questions,
            "priority": result.priority,
            "rationale": getattr(result, "rationale", ""),
        }


class ConfirmUnderstandingModule(dspy.Module):
    """Summarize understanding for user confirmation.

    Uses Predict for fast summary generation.
    """

    def __init__(self):
        super().__init__()
        self.summarize = dspy.Predict(SummarizeUnderstanding)

    def forward(
        self,
        task_description: str,
        user_clarifications: str,
        intent_analysis: str,
        taxonomy_path: str,
        dependencies: list[str],
    ) -> dict[str, Any]:
        """Generate confirmation summary.

        Returns:
            Dict with: summary, key_assumptions, confidence
        """
        result = self.summarize(
            task_description=task_description,
            user_clarifications=user_clarifications,
            intent_analysis=intent_analysis,
            taxonomy_path=taxonomy_path,
            dependencies=dependencies,
        )

        return {
            "summary": result.summary,
            "key_assumptions": result.key_assumptions,
            "confidence": result.confidence,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        # Preserve positional/kw calling flexibility.
        task_description = _get_arg(kwargs, args, "task_description", 0)
        user_clarifications = _get_arg(kwargs, args, "user_clarifications", 1)
        intent_analysis = _get_arg(kwargs, args, "intent_analysis", 2)
        taxonomy_path = _get_arg(kwargs, args, "taxonomy_path", 3)
        dependencies = _get_arg(kwargs, args, "dependencies", 4)

        result = await self.summarize.acall(
            task_description=task_description,
            user_clarifications=user_clarifications,
            intent_analysis=intent_analysis,
            taxonomy_path=taxonomy_path,
            dependencies=dependencies,
        )
        return {
            "summary": result.summary,
            "key_assumptions": result.key_assumptions,
            "confidence": result.confidence,
        }


# =============================================================================
# Phase 2 HITL Modules
# =============================================================================


class PreviewGeneratorModule(dspy.Module):
    """Generate preview of skill content for user review.

    Uses Predict for fast preview generation.
    """

    def __init__(self):
        super().__init__()
        self.generate_preview = dspy.Predict(GeneratePreview)

    def forward(self, skill_content: str, metadata: str) -> dict[str, Any]:
        """Generate content preview.

        Returns:
            Dict with: preview, highlights, potential_issues
        """
        result = self.generate_preview(skill_content=skill_content, metadata=metadata)

        return {
            "preview": result.preview,
            "highlights": result.highlights,
            "potential_issues": result.potential_issues,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        skill_content = _get_arg(kwargs, args, "skill_content", 0)
        metadata = _get_arg(kwargs, args, "metadata", 1)

        result = await self.generate_preview.acall(skill_content=skill_content, metadata=metadata)
        return {
            "preview": result.preview,
            "highlights": result.highlights,
            "potential_issues": result.potential_issues,
        }


class FeedbackAnalyzerModule(dspy.Module):
    """Analyze user feedback and determine changes needed.

    Uses ChainOfThought to reason about feedback and extract actionable changes.
    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeFeedback)

    def forward(self, user_feedback: str, current_content: str) -> dict[str, Any]:
        """Analyze feedback and generate change requests.

        Returns:
            Dict with: change_requests, scope_change, estimated_effort, reasoning
        """
        result = self.analyze(user_feedback=user_feedback, current_content=current_content)

        return {
            "change_requests": result.change_requests,
            "scope_change": result.scope_change,
            "estimated_effort": result.estimated_effort,
            "reasoning": getattr(result, "rationale", ""),  # From ChainOfThought
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        user_feedback = _get_arg(kwargs, args, "user_feedback", 0)
        current_content = _get_arg(kwargs, args, "current_content", 1)

        result = await self.analyze.acall(
            user_feedback=user_feedback, current_content=current_content
        )
        return {
            "change_requests": result.change_requests,
            "scope_change": result.scope_change,
            "estimated_effort": result.estimated_effort,
            "reasoning": getattr(result, "rationale", ""),
        }


# =============================================================================
# Phase 3 HITL Modules
# =============================================================================


class ValidationFormatterModule(dspy.Module):
    """Format validation results for human-readable display.

    Uses Predict for fast formatting.
    """

    def __init__(self):
        super().__init__()
        self.format_results = dspy.Predict(FormatValidationResults)

    def forward(self, validation_report: str, skill_content: str) -> dict[str, Any]:
        """Format validation results.

        Returns:
            Dict with: formatted_report, critical_issues, warnings, auto_fixable
        """
        result = self.format_results(
            validation_report=validation_report, skill_content=skill_content
        )

        return {
            "formatted_report": result.formatted_report,
            "critical_issues": result.critical_issues,
            "warnings": result.warnings,
            "auto_fixable": result.auto_fixable,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        validation_report = _get_arg(kwargs, args, "validation_report", 0)
        skill_content = _get_arg(kwargs, args, "skill_content", 1)

        result = await self.format_results.acall(
            validation_report=validation_report,
            skill_content=skill_content,
        )
        return {
            "formatted_report": result.formatted_report,
            "critical_issues": result.critical_issues,
            "warnings": result.warnings,
            "auto_fixable": result.auto_fixable,
        }


class RefinementPlannerModule(dspy.Module):
    """Generate refinement plan based on validation and feedback.

    Uses ChainOfThought to reason about optimal refinement strategy.
    """

    def __init__(self):
        super().__init__()
        self.plan_refinement = dspy.ChainOfThought(GenerateRefinementPlan)

    def forward(
        self, validation_issues: str, user_feedback: str, current_skill: str
    ) -> dict[str, Any]:
        """Generate refinement plan.

        Returns:
            Dict with: refinement_plan, changes, estimated_iterations, reasoning
        """
        result = self.plan_refinement(
            validation_issues=validation_issues,
            user_feedback=user_feedback,
            current_skill=current_skill,
        )

        return {
            "refinement_plan": result.refinement_plan,
            "changes": result.changes,
            "estimated_iterations": result.estimated_iterations,
            "reasoning": getattr(result, "rationale", ""),  # From ChainOfThought
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        validation_issues = _get_arg(kwargs, args, "validation_issues", 0)
        user_feedback = _get_arg(kwargs, args, "user_feedback", 1)
        current_skill = _get_arg(kwargs, args, "current_skill", 2)

        result = await self.plan_refinement.acall(
            validation_issues=validation_issues,
            user_feedback=user_feedback,
            current_skill=current_skill,
        )
        return {
            "refinement_plan": result.refinement_plan,
            "changes": result.changes,
            "estimated_iterations": result.estimated_iterations,
            "reasoning": getattr(result, "rationale", ""),
        }


# =============================================================================
# Universal HITL Utilities
# =============================================================================


class ReadinessAssessorModule(dspy.Module):
    """Assess readiness to proceed to next phase.

    Uses Predict for fast assessment.
    """

    def __init__(self):
        super().__init__()
        self.assess = dspy.Predict(AssessReadiness)

    def forward(self, phase: str, collected_info: str, min_requirements: str) -> dict[str, Any]:
        """Assess if ready to proceed.

        Returns:
            Dict with: ready, readiness_score, missing_info, next_questions
        """
        result = self.assess(
            phase=phase, collected_info=collected_info, min_requirements=min_requirements
        )

        return {
            "ready": result.ready,
            "readiness_score": result.readiness_score,
            "missing_info": result.missing_info,
            "next_questions": result.next_questions,
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        phase = _get_arg(kwargs, args, "phase", 0)
        collected_info = _get_arg(kwargs, args, "collected_info", 1)
        min_requirements = _get_arg(kwargs, args, "min_requirements", 2)

        result = await self.assess.acall(
            phase=phase,
            collected_info=collected_info,
            min_requirements=min_requirements,
        )
        return {
            "ready": result.ready,
            "readiness_score": result.readiness_score,
            "missing_info": result.missing_info,
            "next_questions": result.next_questions,
        }


class HITLStrategyModule(dspy.Module):
    """Determine optimal HITL strategy for a task.

    Uses ChainOfThought to reason about optimal checkpoint selection.
    """

    def __init__(self):
        super().__init__()
        self.determine_strategy = dspy.ChainOfThought(DetermineHITLStrategy)

    def forward(
        self, task_description: str, task_complexity: str, user_preferences: str
    ) -> dict[str, Any]:
        """Determine HITL strategy.

        Returns:
            Dict with: strategy, checkpoints, reasoning
        """
        result = self.determine_strategy(
            task_description=task_description,
            task_complexity=task_complexity,
            user_preferences=user_preferences,
        )

        return {
            "strategy": result.strategy,
            "checkpoints": result.checkpoints,
            "reasoning": getattr(result, "rationale", ""),  # From ChainOfThought
        }

    async def aforward(self, *args, **kwargs) -> dict[str, Any]:
        """Async version using DSPy `.acall(...)` (preferred)."""
        task_description = _get_arg(kwargs, args, "task_description", 0)
        task_complexity = _get_arg(kwargs, args, "task_complexity", 1)
        user_preferences = _get_arg(kwargs, args, "user_preferences", 2)

        result = await self.determine_strategy.acall(
            task_description=task_description,
            task_complexity=task_complexity,
            user_preferences=user_preferences,
        )
        return {
            "strategy": result.strategy,
            "checkpoints": result.checkpoints,
            "reasoning": getattr(result, "rationale", ""),
        }
