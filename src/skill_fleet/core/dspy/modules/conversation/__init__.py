"""
DSPy conversational modules.

Split into smaller files for better maintainability.
"""

from .feedback import (
    PresentSkillModule,
    ProcessFeedbackModule,
)
from .intent import (
    DetectMultiSkillModule,
    InterpretIntentModule,
)
from .tdd import (
    SuggestTestsModule,
    VerifyTDDModule,
)
from .understanding import (
    AssessReadinessModule,
    ConfirmUnderstandingModule,
    DeepUnderstandingModule,
    GenerateQuestionModule,
    UnderstandingSummaryModule,
)

__all__ = [
    # Intent
    "InterpretIntentModule",
    "DetectMultiSkillModule",
    # Understanding
    "GenerateQuestionModule",
    "DeepUnderstandingModule",
    "UnderstandingSummaryModule",
    "ConfirmUnderstandingModule",
    "AssessReadinessModule",
    # TDD
    "SuggestTestsModule",
    "VerifyTDDModule",
    # Feedback
    "PresentSkillModule",
    "ProcessFeedbackModule",
]
