"""Feedback and presentation modules."""

from __future__ import annotations

import json
import logging

import dspy

from .....common.utils import safe_json_loads
from ...signatures.conversational_interface import (
    PresentSkillForReview,
    ProcessUserFeedback,
)

logger = logging.getLogger(__name__)


class PresentSkillModule(dspy.Module):
    """Module for presenting skill results using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.present = dspy.ChainOfThought(PresentSkillForReview)

    def forward(
        self,
        skill_content: str,
        skill_metadata: dict | str,
        validation_report: dict | str,
    ) -> dspy.Prediction:
        """Present skill for review.

        Args:
            skill_content: The skill content to present.
            skill_metadata: Metadata about the skill.
            validation_report: Validation report for the skill.

        Returns:
            Prediction with presentation results.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )
        report_str = (
            json.dumps(validation_report, indent=2)
            if isinstance(validation_report, dict)
            else validation_report
        )

        result = self.present(
            skill_content=skill_content,
            skill_metadata=metadata_str,
            validation_report=report_str,
        )

        highlights = safe_json_loads(
            getattr(result, "key_highlights", []), default=[], field_name="key_highlights"
        )
        if isinstance(highlights, dict):
            highlights = []
        if not isinstance(highlights, list):
            highlights = [str(highlights)] if highlights else []

        questions = safe_json_loads(
            getattr(result, "suggested_questions", []),
            default=[],
            field_name="suggested_questions",
        )
        if isinstance(questions, dict):
            questions = []
        if not isinstance(questions, list):
            questions = [str(questions)] if questions else []

        return dspy.Prediction(
            conversational_summary=getattr(result, "conversational_summary", "").strip(),
            key_highlights=highlights,
            suggested_questions=questions,
        )

    async def aforward(
        self,
        skill_content: str,
        skill_metadata: dict | str,
        validation_report: dict | str,
    ) -> dspy.Prediction:
        """Async version of forward - present skill for review.

        Args:
            skill_content: The skill content to present.
            skill_metadata: Metadata about the skill.
            validation_report: Validation report for the skill.

        Returns:
            Prediction with conversational_summary, key_highlights, and suggested_questions.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )
        report_str = (
            json.dumps(validation_report, indent=2)
            if isinstance(validation_report, dict)
            else validation_report
        )

        result = await self.present.acall(
            skill_content=skill_content,
            skill_metadata=metadata_str,
            validation_report=report_str,
        )

        highlights = safe_json_loads(
            getattr(result, "key_highlights", []), default=[], field_name="key_highlights"
        )
        if isinstance(highlights, dict):
            highlights = []
        if not isinstance(highlights, list):
            highlights = [str(highlights)] if highlights else []

        questions = safe_json_loads(
            getattr(result, "suggested_questions", []),
            default=[],
            field_name="suggested_questions",
        )
        if isinstance(questions, dict):
            questions = []
        if not isinstance(questions, list):
            questions = [str(questions)] if questions else []

        return dspy.Prediction(
            conversational_summary=getattr(result, "conversational_summary", "").strip(),
            key_highlights=highlights,
            suggested_questions=questions,
        )


class ProcessFeedbackModule(dspy.Module):
    """Module for processing user feedback using dspy.Predict."""

    def __init__(self):
        super().__init__()
        self.process = dspy.Predict(ProcessUserFeedback)

    def forward(
        self,
        user_feedback: str,
        current_skill_content: str,
        validation_errors: list[str] | str = "",
    ) -> dspy.Prediction:
        """Process user feedback on skill content.

        Args:
            user_feedback: The feedback provided by the user.
            current_skill_content: The current skill content being reviewed.
            validation_errors: Any validation errors to consider.

        Returns:
            Prediction with feedback_type, revision_plan, and requires_regeneration.
        """
        errors_str = (
            json.dumps(validation_errors, indent=2)
            if isinstance(validation_errors, list)
            else validation_errors
        )

        result = self.process(
            user_feedback=user_feedback,
            current_skill_content=current_skill_content,
            validation_errors=errors_str,
        )

        feedback_type = getattr(result, "feedback_type", "approve").strip().lower()

        return dspy.Prediction(
            feedback_type=feedback_type,
            revision_plan=getattr(result, "revision_plan", "").strip(),
            requires_regeneration=bool(getattr(result, "requires_regeneration", False)),
        )

    async def aforward(
        self,
        user_feedback: str,
        current_skill_content: str,
        validation_errors: list[str] | str = "",
    ) -> dspy.Prediction:
        """Async version of forward - process user feedback on skill content.

        Args:
            user_feedback: The feedback provided by the user.
            current_skill_content: The current skill content being reviewed.
            validation_errors: Any validation errors to consider.

        Returns:
            Prediction with feedback_type, revision_plan, and requires_regeneration.
        """
        errors_str = (
            json.dumps(validation_errors, indent=2)
            if isinstance(validation_errors, list)
            else validation_errors
        )

        result = await self.process.acall(
            user_feedback=user_feedback,
            current_skill_content=current_skill_content,
            validation_errors=errors_str,
        )

        feedback_type = getattr(result, "feedback_type", "approve").strip().lower()

        return dspy.Prediction(
            feedback_type=feedback_type,
            revision_plan=getattr(result, "revision_plan", "").strip(),
            requires_regeneration=bool(getattr(result, "requires_regeneration", False)),
        )
