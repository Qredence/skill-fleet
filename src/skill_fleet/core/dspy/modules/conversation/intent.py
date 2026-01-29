"""Intent understanding and multi-skill detection modules."""

from __future__ import annotations

import json
import logging

import dspy

from .....common.dspy_compat import coerce_reasoning_text
from .....common.utils import safe_float, safe_json_loads
from ...signatures.chat import (
    DetectMultiSkillNeeds,
    InterpretUserIntent,
)

logger = logging.getLogger(__name__)


class InterpretIntentModule(dspy.Module):
    """Module for interpreting user intent using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.interpret = dspy.ChainOfThought(InterpretUserIntent)

    def forward(
        self,
        user_message: str,
        conversation_history: list[dict] | str = "",
        current_state: str = "EXPLORING",
    ) -> dspy.Prediction:
        history_str = (
            json.dumps(conversation_history, indent=2)
            if isinstance(conversation_history, list)
            else conversation_history
        )

        result = self.interpret(
            user_message=user_message,
            conversation_history=history_str,
            current_state=current_state,
        )

        return dspy.Prediction(
            intent_type=getattr(result, "intent_type", "unknown").strip().lower(),
            extracted_task=getattr(result, "extracted_task", user_message).strip(),
            confidence=safe_float(getattr(result, "confidence", 0.5), default=0.5),
        )


class DetectMultiSkillModule(dspy.Module):
    """Module for detecting multi-skill needs using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.detect = dspy.ChainOfThought(DetectMultiSkillNeeds)

    def forward(
        self,
        task_description: str,
        collected_examples: list[dict] | str = "",
        existing_skills: list[str] | str = "",
    ) -> dspy.Prediction:
        examples_str = (
            json.dumps(collected_examples, indent=2)
            if isinstance(collected_examples, list)
            else collected_examples
        )
        skills_str = (
            json.dumps(existing_skills, indent=2)
            if isinstance(existing_skills, list)
            else existing_skills
        )

        result = self.detect(
            task_description=task_description,
            collected_examples=examples_str,
            existing_skills=skills_str,
        )

        breakdown = safe_json_loads(
            getattr(result, "skill_breakdown", []), default=[], field_name="skill_breakdown"
        )
        if isinstance(breakdown, dict):
            breakdown = []
        if not isinstance(breakdown, list):
            breakdown = [str(breakdown)] if breakdown else []

        order = safe_json_loads(
            getattr(result, "suggested_order", []), default=[], field_name="suggested_order"
        )
        if isinstance(order, dict):
            order = []
        if not isinstance(order, list):
            order = [str(order)] if order else []

        alternatives = safe_json_loads(
            getattr(result, "alternative_approaches", []),
            default=[],
            field_name="alternative_approaches",
        )
        if isinstance(alternatives, dict):
            alternatives = []
        if not isinstance(alternatives, list):
            alternatives = [str(alternatives)] if alternatives else []

        return dspy.Prediction(
            requires_multiple_skills=bool(getattr(result, "requires_multiple_skills", False)),
            skill_breakdown=breakdown,
            reasoning=coerce_reasoning_text(getattr(result, "reasoning", "")),
            suggested_order=order,
            alternative_approaches=alternatives,
        )
