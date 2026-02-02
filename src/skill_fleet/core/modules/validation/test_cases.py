"""
Generate test cases for skill validation.

This module generates comprehensive test cases for validating skill triggering
and functionality. Creates positive tests (should trigger), negative tests
(shouldn't trigger), and edge cases for manual review.
"""

from __future__ import annotations

from typing import Any

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled
from skill_fleet.core.modules.base import BaseModule


class GenerateTestCases(dspy.Signature):
    """
    Generate comprehensive test cases for skill validation.

    Create diverse test cases that cover obvious triggers, paraphrased requests,
    and negative cases to ensure the skill triggers appropriately and doesn't
    trigger on unrelated queries.
    """

    # Inputs
    skill_description: str = dspy.InputField(
        desc="Full skill description including what it does and when to use it"
    )
    trigger_phrases: list[str] = dspy.InputField(
        desc="Specific phrases that should trigger the skill"
    )
    negative_triggers: list[str] = dspy.InputField(desc="Contexts where skill should NOT trigger")
    skill_category: str = dspy.InputField(
        desc="Category: document_creation, workflow_automation, mcp_enhancement, analysis, other"
    )

    # Outputs
    positive_tests: list[str] = dspy.OutputField(
        desc="10 diverse queries that SHOULD trigger the skill. Include: "
        "3 exact trigger phrases, 3 paraphrased variations, 2 context-rich queries, "
        "2 ambiguous but relevant queries."
    )

    negative_tests: list[str] = dspy.OutputField(
        desc="10 queries that should NOT trigger the skill. Include: "
        "3 completely unrelated topics, 3 similar but different intents, "
        "2 partial matches, 2 edge cases that might confuse."
    )

    edge_cases: list[str] = dspy.OutputField(
        desc="5 genuinely ambiguous edge cases for manual review. "
        "These are queries where it's unclear whether the skill should trigger."
    )

    functional_tests: list[dict] = dspy.OutputField(
        desc="5 functional test scenarios. Each dict has: 'scenario' (str), "
        "'input' (str), 'expected_behavior' (str), 'success_criteria' (list[str])."
    )


class GenerateTestCasesModule(BaseModule):
    """
    Generate test cases for skill triggering validation.

    Creates positive tests (should trigger), negative tests (shouldn't trigger),
    edge cases for manual review, and functional test scenarios.

    Example:
        module = GenerateTestCasesModule()
        result = module(
            skill_description="Creates React components. Use when user asks to 'build a component'...",
            trigger_phrases=["create React component", "build UI", "generate component"],
            negative_triggers=["simple queries", "general questions"],
            skill_category="document_creation"
        )
        # result["positive_tests"] == ["Create a React button component", ...]
        # result["negative_tests"] == ["What's the weather today?", ...]
        # result["total_tests"] == 25

    """

    def __init__(self) -> None:
        super().__init__()
        self.generator = dspy.ChainOfThought(GenerateTestCases)

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """
        Generate comprehensive test cases for skill validation.

        Args:
            skill_description: Full skill description
            trigger_phrases: Specific phrases that should trigger the skill
            negative_triggers: Contexts where skill should NOT trigger
            skill_category: Skill category for context
            **kwargs: Additional keyword arguments for compatibility.

        Returns:
            Dictionary containing:
            - positive_tests: 10 queries that should trigger
            - negative_tests: 10 queries that should not trigger
            - edge_cases: 5 ambiguous cases for manual review
            - functional_tests: 5 functional test scenarios
            - total_tests: Total count of all tests

        """
        start_time = self._get_time()

        skill_description = kwargs.get("skill_description")
        if skill_description is None:
            raise ValueError("skill_description must be provided")

        trigger_phrases = kwargs.get("trigger_phrases", [])
        negative_triggers = kwargs.get("negative_triggers", [])
        skill_category = kwargs.get("skill_category", "other")

        if not isinstance(trigger_phrases, list):
            trigger_phrases = []
        if not isinstance(negative_triggers, list):
            negative_triggers = []
        if not isinstance(skill_category, str):
            skill_category = "other"

        # Sanitize inputs
        clean_description = self._sanitize_input(str(skill_description), max_length=2000)
        clean_trigger_phrases = [self._sanitize_input(str(p)) for p in trigger_phrases[:10]]
        clean_negative_triggers = [self._sanitize_input(str(t)) for t in negative_triggers[:5]]

        try:
            result = self.generator(
                skill_description=clean_description,
                trigger_phrases=clean_trigger_phrases,
                negative_triggers=clean_negative_triggers,
                skill_category=skill_category,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.error(f"Test case generation failed: {e}")
            # Return minimal fallback result
            fallback = self._create_fallback_result(trigger_phrases, negative_triggers)
            return self._to_prediction(**fallback)

        # Calculate total tests
        total_tests = (
            len(result.positive_tests or [])
            + len(result.negative_tests or [])
            + len(result.edge_cases or [])
        )

        trigger_coverage = self._assess_trigger_coverage(
            result.positive_tests or [], clean_trigger_phrases
        )

        output = {
            "positive_tests": result.positive_tests or [],
            "negative_tests": result.negative_tests or [],
            "edge_cases": result.edge_cases or [],
            "functional_tests": result.functional_tests or [],
            "total_tests": total_tests,
            "trigger_coverage": trigger_coverage,
        }

        # Log execution
        duration_ms = (self._get_time() - start_time) * 1000
        self._log_execution(
            inputs={
                "skill_category": skill_category,
                "trigger_count": len(trigger_phrases),
            },
            outputs={"total_tests": total_tests},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _assess_trigger_coverage(
        self, positive_tests: list[str], trigger_phrases: list[str]
    ) -> float:
        """Assess how many trigger phrases appear in at least one positive test."""
        if not trigger_phrases:
            return 0.0

        covered = 0
        for phrase in trigger_phrases:
            phrase_lower = (phrase or "").lower()
            for test in positive_tests:
                if phrase_lower and phrase_lower in (test or "").lower():
                    covered += 1
                    break

        return covered / len(trigger_phrases)

    def _create_fallback_result(
        self,
        trigger_phrases: list[str],
        negative_triggers: list[str],
    ) -> dict[str, Any]:
        """Create minimal fallback result when generation fails."""
        # Generate basic positive tests from trigger phrases
        positive_tests = trigger_phrases[:10] if trigger_phrases else ["Example trigger query"]

        # Generate basic negative tests
        negative_tests = [
            "What's the weather today?",
            "Help me with something completely different",
            "Tell me a joke",
            "What is the capital of France?",
            "Simple question",
        ]
        if negative_triggers:
            negative_tests.extend(negative_triggers[:5])

        # Provide a few deterministic functional tests so callers can rely on this field.
        functional_tests = [
            {
                "scenario": "Basic trigger query",
                "input": positive_tests[0] if positive_tests else "Example trigger query",
                "expected_behavior": "Skill should trigger and follow its instructions.",
                "success_criteria": ["Skill triggers", "Output follows skill format"],
            },
            {
                "scenario": "Non-trigger query",
                "input": negative_tests[0] if negative_tests else "Unrelated query",
                "expected_behavior": "Skill should not trigger.",
                "success_criteria": ["Skill does not trigger"],
            },
        ]

        trigger_coverage = self._assess_trigger_coverage(positive_tests, trigger_phrases)

        return {
            "positive_tests": positive_tests,
            "negative_tests": negative_tests[:10],
            "edge_cases": ["Fallback edge case - generation failed"],
            "functional_tests": functional_tests,
            "total_tests": len(positive_tests) + len(negative_tests[:10]) + 1,
            "trigger_coverage": trigger_coverage,
            "fallback": True,
        }

    def _get_time(self) -> float:
        """Get current time for duration tracking."""
        import time

        return time.time()
