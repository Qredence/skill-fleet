"""DSPy workflow for dynamic skill creation.

This package provides:
- TaxonomySkillCreator: Main orchestrator for skill creation
- Pydantic models for structured outputs (models.py)
- HITL models for human-in-the-loop feedback (models.py)
- Feedback handlers including InteractiveHITLHandler (feedback.py)
- Reward functions for quality assurance (rewards.py)
- Evaluation metrics and data loading (evaluation.py)
- MIPROv2/GEPA optimization (optimize.py)
"""

from __future__ import annotations

from .creator import TaxonomySkillCreator
from .evaluation import load_trainset, skill_creation_metric
from .feedback import (
    AutoApprovalHandler,
    CLIFeedbackHandler,
    FeedbackHandler,
    InteractiveHITLHandler,
    WebhookFeedbackHandler,
    create_feedback_handler,
)
from .models import (
    ClarifyingQuestion,
    HITLRound,
    HITLSession,
    QuestionAnswer,
    QuestionOption,
)
from .optimize import load_optimized_program, optimize_with_gepa, optimize_with_miprov2

# Core workflow components
__all__ = [
    # Main orchestrator
    "TaxonomySkillCreator",
    # Feedback handlers
    "FeedbackHandler",
    "AutoApprovalHandler",
    "CLIFeedbackHandler",
    "InteractiveHITLHandler",
    "WebhookFeedbackHandler",
    "create_feedback_handler",
    # HITL models
    "ClarifyingQuestion",
    "QuestionOption",
    "QuestionAnswer",
    "HITLRound",
    "HITLSession",
    # Optimization functions
    "optimize_with_miprov2",
    "optimize_with_gepa",
    "load_optimized_program",
    # Evaluation functions
    "skill_creation_metric",
    "load_trainset",
]
