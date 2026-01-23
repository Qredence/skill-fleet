"""
Skills Fleet Workflows Layer.

This package provides orchestration layers that glue DSPy components together
into cohesive workflows. Both the FastAPI app and CLI interface use these
orchestrators, ensuring a single source of truth for all skill-related operations.

**Workflow Architecture:**
- Conversational Interface: Multi-turn conversation workflow
- Task Analysis & Planning: Phase 1 - Understanding & Planning
- Content Generation: Phase 2 - Skill content creation
- Quality Assurance: Phase 3 - Validation & refinement
- Human-in-the-Loop: HITL checkpoint management
- Signature Optimization: Signature tuning workflow

**Design Principles:**
1. Orchestrators are workflow engines that coordinate DSPy modules
2. Both API and CLI call the same orchestrators via app/services/
3. Each orchestrator is responsible for a cohesive business workflow
4. Orchestrators expose clean interfaces with well-defined inputs/outputs
"""

# Task Analysis & Planning
# Content Generation
from .content_generation import ContentGenerationOrchestrator

# Conversational Interface
from .conversational_interface import (
    ConversationalOrchestrator,
    ConversationContext,
    ConversationMessage,
    ConversationState,
    IntentType,
)

# Human-in-the-Loop
from .human_in_the_loop import Checkpoint, CheckpointPhase, HITLCheckpointManager

# Quality Assurance
from .quality_assurance import QualityAssuranceOrchestrator

# Signature Optimization
from .signature_optimization import SignatureTuningOrchestrator
from .task_analysis_planning import TaskAnalysisOrchestrator

__all__ = [
    # Task Analysis & Planning
    "TaskAnalysisOrchestrator",
    # Content Generation
    "ContentGenerationOrchestrator",
    # Quality Assurance
    "QualityAssuranceOrchestrator",
    # Human-in-the-Loop
    "HITLCheckpointManager",
    "Checkpoint",
    "CheckpointPhase",
    # Conversational Interface
    "ConversationalOrchestrator",
    "ConversationContext",
    "ConversationMessage",
    "ConversationState",
    "IntentType",
    # Signature Optimization
    "SignatureTuningOrchestrator",
]
