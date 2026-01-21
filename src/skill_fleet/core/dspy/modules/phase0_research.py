"""Phase 0: Research and Example Gathering with ReAct.

Uses ReAct pattern for gathering examples and researching skill topics
before generation. This improves quality by grounding skills in concrete examples.
"""

from __future__ import annotations

import logging

import dspy

from ..signatures.base import GatherExamplesForSkill

logger = logging.getLogger(__name__)


class GatherExamplesModule(dspy.Module):
    """Gather concrete examples from user using ReAct pattern.

    This module uses ReAct to intelligently ask clarifying questions
    and extract examples from user responses. Continues until sufficient
    examples are collected or max questions reached.

    Tools available to ReAct:
    - extract_examples: Parse user response for usage examples
    - check_readiness: Assess if we have enough examples to proceed
    - generate_question: Create focused clarifying question

    Example:
        gatherer = GatherExamplesModule(min_examples=3, threshold=0.8)
        result = gatherer(
            task_description="Create async Python skill",
            user_responses="[]",
            collected_examples="[]",
        )
    """

    def __init__(
        self,
        min_examples: int = 3,
        readiness_threshold: float = 0.8,
        max_questions: int = 10,
    ) -> None:
        """Initialize example gatherer.

        Args:
            min_examples: Minimum examples before considering ready
            readiness_threshold: Readiness score threshold (0-1)
            max_questions: Maximum clarifying questions to ask
        """
        super().__init__()
        self.min_examples = min_examples
        self.readiness_threshold = readiness_threshold
        self.max_questions = max_questions

        # Use ChainOfThought for now (ReAct requires tool definitions)
        # In full implementation, this would use dspy.ReAct with actual tools
        self.gather = dspy.ChainOfThought(GatherExamplesForSkill)

    def forward(
        self,
        task_description: str,
        user_responses: str = "[]",
        collected_examples: str = "[]",
    ) -> dspy.Prediction:
        """Gather examples from user with intelligent questioning.

        Args:
            task_description: User's initial task description
            user_responses: JSON array of previous user responses
            collected_examples: JSON array of UserExample objects collected so far

        Returns:
            Prediction with: clarifying_questions, new_examples, refined_task,
            readiness_score, readiness_reasoning
        """
        import json

        # Parse collected examples to check count
        try:
            examples = json.loads(collected_examples)
            example_count = len(examples)
        except (json.JSONDecodeError, TypeError):
            example_count = 0

        # Build config
        config = json.dumps(
            {
                "min_examples": self.min_examples,
                "readiness_threshold": self.readiness_threshold,
                "max_questions": self.max_questions,
            }
        )

        # Execute gathering with enhanced signature
        result = self.gather(
            task_description=task_description,
            user_responses=user_responses,
            collected_examples=collected_examples,
            config=config,
        )

        # Log progress
        logger.info(
            f"Example gathering: {example_count} collected, readiness={result.readiness_score:.2f}"
        )

        return result
