"""
DSPy signatures for skill creation workflows.

This package contains signature definitions organized by workflow phase:
- understanding/: Signatures for requirements, intent, taxonomy, dependencies
- generation/: Signatures for content generation
- validation/: Signatures for compliance and quality assessment
- hitl/: Signatures for human-in-the-loop questions

Modern DSPy 3.1.2+ signatures with Reasoning support:
- TypedSignature: Base class with type hints
- ChatResponse: Conversational signature with reasoning
"""

from __future__ import annotations

from skill_fleet.core.signatures.base import (
    AnalyzeSkillRequirements,
    ChatResponse,
    GenerateSkillContent,
    RefineSkillContent,
    TypedSignature,
    ValidateSkillStructure,
)

__all__ = [
    "TypedSignature",
    "AnalyzeSkillRequirements",
    "GenerateSkillContent",
    "ValidateSkillStructure",
    "RefineSkillContent",
    "ChatResponse",
]
