"""
Content generation DSPy signatures.

These signatures handle Phase 2: Content Generation.
Renamed from phase2_generation.py to use task-based naming.

Signatures:
- GenerateSkillContent: Generate production-ready SKILL.md
- GenerateSkillSection: Generate individual section (chunked generation)
- IncorporateFeedback: Refine content based on user feedback
- GenerateCapabilityImplementation: Generate capability implementation guide
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.phase2_generation import (
    GenerateCapabilityImplementation,
    GenerateSkillContent,
    GenerateSkillSection,
    IncorporateFeedback,
    SkillStyle,
    TargetLevel,
)

__all__ = [
    # Type definitions
    "SkillStyle",
    "TargetLevel",
    # Signatures
    "GenerateSkillContent",
    "GenerateSkillSection",
    "IncorporateFeedback",
    "GenerateCapabilityImplementation",
]
