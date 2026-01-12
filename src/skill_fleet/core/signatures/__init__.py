"""DSPy signatures for the skills-fleet reworked architecture.

This module exports all signatures organized by phase:
- HITL: Human-in-the-Loop interaction signatures
- Phase 1: Understanding & Planning signatures
- Phase 2: Content Generation signatures
- Phase 3: Validation & Refinement signatures

Usage:
    from skill_fleet.core.signatures import (
        GenerateClarifyingQuestions,  # HITL
        AnalyzeIntent,                # Phase 1
        GenerateSkillContent,         # Phase 2
        ValidateSkill,                # Phase 3
    )
"""

from __future__ import annotations

# HITL Signatures
from .hitl import (
    AnalyzeFeedback,
    AssessReadiness,
    DetermineHITLStrategy,
    FormatValidationResults,
    GenerateClarifyingQuestions,
    GeneratePreview,
    GenerateRefinementPlan,
    SummarizeUnderstanding,
)

# Phase 1: Understanding & Planning
from .phase1_understanding import (
    AnalyzeDependencies,
    AnalyzeIntent,
    FindTaxonomyPath,
    GatherRequirements,
    SynthesizePlan,
)

# Phase 2: Content Generation
from .phase2_generation import (
    GenerateCapabilityImplementation,
    GenerateSkillContent,
    GenerateSkillSection,
    IncorporateFeedback,
)

# Phase 3: Validation & Refinement
from .phase3_validation import (
    AnalyzeValidationIssues,
    AssessSkillQuality,
    GenerateAutoFix,
    RefineSkillFromFeedback,
    ValidateSkill,
)

__all__ = [
    # HITL
    "GenerateClarifyingQuestions",
    "SummarizeUnderstanding",
    "GeneratePreview",
    "AnalyzeFeedback",
    "FormatValidationResults",
    "GenerateRefinementPlan",
    "AssessReadiness",
    "DetermineHITLStrategy",
    # Phase 1
    "GatherRequirements",
    "AnalyzeIntent",
    "FindTaxonomyPath",
    "AnalyzeDependencies",
    "SynthesizePlan",
    # Phase 2
    "GenerateSkillContent",
    "GenerateSkillSection",
    "IncorporateFeedback",
    "GenerateCapabilityImplementation",
    # Phase 3
    "ValidateSkill",
    "AnalyzeValidationIssues",
    "RefineSkillFromFeedback",
    "GenerateAutoFix",
    "AssessSkillQuality",
]
