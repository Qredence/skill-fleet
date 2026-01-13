"""DSPy signatures for skill creation workflow.

This module provides DSPy signature definitions for:
- Phase 1: Understanding (task analysis, taxonomy placement)
- Phase 2: Generation (content creation)
- Phase 3: Validation (quality checks)
- HITL: Human-in-the-loop interactions
- Chat: Conversational signatures
"""

# Import from base (legacy workflow signatures)
from skill_fleet.core.dspy.signatures.base import (
    EditSkillContent,
    GatherExamplesForSkill,
    GenerateDynamicFeedbackQuestions,
    InitializeSkillSkeleton,
    IterateSkillWithFeedback,
    PackageSkillForApproval,
    PlanSkillStructure,
    UnderstandTaskForSkill,
)

__all__ = [
    # Legacy signatures
    "GatherExamplesForSkill",
    "UnderstandTaskForSkill",
    "PlanSkillStructure",
    "InitializeSkillSkeleton",
    "EditSkillContent",
    "PackageSkillForApproval",
    "IterateSkillWithFeedback",
    "GenerateDynamicFeedbackQuestions",
]
