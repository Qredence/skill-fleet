"""
HITL clarifying questions module.

Generates focused questions to resolve ambiguities and clarify
user requirements during HITL checkpoints.
"""

import time
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.hitl.questions import GenerateClarifyingQuestions


class GenerateClarifyingQuestionsModule(BaseModule):
    """
    Generate clarifying questions for ambiguous requirements.

    Uses GenerateClarifyingQuestions signature to create:
    - Focused questions targeting specific ambiguities
    - Multiple choice options where applicable
    - Priority levels (critical, important, optional)
    - Rationale for each question

    Example:
        module = GenerateClarifyingQuestionsModule()
        result = module.forward(
            task_description="Help me build something",
            ambiguities=["Unclear what technology stack"]
        )
        # Returns: {
        #   "questions": [
        #     {
        #       "text": "What technology stack do you prefer?",
        #       "question_type": "single",
        #       "options": [...],
        #       "rationale": "..."
        #     }
        #   ],
        #   "priority": "critical",
        #   "rationale": "..."
        # }

    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateClarifyingQuestions)

    def forward(  # type: ignore[override]
        self,
        task_description: str,
        ambiguities: list[str],
        initial_analysis: str = "",
        previous_answers: dict | None = None,
    ) -> dict[str, Any]:
        """
        Generate clarifying questions.

        Args:
            task_description: Original user task description
            ambiguities: List of detected ambiguities to clarify
            initial_analysis: Optional initial analysis context
            previous_answers: Optional previous Q&A for follow-up

        Returns:
            Dictionary with:
            - questions: List of structured questions
            - priority: Priority level (critical/important/optional)
            - rationale: Overall rationale for questions

        """
        start_time = time.time()

        # Sanitize inputs
        clean_task = self._sanitize_input(task_description)
        clean_ambiguities = ambiguities if ambiguities else []
        clean_analysis = self._sanitize_input(initial_analysis)
        clean_previous = str(previous_answers or {})

        # Execute signature
        result = self.generate(
            task_description=clean_task,
            ambiguities=clean_ambiguities,
            initial_analysis=clean_analysis,
            previous_answers=clean_previous,
        )

        # Transform to structured output
        questions = result.questions if isinstance(result.questions, list) else []

        # Normalize question structure
        normalized_questions = []
        for q in questions:
            if isinstance(q, dict):
                normalized_questions.append(
                    {
                        "text": q.get("text", ""),
                        "question_type": q.get("question_type", "text"),
                        "options": q.get("options", []),
                        "rationale": q.get("rationale", ""),
                        "allows_other": q.get("allows_other", False),
                    }
                )

        output = {
            "questions": normalized_questions,
            "priority": result.priority if hasattr(result, "priority") else "important",
            "rationale": result.rationale if hasattr(result, "rationale") else "",
        }

        # Validate
        required = ["questions", "priority"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("questions", [])
            output.setdefault("priority", "important")

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "task_description": clean_task[:100],
                "ambiguities_count": len(clean_ambiguities),
            },
            outputs={"questions_count": len(normalized_questions), "priority": output["priority"]},
            duration_ms=duration_ms,
        )

        return output
