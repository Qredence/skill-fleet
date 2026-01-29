"""Human-in-the-loop feedback handlers."""

from skill_fleet.core.modules.hitl.questions import GenerateClarifyingQuestionsModule

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
    "GenerateClarifyingQuestionsModule",
]
