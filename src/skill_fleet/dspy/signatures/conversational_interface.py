"""
Conversational interface DSPy signatures.

These signatures handle the conversational agent interface for natural language
skill creation interactions.

Signatures:
- InterpretUserIntent: Interpret user's skill creation intent
- DetectMultiSkillNeeds: Detect if multiple skills needed
- GenerateClarifyingQuestion: Generate single clarifying question
- AssessReadiness: Assess readiness to proceed
- DeepUnderstandingSignature: Deep understanding questions
- ConfirmUnderstandingBeforeCreation: Confirmation checkpoint
- UnderstandingSummary: Structured understanding summary
- PresentSkillForReview: Format skill for review
- ProcessUserFeedback: Process user feedback
- SuggestTestScenarios: Suggest TDD test scenarios
- VerifyTDDPassed: Verify TDD checklist complete
- EnhanceSkillContent: Add missing sections
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.chat import (
    AssessReadiness,
    ConfirmUnderstandingBeforeCreation,
    DeepUnderstandingSignature,
    DetectMultiSkillNeeds,
    EnhanceSkillContent,
    GenerateClarifyingQuestion,
    InterpretUserIntent,
    PresentSkillForReview,
    ProcessUserFeedback,
    SuggestTestScenarios,
    UnderstandingSummary,
    VerifyTDDPassed,
)

# Aliases for the old names
GenerateConversationalResponse = DeepUnderstandingSignature
ExtractUserIntent = InterpretUserIntent
GenerateFollowUp = GenerateClarifyingQuestion
SummarizeConversation = UnderstandingSummary

__all__ = [
    # Core conversational signatures
    "InterpretUserIntent",
    "DetectMultiSkillNeeds",
    "GenerateClarifyingQuestion",
    "AssessReadiness",
    "DeepUnderstandingSignature",
    "ConfirmUnderstandingBeforeCreation",
    "UnderstandingSummary",
    "PresentSkillForReview",
    "ProcessUserFeedback",
    # TDD signatures
    "SuggestTestScenarios",
    "VerifyTDDPassed",
    "EnhanceSkillContent",
    # Aliases for backward compatibility
    "GenerateConversationalResponse",
    "ExtractUserIntent",
    "GenerateFollowUp",
    "SummarizeConversation",
]
