"""DSPy workflow for dynamic skill creation.

DEPRECATION NOTICE: This module is deprecated. Please import from:
- skill_fleet.core.models
- skill_fleet.core.creator
- skill_fleet.core.hitl
- skill_fleet.core.optimization

This package re-exports components for backward compatibility.
"""

from __future__ import annotations

# Backward compat: allow `from skill_fleet.workflow.models import X`
from skill_fleet.core import models

# Re-export from new locations for backward compatibility
from skill_fleet.core.creator import TaxonomySkillCreator
from skill_fleet.core.dspy.modules.base import (
    EditModule,
    EditModuleQA,
    GatherExamplesModule,
    InitializeModule,
    IterateModule,
    PackageModule,
    PackageModuleQA,
    PlanModule,
    PlanModuleQA,
    UnderstandModule,
    UnderstandModuleQA,
)
from skill_fleet.core.hitl import (
    AutoApprovalHandler,
    CLIFeedbackHandler,
    FeedbackHandler,
    InteractiveHITLHandler,
    WebhookFeedbackHandler,
    create_feedback_handler,
)
from skill_fleet.core.models import (
    Capability,
    ClarifyingQuestion,
    HITLRound,
    HITLSession,
    QuestionAnswer,
    QuestionOption,
)
from skill_fleet.core.optimization import (
    load_optimized_program,
    optimize_with_gepa,
    optimize_with_miprov2,
)
from skill_fleet.core.optimization.evaluation import load_trainset, skill_creation_metric

# Core workflow components
__all__ = [
    # Main orchestrator
    "TaxonomySkillCreator",
    # DSPy Modules (backward compat)
    "EditModule",
    "EditModuleQA",
    "GatherExamplesModule",
    "InitializeModule",
    "IterateModule",
    "PackageModule",
    "PackageModuleQA",
    "PlanModule",
    "PlanModuleQA",
    "UnderstandModule",
    "UnderstandModuleQA",
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
    # Other models
    "Capability",
    "models",
    # Optimization functions
    "optimize_with_miprov2",
    "optimize_with_gepa",
    "load_optimized_program",
    # Evaluation functions
    "skill_creation_metric",
    "load_trainset",
]
