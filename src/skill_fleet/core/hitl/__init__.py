"""Human-in-the-loop feedback handlers and DSPy modules."""

# Re-export DSPy HITL modules for unified access
from skill_fleet.core.dspy.modules.hitl import (
    ClarifyingQuestionsModule,
    ConfirmUnderstandingModule,
    FeedbackAnalyzerModule,
    HITLStrategyModule,
    PreviewGeneratorModule,
    ReadinessAssessorModule,
    RefinementPlannerModule,
    ValidationFormatterModule,
)

from .handlers import (
    AutoApprovalHandler,
    CLIFeedbackHandler,
    FeedbackHandler,
    InteractiveHITLHandler,
    WebhookFeedbackHandler,
    create_feedback_handler,
)

__all__ = [
    # Handlers
    "FeedbackHandler",
    "AutoApprovalHandler",
    "CLIFeedbackHandler",
    "InteractiveHITLHandler",
    "WebhookFeedbackHandler",
    "create_feedback_handler",
    # DSPy Modules (re-exported for unified access)
    "ClarifyingQuestionsModule",
    "ConfirmUnderstandingModule",
    "FeedbackAnalyzerModule",
    "HITLStrategyModule",
    "PreviewGeneratorModule",
    "ReadinessAssessorModule",
    "RefinementPlannerModule",
    "ValidationFormatterModule",
]
