"""
Workflow Orchestrators.

This module provides high-level orchestration interfaces for the skill creation workflow.
All orchestrators delegate to underlying DSPy modules and provide clean interfaces
for both API and CLI use.

Orchestrators:
- TaskAnalysisOrchestrator: Phase 1 - Understanding and Planning
- ContentGenerationOrchestrator: Phase 2 - Content Generation
- QualityAssuranceOrchestrator: Phase 3 - Validation and Refinement
- ConversationalOrchestrator: Multi-turn conversational interface
- HITLCheckpointManager: Human-in-the-Loop checkpoint management
- SignatureTuningOrchestrator: Signature tuning and optimization
"""

from .content_generation import ContentGenerationOrchestrator
from .conversational import (
    ConversationalOrchestrator,
    ConversationContext,
    ConversationMessage,
    ConversationState,
    IntentType,
)
from .hitl_checkpoint import Checkpoint, CheckpointPhase, HITLCheckpointManager
from .quality_assurance import QualityAssuranceOrchestrator
from .signature_tuning import SignatureTuningOrchestrator
from .task_analysis import TaskAnalysisOrchestrator

__all__ = [
    "TaskAnalysisOrchestrator",
    "ContentGenerationOrchestrator",
    "QualityAssuranceOrchestrator",
    "ConversationalOrchestrator",
    "HITLCheckpointManager",
    "SignatureTuningOrchestrator",
    # Conversational exports
    "ConversationState",
    "IntentType",
    "ConversationMessage",
    "ConversationContext",
    # HITL exports
    "Checkpoint",
    "CheckpointPhase",
]
