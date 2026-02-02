"""
Base signatures for skill-fleet with modern DSPy 3.1.2+ support.

Provides signature base classes with typed fields, Reasoning support,
and utility methods for skill creation workflows.
"""

from __future__ import annotations

from typing import get_type_hints

import dspy


class TypedSignature(dspy.Signature):
    """
    Base signature with type hints and Reasoning support.

    Extends DSPy Signature with:
    - Type hint introspection
    - Reasoning field detection
    - Field metadata access

    Example:
        class MySignature(TypedSignature):
            query: str = dspy.InputField()
            answer: str = dspy.OutputField()
            reasoning: dspy.Reasoning = dspy.OutputField()

        # Check if signature uses reasoning
        if MySignature.has_reasoning_field():
            print("Uses reasoning")

    """

    @classmethod
    def get_output_fields(cls) -> dict[str, type]:
        """
        Get output fields with their types.

        Returns:
            Dictionary mapping field names to their types

        """
        hints = get_type_hints(cls)
        return {
            name: hint
            for name, hint in hints.items()
            if not name.startswith("_") and not callable(getattr(cls, name, None))
        }

    @classmethod
    def has_reasoning_field(cls) -> bool:
        """
        Check if signature has a Reasoning output field.

        Returns:
            True if any output field is of type Reasoning

        """
        hints = get_type_hints(cls)
        return any(getattr(hint, "__name__", None) == "Reasoning" for hint in hints.values())

    @classmethod
    def get_field_description(cls, field_name: str) -> str | None:
        """
        Get description for a field.

        Args:
            field_name: Name of the field

        Returns:
            Field description or None

        """
        field = getattr(cls, field_name, None)
        if field and hasattr(field, "desc"):
            return field.desc
        return None


# Common signatures for skill-fleet workflows


class AnalyzeSkillRequirements(TypedSignature):
    """Analyze user requirements for skill creation."""

    task_description: str = dspy.InputField(
        desc="User's natural language description of the skill they want to create"
    )
    context: str | None = dspy.InputField(
        desc="Additional context or constraints",
        default=None,
    )

    requirements: list[str] = dspy.OutputField(desc="List of extracted functional requirements")
    domain: str = dspy.OutputField(
        desc="Detected domain or topic area (e.g., 'data_processing', 'api_integration')"
    )
    complexity: str = dspy.OutputField(
        desc="Estimated complexity level: simple, medium, or complex"
    )
    reasoning: dspy.Reasoning = dspy.OutputField(
        desc="Step-by-step analysis of how requirements were extracted"
    )


class GenerateSkillContent(TypedSignature):
    """Generate skill content based on analyzed requirements."""

    requirements: list[str] = dspy.InputField(desc="List of functional requirements")
    domain: str = dspy.InputField(desc="Domain or topic area")
    complexity: str = dspy.InputField(desc="Complexity level")
    template: str | None = dspy.InputField(
        desc="Optional template to follow",
        default=None,
    )

    content: str = dspy.OutputField(desc="Complete SKILL.md content in valid markdown format")
    metadata: dict = dspy.OutputField(desc="Skill metadata including name, description, tags")
    reasoning: dspy.Reasoning = dspy.OutputField(
        desc="Reasoning about content generation decisions"
    )


class ValidateSkillStructure(TypedSignature):
    """Validate skill structure against agentskills.io standards."""

    content: str = dspy.InputField(desc="SKILL.md content to validate")

    is_valid: bool = dspy.OutputField(desc="Whether the structure is valid")
    errors: list[str] = dspy.OutputField(desc="List of structural errors found")
    warnings: list[str] = dspy.OutputField(desc="List of warnings")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Validation reasoning")


class RefineSkillContent(TypedSignature):
    """Refine skill content based on feedback."""

    content: str = dspy.InputField(desc="Current SKILL.md content")
    feedback: str = dspy.InputField(desc="Feedback or issues to address")
    improvement_areas: list[str] = dspy.InputField(desc="Specific areas needing improvement")

    refined_content: str = dspy.OutputField(desc="Improved SKILL.md content")
    changes_made: list[str] = dspy.OutputField(desc="Summary of changes")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning for changes")


class ChatResponse(TypedSignature):
    """Generate conversational response with reasoning."""

    message: str = dspy.InputField(desc="User message")
    context: str = dspy.InputField(
        desc="Conversation context and history",
        default="",
    )

    response: str = dspy.OutputField(desc="Assistant response")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for the response")
    suggested_actions: list[str] = dspy.OutputField(
        desc="Suggested next actions for the user",
        default=[],
    )
