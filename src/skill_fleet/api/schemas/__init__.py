"""API schemas package.

Pydantic models for request/response validation are defined here,
following the codebase pattern (see core/models.py).

HITL models provide structured question/response types for the
API-first architecture where CLI is a thin client.
"""

from .hitl import QuestionOption, StructuredQuestion, normalize_questions
from .models import DeepUnderstandingState, JobState, TDDWorkflowState

__all__ = [
    # Job state models
    "TDDWorkflowState",
    "DeepUnderstandingState",
    "JobState",
    # HITL models
    "QuestionOption",
    "StructuredQuestion",
    "normalize_questions",
]
