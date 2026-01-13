"""DSPy conversational modules using MultiChainComparison and Predict.

These modules use dspy.MultiChainComparison for higher quality outputs and
dspy.Predict for simpler predictions. This replaces ChainOfThought with
more advanced DSPy patterns for better question generation and understanding.
"""

from __future__ import annotations

import json
import logging

import dspy

from ...agent.signatures import (
    AssessReadiness,
    ConfirmUnderstandingBeforeCreation,
    DeepUnderstandingSignature,
    DetectMultiSkillNeeds,
    GenerateClarifyingQuestion,
    InterpretUserIntent,
    PresentSkillForReview,
    ProcessUserFeedback,
    SuggestTestScenarios,
    VerifyTDDPassed,
)
from ...common.utils import safe_float, safe_json_loads
from ..models import ClarifyingQuestion

logger = logging.getLogger(__name__)


# =============================================================================
# MultiChainComparison Modules - Higher Quality through Multiple Candidates
# =============================================================================


class InterpretIntentModuleQA(dspy.Module):
    """Module for interpreting user intent using MultiChainComparison.

    Generates multiple interpretations and selects the best one for higher accuracy.
    Uses dspy.MultiChainComparison to improve confidence in intent detection.
    """

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison for quality assurance.

        Args:
            n_candidates: Number of candidate interpretations to generate (default: 3)
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.interpret = dspy.MultiChainComparison(
            InterpretUserIntent,
            n=n_candidates,
        )

    def forward(
        self,
        user_message: str,
        conversation_history: list[dict] | str = "",
        current_state: str = "EXPLORING",
    ) -> dict:
        """Interpret user's intent with multi-candidate quality assurance.

        Args:
            user_message: User's message
            conversation_history: Previous conversation context (list or JSON string)
            current_state: Current workflow state

        Returns:
            Dict with intent_type, extracted_task, and confidence
        """
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

        return {
            "intent_type": getattr(result, "intent_type", "unknown").strip().lower(),
            "extracted_task": getattr(result, "extracted_task", user_message).strip(),
            "confidence": safe_float(getattr(result, "confidence", 0.5), default=0.5),
        }


class DetectMultiSkillModuleQA(dspy.Module):
    """Module for detecting multi-skill needs using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison.

        Args:
            n_candidates: Number of candidates for skill breakdown analysis
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.detect = dspy.MultiChainComparison(
            DetectMultiSkillNeeds,
            n=n_candidates,
        )

    def forward(
        self,
        task_description: str,
        collected_examples: list[dict] | str = "",
        existing_skills: list[str] | str = "",
    ) -> dict:
        """Detect if task requires multiple skills with quality assurance.

        Args:
            task_description: User's complete task description
            collected_examples: Examples gathered (list or JSON string)
            existing_skills: Existing skills in taxonomy (list or JSON string)

        Returns:
            Dict with requires_multiple_skills, skill_breakdown, reasoning, and suggested_order
        """
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

        return {
            "requires_multiple_skills": bool(getattr(result, "requires_multiple_skills", False)),
            "skill_breakdown": breakdown,
            "reasoning": getattr(result, "reasoning", "").strip(),
            "suggested_order": order,
        }


class GenerateQuestionModuleQA(dspy.Module):
    """Module for generating contextual clarifying questions using MultiChainComparison.

    Uses multiple candidates to generate the most relevant question based on:
    - Task description
    - Examples gathered so far
    - Conversation context
    - Previous questions asked

    This ensures each question is contextual and not a fallback default.
    """

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison for contextual questions.

        Args:
            n_candidates: Number of candidate questions to generate
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.generate = dspy.MultiChainComparison(
            GenerateClarifyingQuestion,
            n=n_candidates,
        )

    def forward(
        self,
        task_description: str,
        collected_examples: list[dict] | str = "",
        conversation_context: str = "",
        previous_questions: list[str] | None = None,
    ) -> dict:
        """Generate a contextual clarifying question (NO fallback defaults).

        Each question is dynamically generated based on:
        - What we know so far (task_description, collected_examples)
        - What we've already discussed (conversation_context)
        - What questions we've already asked (previous_questions)

        Args:
            task_description: Current understanding of task
            collected_examples: Examples gathered (list or JSON string)
            conversation_context: What's already been discussed
            previous_questions: Questions already asked (to avoid repetition)

        Returns:
            Dict with question, question_options, and reasoning
        """
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

        return {
            "question": getattr(result, "question", "").strip(),
            "question_options": options,
            "reasoning": getattr(result, "reasoning", "").strip(),
        }


class DeepUnderstandingModuleQA(dspy.Module):
    """Module for deep understanding using MultiChainComparison.

    Generates contextual multi-choice questions that understand:
    - User's problem (WHY do they need this?)
    - User's goals (WHAT outcomes do they want?)
    - Context and constraints (WHAT limitations exist?)

    Uses research when needed to provide better context.
    """

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison for deep understanding.

        Args:
            n_candidates: Number of candidates for question generation
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.understand = dspy.MultiChainComparison(
            DeepUnderstandingSignature,
            n=n_candidates,
        )

    def forward(
        self,
        initial_task: str,
        conversation_history: list[dict] | str = "",
        research_findings: dict | str = "",
        current_understanding: str = "",
        previous_questions: list[dict] | None = None,
    ) -> dict:
        """Generate next contextual question based on deep understanding.

        Args:
            initial_task: User's original task description
            conversation_history: Previous questions and answers
            research_findings: Research results from web/filesystem
            current_understanding: Current understanding summary
            previous_questions: Questions already asked (to avoid repetition)

        Returns:
            Dict with next_question, reasoning, research_needed, understanding_summary,
            readiness_score, refined_task_description, user_problem, user_goals
        """
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
        )

        # Parse next_question (JSON string or empty string)
        next_question = None
        question_data = getattr(result, "next_question", None) or ""
        if question_data and isinstance(question_data, str) and question_data.strip():
            try:
                parsed = json.loads(question_data)
                next_question = ClarifyingQuestion(**parsed)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to parse next_question: {e}")
                next_question = None
        elif isinstance(question_data, dict):
            try:
                next_question = ClarifyingQuestion(**question_data)
            except Exception as e:
                logger.warning(f"Failed to parse next_question dict: {e}")
                next_question = None
        elif isinstance(question_data, ClarifyingQuestion):
            next_question = question_data

        # Parse research_needed (dict or None)
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

        # Parse user_goals (list[str])
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

        return {
            "next_question": next_question.model_dump() if next_question else None,
            "reasoning": getattr(result, "reasoning", "").strip(),
            "research_needed": research_needed,
            "understanding_summary": getattr(result, "understanding_summary", "").strip(),
            "readiness_score": safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            "refined_task_description": getattr(
                result, "refined_task_description", initial_task
            ).strip(),
            "user_problem": getattr(result, "user_problem", "").strip(),
            "user_goals": user_goals,
        }


class PresentSkillModuleQA(dspy.Module):
    """Module for presenting skill results using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison.

        Args:
            n_candidates: Number of candidates for presentation formatting
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.present = dspy.MultiChainComparison(
            PresentSkillForReview,
            n=n_candidates,
        )

    def forward(
        self,
        skill_content: str,
        skill_metadata: dict | str,
        validation_report: dict | str,
    ) -> dict:
        """Format skill results for conversational presentation with quality assurance.

        Args:
            skill_content: Generated SKILL.md content
            skill_metadata: Skill metadata (dict or JSON string)
            validation_report: Validation results (dict or JSON string)

        Returns:
            Dict with conversational_summary, key_highlights, and suggested_questions
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

        return {
            "conversational_summary": getattr(result, "conversational_summary", "").strip(),
            "key_highlights": highlights,
            "suggested_questions": questions,
        }


class SuggestTestsModuleQA(dspy.Module):
    """Module for suggesting test scenarios using MultiChainComparison.

    Generates pressure scenarios for TDD testing with multi-candidate quality assurance.
    Different skill types require different test approaches.
    """

    def __init__(self, n_candidates: int = 3):
        """Initialize with MultiChainComparison.

        Args:
            n_candidates: Number of candidates for test scenario generation
        """
        super().__init__()
        # MultiChainComparison requires a Signature class directly
        self.suggest = dspy.MultiChainComparison(
            SuggestTestScenarios,
            n=n_candidates,
        )

    def forward(
        self,
        skill_content: str,
        skill_type: str,
        skill_metadata: dict | str,
    ) -> dict:
        """Suggest test scenarios with quality assurance.

        Args:
            skill_content: Generated skill content (SKILL.md)
            skill_type: Type of skill (technique, pattern, reference, discipline)
            skill_metadata: Skill metadata (dict or JSON string)

        Returns:
            Dict with test_scenarios, baseline_predictions, and expected_rationalizations
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )

        result = self.suggest(
            skill_content=skill_content,
            skill_type=skill_type,
            skill_metadata=metadata_str,
        )

        scenarios = safe_json_loads(
            getattr(result, "test_scenarios", []), default=[], field_name="test_scenarios"
        )
        if isinstance(scenarios, dict):
            scenarios = []
        if not isinstance(scenarios, list):
            scenarios = [str(scenarios)] if scenarios else []

        predictions = safe_json_loads(
            getattr(result, "baseline_predictions", []),
            default=[],
            field_name="baseline_predictions",
        )
        if isinstance(predictions, dict):
            predictions = []
        if not isinstance(predictions, list):
            predictions = [str(predictions)] if predictions else []

        rationalizations = safe_json_loads(
            getattr(result, "expected_rationalizations", []),
            default=[],
            field_name="expected_rationalizations",
        )
        if isinstance(rationalizations, dict):
            rationalizations = []
        if not isinstance(rationalizations, list):
            rationalizations = [str(rationalizations)] if rationalizations else []

        return {
            "test_scenarios": scenarios,
            "baseline_predictions": predictions,
            "expected_rationalizations": rationalizations,
        }


# =============================================================================
# Simple Predict Modules - For Straightforward Predictions
# =============================================================================


class AssessReadinessModule(dspy.Module):
    """Module for assessing readiness using dspy.Predict.

    Simple prediction that doesn't require MultiChainComparison.
    """

    def __init__(self):
        super().__init__()
        self.assess = dspy.Predict(AssessReadiness)

    def forward(
        self,
        task_description: str,
        examples: list[dict] | str = "",
        questions_asked: int = 0,
    ) -> dict:
        """Assess if we have enough information to proceed.

        Args:
            task_description: Refined task description
            examples: Collected examples (list or JSON string)
            questions_asked: Number of questions already asked

        Returns:
            Dict with readiness_score, readiness_reasoning, and should_proceed
        """
        examples_str = json.dumps(examples, indent=2) if isinstance(examples, list) else examples

        result = self.assess(
            task_description=task_description,
            examples=examples_str,
            questions_asked=questions_asked,
        )

        return {
            "readiness_score": safe_float(getattr(result, "readiness_score", 0.0), default=0.0),
            "readiness_reasoning": getattr(result, "readiness_reasoning", "").strip(),
            "should_proceed": bool(getattr(result, "should_proceed", False)),
        }


class ConfirmUnderstandingModule(dspy.Module):
    """Module for generating confirmation message before skill creation.

    MANDATORY checkpoint before writing any skill directory structure or content.
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
    ) -> dict:
        """Generate confirmation summary before creation.

        Args:
            task_description: Refined task description
            taxonomy_path: Proposed taxonomy path
            skill_metadata_draft: Draft skill metadata (dict or JSON string)
            collected_examples: Examples collected (list or JSON string)

        Returns:
            Dict with confirmation_summary, key_points, and confirmation_question
        """
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

        return {
            "confirmation_summary": getattr(result, "confirmation_summary", "").strip(),
            "key_points": points,
            "confirmation_question": getattr(result, "confirmation_question", "").strip(),
        }


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
    ) -> dict:
        """Process user feedback and determine revision plan.

        Args:
            user_feedback: User's feedback message
            current_skill_content: Current skill content
            validation_errors: Validation errors (list or JSON string)

        Returns:
            Dict with feedback_type, revision_plan, and requires_regeneration
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

        return {
            "feedback_type": feedback_type,
            "revision_plan": getattr(result, "revision_plan", "").strip(),
            "requires_regeneration": bool(getattr(result, "requires_regeneration", False)),
        }


class VerifyTDDModule(dspy.Module):
    """Module for verifying TDD checklist completion using dspy.Predict."""

    def __init__(self):
        super().__init__()
        self.verify = dspy.Predict(VerifyTDDPassed)

    def forward(
        self,
        skill_content: str,
        checklist_state: dict | str,
    ) -> dict:
        """Verify TDD checklist is complete.

        Args:
            skill_content: Generated skill content (SKILL.md)
            checklist_state: Checklist completion state (dict or JSON string)

        Returns:
            Dict with all_passed, missing_items, and ready_to_save
        """
        checklist_str = (
            json.dumps(checklist_state, indent=2)
            if isinstance(checklist_state, dict)
            else checklist_state
        )

        result = self.verify(
            skill_content=skill_content,
            checklist_state=checklist_str,
        )

        missing = safe_json_loads(
            getattr(result, "missing_items", []), default=[], field_name="missing_items"
        )
        if isinstance(missing, dict):
            missing = []
        if not isinstance(missing, list):
            missing = [str(missing)] if missing else []

        return {
            "all_passed": bool(getattr(result, "all_passed", False)),
            "missing_items": missing,
            "ready_to_save": bool(getattr(result, "ready_to_save", False)),
        }
