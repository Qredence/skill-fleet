"""
Human-in-the-loop (HITL) DSPy signatures.

These signatures handle HITL checkpoints throughout the skill creation workflow.
Renamed from hitl.py with clarified task-based naming.

Signatures:
- GenerateClarifyingQuestions: Generate focused clarifying questions
- GenerateHITLQuestions: Generate HITL clarification from requirements
- SummarizeUnderstanding: Summarize understanding for confirmation
- GeneratePreview: Generate preview for user review
- AnalyzeFeedback: Analyze feedback and determine changes
- FormatValidationResults: Format validation results for display
- GenerateRefinementPlan: Generate refinement plan
- AssessReadiness: Assess readiness to proceed
- DetermineHITLStrategy: Determine optimal HITL strategy
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.core.dspy.signatures.human_in_the_loop import (
    AnalyzeFeedback,
    AssessReadiness,
    DetermineHITLStrategy,
    FormatValidationResults,
    GenerateClarifyingQuestions,
    GenerateHITLQuestions,
    GeneratePreview,
    GenerateRefinementPlan,
    SummarizeUnderstanding,
)

__all__ = [
    # Phase 1 HITL
    "GenerateClarifyingQuestions",
    "GenerateHITLQuestions",
    "SummarizeUnderstanding",
    # Phase 2 HITL
    "GeneratePreview",
    "AnalyzeFeedback",
    # Phase 3 HITL
    "FormatValidationResults",
    "GenerateRefinementPlan",
    # Universal HITL
    "AssessReadiness",
    "DetermineHITLStrategy",
]
