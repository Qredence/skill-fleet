"""
DSPy signature definitions organized by task.

This package contains DSPy signatures grouped by their functional purpose:
- conversational_interface.py: Chat and conversation signatures
- human_in_the_loop.py: HITL checkpoint and feedback signatures
- task_analysis.py: Task understanding and planning signatures
- content_generation.py: Skill content creation signatures
- quality_assurance.py: Validation and quality check signatures
- signature_optimization.py: Signature tuning signatures

Migration Note:
    Old phase-based names are deprecated:
    - phase1_understanding.py → task_analysis.py
    - phase2_generation.py → content_generation.py
    - phase3_validation.py → quality_assurance.py
"""

from __future__ import annotations

# Content Generation Signatures (Phase 2: Generation)
from skill_fleet.dspy.signatures.content_generation import (
    GenerateCapabilityImplementation,
    GenerateSkillContent,
    GenerateSkillSection,
    IncorporateFeedback,
    SkillStyle,
)

# Conversational Interface Signatures
from skill_fleet.dspy.signatures.conversational_interface import (
    AssessReadiness as ConversationalAssessReadiness,
)
from skill_fleet.dspy.signatures.conversational_interface import (
    ConfirmUnderstandingBeforeCreation,
    DeepUnderstandingSignature,
    DetectMultiSkillNeeds,
    EnhanceSkillContent,
    ExtractUserIntent,
    GenerateClarifyingQuestion,
    GenerateConversationalResponse,
    GenerateFollowUp,
    InterpretUserIntent,
    PresentSkillForReview,
    ProcessUserFeedback,
    SuggestTestScenarios,
    SummarizeConversation,
    UnderstandingSummary,
    VerifyTDDPassed,
)

# Human-in-the-Loop Signatures
from skill_fleet.dspy.signatures.human_in_the_loop import (
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

# Quality Assurance Signatures (Phase 3: Validation)
from skill_fleet.dspy.signatures.quality_assurance import (
    AnalyzeValidationIssues,
    AssessSkillQuality,
    GenerateAutoFix,
    RefineSkillFromFeedback,
    ValidateSkill,
)

# Signature Optimization Signatures
from skill_fleet.dspy.signatures.signature_optimization import (
    AnalyzeSignatureFailures,
    CompareSignatureVersions,
    ProposeSignatureImprovement,
    ValidateSignatureImprovement,
)

# Task Analysis Signatures (Phase 1: Understanding & Planning)
from skill_fleet.dspy.signatures.task_analysis import (
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
    # Task Analysis (Phase 1)
    "Domain",
    "TargetLevel",
    "SkillType",
    "SkillLength",
    "GatherRequirements",
    "AnalyzeIntent",
    "FindTaxonomyPath",
    "AnalyzeDependencies",
    "SynthesizePlan",
    # Content Generation (Phase 2)
    "SkillStyle",
    "GenerateSkillContent",
    "GenerateSkillSection",
    "IncorporateFeedback",
    "GenerateCapabilityImplementation",
    # Quality Assurance (Phase 3)
    "ValidateSkill",
    "AnalyzeValidationIssues",
    "RefineSkillFromFeedback",
    "GenerateAutoFix",
    "AssessSkillQuality",
    # Human-in-the-Loop
    "GenerateClarifyingQuestions",
    "GenerateHITLQuestions",
    "SummarizeUnderstanding",
    "GeneratePreview",
    "AnalyzeFeedback",
    "FormatValidationResults",
    "GenerateRefinementPlan",
    "AssessReadiness",
    "DetermineHITLStrategy",
    # Conversational Interface
    "InterpretUserIntent",
    "DetectMultiSkillNeeds",
    "GenerateClarifyingQuestion",
    "ConversationalAssessReadiness",
    "DeepUnderstandingSignature",
    "ConfirmUnderstandingBeforeCreation",
    "UnderstandingSummary",
    "PresentSkillForReview",
    "ProcessUserFeedback",
    "SuggestTestScenarios",
    "VerifyTDDPassed",
    "EnhanceSkillContent",
    # Conversational aliases
    "GenerateConversationalResponse",
    "ExtractUserIntent",
    "GenerateFollowUp",
    "SummarizeConversation",
    # Signature Optimization
    "AnalyzeSignatureFailures",
    "ProposeSignatureImprovement",
    "ValidateSignatureImprovement",
    "CompareSignatureVersions",
]
