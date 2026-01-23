"""
Task analysis and planning DSPy signatures.

These signatures handle Phase 1: Understanding & Planning.
Renamed from phase1_understanding.py to use task-based naming.

Signatures:
- GatherRequirements: Extract structured requirements from task description
- AnalyzeIntent: Analyze user intent for skill purpose and value
- FindTaxonomyPath: Find optimal taxonomy path placement
- AnalyzeDependencies: Identify prerequisites and related skills
- SynthesizePlan: Combine analyses into executable plan
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.task_analysis_planning import (
    AnalyzeDependencies,
    AnalyzeIntent,
    Domain,
    FindTaxonomyPath,
    GatherRequirements,
    SkillLength,
    SkillType,
    SynthesizePlan,
    TargetLevel,
)

__all__ = [
    # Type definitions
    "Domain",
    "TargetLevel",
    "SkillType",
    "SkillLength",
    # Signatures
    "GatherRequirements",
    "AnalyzeIntent",
    "FindTaxonomyPath",
    "AnalyzeDependencies",
    "SynthesizePlan",
]
