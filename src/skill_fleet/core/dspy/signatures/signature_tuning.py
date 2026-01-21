"""
DSPy signatures for metric-driven signature tuning.

These signatures support the SignatureTuner module for analyzing
skill quality failures and proposing improved signatures.

Phase 1.2 of the DSPy quality improvement roadmap.
"""

from __future__ import annotations

from typing import Literal

import dspy

# =============================================================================
# Failure Analysis Signature
# =============================================================================


class AnalyzeSignatureFailures(dspy.Signature):
    """
    Analyze why a skill failed to meet quality thresholds.

    Identify root causes of low quality scores by examining:
    1. What quality indicators are missing (core principle, contrast patterns, etc.)
    2. What structural issues exist (missing sections, poor organization)
    3. What content gaps need addressing (examples, edge cases, anti-patterns)

    Focus on actionable, specific issues that signature improvements can address.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="The SKILL.md content that scored below threshold")
    current_signature: str = dspy.InputField(
        desc="The DSPy signature (inline or class-based) that generated this content"
    )
    metric_score: float = dspy.InputField(
        desc="Current quality score (0.0-1.0). Below 0.75 needs tuning."
    )
    target_score: float = dspy.InputField(desc="Target quality score to achieve (typically 0.80+)")
    quality_issues: str = dspy.InputField(
        desc="JSON array of specific quality issues from deterministic metrics"
    )

    # Outputs
    failure_categories: list[
        Literal[
            "missing_structure",
            "weak_guidance",
            "no_contrast_patterns",
            "insufficient_examples",
            "missing_core_principle",
            "poor_organization",
            "lacks_anti_patterns",
            "weak_audience_targeting",
            "missing_quick_reference",
        ]
    ] = dspy.OutputField(
        desc="1-4 failure categories from the predefined list. Most impactful first."
    )
    root_causes: list[str] = dspy.OutputField(
        desc="2-5 root causes explaining WHY the failures occurred. "
        "Format: specific, actionable statements like 'Signature lacks instruction for Iron Law'"
    )
    missing_quality_indicators: list[str] = dspy.OutputField(
        desc="1-5 missing Obra quality indicators: core_principle, iron_law, "
        "good_bad_contrast, strong_guidance, practical_examples"
    )
    improvement_directions: list[str] = dspy.OutputField(
        desc="2-4 high-level improvement directions. "
        "Format: 'Add X to signature to enforce Y' style statements"
    )
    priority_fixes: list[str] = dspy.OutputField(
        desc="Top 3 fixes ranked by impact on score. "
        "Each should be concrete and signature-addressable."
    )


# =============================================================================
# Signature Improvement Proposal
# =============================================================================


class ProposeSignatureImprovement(dspy.Signature):
    """
    Propose an improved DSPy signature to address quality failures.

    Generate a modified signature that:
    1. Adds explicit OutputField constraints for missing quality indicators
    2. Improves field descriptions to guide better LM outputs
    3. Adds format hints that encourage Obra-compliant content

    The improved signature should directly address the root causes identified.
    """

    # Inputs
    current_signature: str = dspy.InputField(
        desc="The current DSPy signature text (inline like 'a -> b' or class definition)"
    )
    failure_analysis: str = dspy.InputField(
        desc="JSON object with failure_categories, root_causes, improvement_directions"
    )
    target_score: float = dspy.InputField(
        desc="Target quality score to achieve (0.80+ for approval)"
    )
    skill_type: Literal["navigation_hub", "comprehensive", "minimal"] = dspy.InputField(
        desc="Skill style affecting weight of different quality indicators"
    )

    # Outputs
    improved_signature: str = dspy.OutputField(
        desc="The improved DSPy signature. If class-based, output full class definition. "
        "If inline, output the improved inline signature. "
        "Add/modify field descriptions to enforce quality indicators."
    )
    improvement_reasoning: str = dspy.OutputField(
        desc="2-4 sentences explaining what was changed and why. "
        "Reference specific root causes addressed."
    )
    expected_impact: str = dspy.OutputField(
        desc="Expected score improvement (e.g., '+0.10 to +0.15'). "
        "Be realistic based on changes made."
    )
    changes_made: list[str] = dspy.OutputField(
        desc="3-6 specific changes made to the signature. "
        "Format: 'Added X constraint to OutputField Y'"
    )
    confidence: float = dspy.OutputField(
        desc="Confidence this improvement will help (0.0-1.0). "
        ">0.8 = high confidence, 0.6-0.8 = medium, <0.6 = experimental"
    )


# =============================================================================
# Signature Improvement Validation
# =============================================================================


class ValidateSignatureImprovement(dspy.Signature):
    """
    Validate that a proposed signature improvement is safe and beneficial.

    Check that the improved signature:
    1. Is syntactically valid DSPy signature
    2. Doesn't remove essential fields
    3. Doesn't add contradictory constraints
    4. Is likely to improve quality without side effects
    """

    # Inputs
    original_signature: str = dspy.InputField(desc="The original DSPy signature before improvement")
    proposed_signature: str = dspy.InputField(desc="The proposed improved DSPy signature")
    improvement_reasoning: str = dspy.InputField(
        desc="Explanation of why this improvement should help"
    )

    # Outputs
    is_valid: bool = dspy.OutputField(
        desc="True if the signature is syntactically valid and complete. "
        "False if it has errors or missing required components."
    )
    is_improvement: bool = dspy.OutputField(
        desc="True if the changes are likely to improve quality. "
        "False if changes might hurt quality or are neutral."
    )
    validation_notes: str = dspy.OutputField(
        desc="1-3 sentences summarizing validation findings. "
        "Mention what was checked and any concerns."
    )
    potential_issues: list[str] = dspy.OutputField(
        desc="0-3 potential issues or risks with the improvement. "
        "Empty list if no concerns. Be specific about what could go wrong."
    )
    recommendation: Literal["approve", "approve_with_caution", "reject"] = dspy.OutputField(
        desc="Final recommendation: approve (safe to use), "
        "approve_with_caution (use but monitor), reject (don't use)"
    )


# =============================================================================
# Signature Comparison (for A/B testing)
# =============================================================================


class CompareSignatureVersions(dspy.Signature):
    """
    Compare two signature versions to determine which is better.

    Used for A/B testing of signature improvements to validate
    that changes actually improve quality in practice.
    """

    # Inputs
    signature_a: str = dspy.InputField(desc="First signature version (typically original)")
    signature_b: str = dspy.InputField(desc="Second signature version (typically improved)")
    output_a: str = dspy.InputField(desc="Sample output from signature_a")
    output_b: str = dspy.InputField(desc="Sample output from signature_b")
    evaluation_criteria: str = dspy.InputField(
        desc="JSON list of evaluation criteria (e.g., 'has_core_principle', 'has_contrast')"
    )

    # Outputs
    winner: Literal["a", "b", "tie"] = dspy.OutputField(
        desc="Which signature produced better output: 'a', 'b', or 'tie'"
    )
    score_a: float = dspy.OutputField(desc="Quality score for output_a (0.0-1.0)")
    score_b: float = dspy.OutputField(desc="Quality score for output_b (0.0-1.0)")
    comparison_notes: str = dspy.OutputField(
        desc="2-4 sentences comparing the outputs. "
        "Highlight key differences that determined the winner."
    )
    criteria_breakdown: dict[str, str] = dspy.OutputField(
        desc="Mapping of each criterion to winner ('a' or 'b'). "
        "E.g., {'has_core_principle': 'b', 'has_contrast': 'a'}"
    )


__all__ = [
    "AnalyzeSignatureFailures",
    "ProposeSignatureImprovement",
    "ValidateSignatureImprovement",
    "CompareSignatureVersions",
]
