"""
Quality assurance DSPy signatures.

These signatures handle Phase 3: Validation & Refinement.
Renamed from phase3_validation.py to use task-based naming.

Signatures:
- ValidateSkill: Validate against agentskills.io spec and quality standards
- AnalyzeValidationIssues: Categorize issues and plan fixes
- RefineSkillFromFeedback: Apply fixes addressing validation issues
- GenerateAutoFix: Generate automatic fix for single issue
- AssessSkillQuality: Assess content quality beyond structural validation
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.quality_assurance import (
    AnalyzeValidationIssues,
    AssessSkillQuality,
    GenerateAutoFix,
    RefineSkillFromFeedback,
    ValidateSkill,
)

__all__ = [
    # Signatures
    "ValidateSkill",
    "AnalyzeValidationIssues",
    "RefineSkillFromFeedback",
    "GenerateAutoFix",
    "AssessSkillQuality",
]
