"""DEPRECATED: Backward compatibility shim for workflow.models.

All models have been moved to skill_fleet.core.models.
This file re-exports for backward compatibility.
"""

from __future__ import annotations

# Re-export all models from the new location
from skill_fleet.core.models import (
    # Capability Models
    Capability,
    CapabilityImplementation,
    # HITL Models
    ClarifyingQuestion,
    DependencyAnalysis,
    DependencyRef,
    HITLRound,
    HITLSession,
    QuestionAnswer,
    QuestionOption,
    # Results
    SkillCreationResult,
    # Skill Metadata
    SkillMetadata,
    SkillSkeleton,
    # Task Analysis
    TaskIntent,
    ValidationReport,
)

__all__ = [
    # HITL Models
    "ClarifyingQuestion",
    "QuestionOption",
    "QuestionAnswer",
    "HITLRound",
    "HITLSession",
    # Capability Models
    "Capability",
    "CapabilityImplementation",
    # Skill Metadata
    "SkillMetadata",
    "SkillSkeleton",
    "ValidationReport",
    # Task Analysis
    "TaskIntent",
    "DependencyRef",
    "DependencyAnalysis",
    # Results
    "SkillCreationResult",
]
