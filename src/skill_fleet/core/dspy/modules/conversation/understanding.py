"""Deep understanding and clarification modules."""

from __future__ import annotations

import json
import logging

import dspy

from .....common.dspy_compat import coerce_reasoning_text
from .....common.utils import safe_float, safe_json_loads
from ....models import ClarifyingQuestion, QuestionOption
from ...utils.question_options import generate_smart_options
from ...signatures.chat import (
    AssessReadiness,
    ConfirmUnderstandingBeforeCreation,
    DeepUnderstandingSignature,
    GenerateClarifyingQuestion,
    UnderstandingSummary,
)

logger = logging.getLogger(__name__)


class GenerateQuestionModule(dspy.Module):
    """
    Module for generating contextual clarifying questions using MultiChainComparison.
    """

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateClarifyingQuestion)

    def forward(
        self,
        task_description: str,
        collected_examples: list[dict] | str = "",
        conversation_context: str = "",
        previous_questions: list[str] | None = None,
    ) -> dspy.Prediction:
        examples_str = (
            json.dumps(collected_examples, indent=2)
            if isinstance(collected_examples, list)
            else collected_examples
        )

        # Add previous questions context to avoid repetition
        enhanced_context = conversation_context
        if previous_questions:
            prev_q_str = "\nPreviously asked questions (DO NOT repeat):\n" + "\n".join(
                f"- {q}" for q in previous_questions
            )
            enhanced_context = (
                f"{conversation_context}\n{prev_q_str}" if conversation_context else prev_q_str
            )

        result = self.generate(
            task_description=task_description,
            collected_examples=examples_str,
            conversation_context=enhanced_context,
        )

        # Parse question_options
        options = safe_json_loads(
            getattr(result, "question_options", []), default=[], field_name="question_options"
        )
        if isinstance(options, dict):
            options = []
        if not isinstance(options, list):
            options = [str(options)] if options else []

        # If LLM didn't return options, generate smart fallback
        if not options:
            question_text = getattr(result, "question", "").strip()
            options, _ = generate_smart_options(question_text, task_description)

        return dspy.Prediction(
            question=getattr(result, "question", "").strip(),
            question_options=options,
            reasoning=coerce_reasoning_text(getattr(result, "reasoning", "")),
        )


class DeepUnderstandingModule(dspy.Module):
    """
    Module for deep understanding using MultiChainComparison.
    """

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.understand = dspy.ChainOfThought(DeepUnderstandingSignature)

    def forward(
        self,
        initial_task: str,
        conversation_history: list[dict] | str = "",
        research_findings: dict | str = "",
        current_understanding: str = "",
        previous_questions: list[dict] | None = None,
        questions_asked_count: int = 0,
    ) -> dspy.Prediction:
        history_str = (
            json.dumps(conversation_history, indent=2)
            if isinstance(conversation_history, list)
            else conversation_history
        )
        research_str = (
            json.dumps(research_findings, indent=2)
            if isinstance(research_findings, dict)
            else research_findings
        )

        # Add context about previous questions to avoid repetition
        enhanced_history = history_str
        if previous_questions:
            prev_q_context = "\nQuestions already asked (avoid repetition):\n"
            prev_q_context += "\n".join(f"- {q.get('question', q)}" for q in previous_questions)
            enhanced_history = f"{history_str}\n{prev_q_context}" if history_str else prev_q_context

        result = self.understand(
            initial_task=initial_task,
            conversation_history=enhanced_history or "[]",
            research_findings=research_str or "{}",
            current_understanding=current_understanding or "",
            questions_asked_count=questions_asked_count,
        )

        # Parse next_question
        next_question = None
        question_data = getattr(result, "next_question", None) or ""
        if question_data and isinstance(question_data, str) and question_data.strip():
            try:
                parsed = json.loads(question_data)
                # Handle case where JSON loads returns a string (string literal)
                if isinstance(parsed, str):
                    # Treat the string as the question text
                    next_question = ClarifyingQuestion(
                        id=f"q_{hash(parsed) & 0x7FFFFFFF}",
                        question=parsed,
                        context="",
                        options=[],
                        allows_multiple=True,
                        required=True,
                    )
                elif isinstance(parsed, dict):
                    next_question = ClarifyingQuestion(**parsed)
                else:
                    logger.warning(f"Unexpected JSON type for next_question: {type(parsed)}")
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to parse next_question JSON, attempting repair: {e}")
                next_question = self._repair_question_json(question_data)
        elif isinstance(question_data, dict):
            try:
                next_question = ClarifyingQuestion(**question_data)
            except Exception as e:
                logger.warning(f"Failed to parse next_question dict, attempting repair: {e}")
                next_question = self._repair_question_dict(question_data)
        elif isinstance(question_data, ClarifyingQuestion):
            next_question = question_data

        # If question parsed but has no options, generate smart options
        if next_question and not next_question.options:
            smart_options, refined_q = generate_smart_options(next_question.question, initial_task)
            if smart_options:
                next_question.options = [
                    QuestionOption(id=str(i), label=opt, description="")
                    for i, opt in enumerate(smart_options)
                ]

        # Parse research_needed
        research_needed = None
        research_data = getattr(result, "research_needed", None)
        if research_data:
            try:
                if isinstance(research_data, dict):
                    research_needed = research_data
                elif isinstance(research_data, str) and research_data.strip():
                    research_needed = json.loads(research_data)
            except Exception as e:
                logger.warning(f"Failed to parse research_needed: {e}")
                research_needed = None

        # Parse user_goals
        user_goals = []
        goals_data = getattr(result, "user_goals", None)
        if goals_data:
            try:
                if isinstance(goals_data, list):
                    user_goals = [str(g) for g in goals_data if g]
                elif isinstance(goals_data, str) and goals_data.strip():
                    parsed = json.loads(goals_data)
                    user_goals = [str(g) for g in parsed if g]
            except Exception as e:
                logger.warning(f"Failed to parse user_goals: {e}")
                user_goals = []

        return dspy.Prediction(
            next_question=next_question.model_dump() if next_question else None,
            reasoning=coerce_reasoning_text(getattr(result, "reasoning", "")),
            research_needed=research_needed,
            understanding_summary=getattr(result, "understanding_summary", "").strip(),
            readiness_score=safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            refined_task_description=getattr(
                result, "refined_task_description", initial_task
            ).strip(),
            user_problem=getattr(result, "user_problem", "").strip(),
            user_goals=user_goals,
        )

    def _repair_question_json(self, question_str: str) -> ClarifyingQuestion | None:
        """Attempt to repair malformed JSON for a question."""
        try:
            parsed = json.loads(question_str)
            # Handle string literal case
            if isinstance(parsed, str):
                return ClarifyingQuestion(
                    id=f"q_{hash(parsed) & 0x7FFFFFFF}",
                    question=parsed,
                    context="",
                    options=[],
                    allows_multiple=True,
                    required=True,
                )
            elif isinstance(parsed, dict):
                return self._repair_question_dict(parsed)
            else:
                logger.warning(f"Unexpected JSON type during repair: {type(parsed)}")
                return None
        except Exception as e:
            logger.warning(f"Failed to repair question JSON: {e}")
            return None

    def _repair_question_dict(self, question_dict: dict) -> ClarifyingQuestion | None:
        """Repair a partially malformed question dict."""
        try:
            # Ensure required fields exist
            if "id" not in question_dict:
                question_dict["id"] = f"q_{hash(str(question_dict)) & 0x7FFFFFFF}"
            if "question" not in question_dict:
                return None
            if "allows_multiple" not in question_dict:
                question_dict["allows_multiple"] = True
            if "required" not in question_dict:
                question_dict["required"] = True
            if "context" not in question_dict:
                question_dict["context"] = ""

            # Repair options field
            if "options" not in question_dict:
                question_dict["options"] = []
            else:
                question_dict["options"] = self._repair_options(question_dict["options"])

            return ClarifyingQuestion(**question_dict)
        except Exception as e:
            logger.warning(f"Failed to repair question dict: {e}")
            return None

    def _repair_options(self, options: list | dict) -> list[QuestionOption]:
        """Repair options field - convert strings to QuestionOption objects."""
        repaired_options = []

        if not isinstance(options, list):
            options = [options] if options else []

        for i, opt in enumerate(options):
            if isinstance(opt, str):
                # Convert string to QuestionOption
                label = opt.strip()
                # Extract short label from description
                if len(label) > 50:
                    short_label = label[:47] + "..."
                else:
                    colon_pos = label.find(":")
                    if colon_pos > 0 and colon_pos < 30:
                        short_label = label[:colon_pos].strip()
                    else:
                        short_label = label

                repaired_options.append(
                    QuestionOption(id=str(i), label=short_label, description=opt)
                )
            elif isinstance(opt, dict):
                # Repair dict option
                if "id" not in opt:
                    opt["id"] = str(i)
                if "label" not in opt:
                    opt["label"] = str(i)
                if "description" not in opt:
                    opt["description"] = ""
                repaired_options.append(QuestionOption(**opt))
            elif isinstance(opt, QuestionOption):
                repaired_options.append(opt)

        return repaired_options


class AssessReadinessModule(dspy.Module):
    """Module for assessing readiness using dspy.Predict."""

    def __init__(self):
        super().__init__()
        self.assess = dspy.Predict(AssessReadiness)

    def forward(
        self,
        task_description: str,
        examples: list[dict] | str = "",
        questions_asked: int = 0,
    ) -> dspy.Prediction:
        examples_str = json.dumps(examples, indent=2) if isinstance(examples, list) else examples

        result = self.assess(
            task_description=task_description,
            examples=examples_str,
            questions_asked=questions_asked,
        )

        return dspy.Prediction(
            readiness_score=safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            readiness_reasoning=getattr(result, "readiness_reasoning", "").strip(),
            should_proceed=bool(getattr(result, "should_proceed", False)),
        )


class ConfirmUnderstandingModule(dspy.Module):
    """
    Module for generating confirmation message before skill creation.
    """

    def __init__(self):
        super().__init__()
        self.confirm = dspy.Predict(ConfirmUnderstandingBeforeCreation)

    def forward(
        self,
        task_description: str,
        taxonomy_path: str,
        skill_metadata_draft: dict | str,
        collected_examples: list[dict] | str = "",
    ) -> dspy.Prediction:
        metadata_str = (
            json.dumps(skill_metadata_draft, indent=2)
            if isinstance(skill_metadata_draft, dict)
            else skill_metadata_draft
        )
        examples_str = (
            json.dumps(collected_examples, indent=2)
            if isinstance(collected_examples, list)
            else collected_examples
        )

        result = self.confirm(
            task_description=task_description,
            taxonomy_path=taxonomy_path,
            skill_metadata_draft=metadata_str,
            collected_examples=examples_str,
        )

        points = safe_json_loads(
            getattr(result, "key_points", []), default=[], field_name="key_points"
        )
        if isinstance(points, dict):
            points = []
        if not isinstance(points, list):
            points = [str(points)] if points else []

        return dspy.Prediction(
            confirmation_summary=getattr(result, "confirmation_summary", "").strip(),
            key_points=points,
            confirmation_question=getattr(result, "confirmation_question", "").strip(),
        )


class UnderstandingSummaryModule(dspy.Module):
    """
    Module for generating structured understanding summary before creation.
    """

    def __init__(self):
        super().__init__()
        self.summarize = dspy.ChainOfThought(UnderstandingSummary)

    def forward(
        self,
        task_description: str,
        taxonomy_path: str,
        skill_metadata_draft: dict | str,
        user_problem: str = "",
        user_goals: list[str] | None = None,
        research_context: dict | str = "",
        collected_examples: list[dict] | str = "",
    ) -> dspy.Prediction:
        metadata_str = (
            json.dumps(skill_metadata_draft, indent=2)
            if isinstance(skill_metadata_draft, dict)
            else skill_metadata_draft
        )
        research_str = (
            json.dumps(research_context, indent=2)
            if isinstance(research_context, dict)
            else research_context
        )
        examples_str = (
            json.dumps(collected_examples, indent=2)
            if isinstance(collected_examples, list)
            else collected_examples
        )
        goals_str = json.dumps(user_goals or [], indent=2)

        result = self.summarize(
            task_description=task_description,
            user_problem=user_problem,
            user_goals=goals_str,
            research_context=research_str,
            taxonomy_path=taxonomy_path,
            skill_metadata_draft=metadata_str,
            collected_examples=examples_str,
        )

        return dspy.Prediction(
            what_was_understood=getattr(result, "what_was_understood", "").strip(),
            what_will_be_created=getattr(result, "what_will_be_created", "").strip(),
            how_it_addresses_task=getattr(result, "how_it_addresses_task", "").strip(),
            alignment_summary=getattr(result, "alignment_summary", "").strip(),
        )
