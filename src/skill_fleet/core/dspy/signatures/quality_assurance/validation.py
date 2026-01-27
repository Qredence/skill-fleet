"""
DSPy signatures for Phase 3: Validation & Refinement.

Phase 3 validates generated skill content and iteratively refines
it based on validation results and user feedback.

Workflow:
1. ValidateSkill (check agentskills.io compliance, content quality)
2. HITL: FormatValidationResults (show results to user)
3. RefineSkillFromFeedback (iterative refinement with dspy.Refine)

All signatures use Pydantic models for type safety.
"""

import dspy

from ....models import (
    SkillMetadata,
    ValidationCheckItem,
    ValidationReport,
)

# =============================================================================
# Step 3.1: Validate Skill
# =============================================================================


class ValidateSkill(dspy.Signature):
    """
    Validate skill against agentskills.io spec and quality standards.

    Check: (1) spec compliance (frontmatter, kebab-case name), (2) content quality
    (sections, examples, patterns), (3) structure (markdown, links), (4) metadata consistency.
    Report specific, fixable issues.
    """

    # Inputs
    skill_content: str = dspy.InputField(
        desc="Complete SKILL.md content with frontmatter to validate"
    )
    skill_metadata: SkillMetadata = dspy.InputField(
        desc="Skill metadata object for consistency checks"
    )
    content_plan: str = dspy.InputField(
        desc="Original Phase 1 content plan to verify all planned sections/patterns present"
    )
    validation_rules: str = dspy.InputField(
        desc="JSON validation rules: {min_quality_score: 0.60, required_sections: [...], ...}"
    )

    # Outputs
    validation_report: ValidationReport = dspy.OutputField(
        desc="Report object: passed (bool overall), checks (list of ValidationCheckItem), "
        "errors (blocking issues), warnings (non-blocking). Includes spec compliance and quality checks."
    )
    critical_issues: list[ValidationCheckItem] = dspy.OutputField(
        desc="0-10 blocking issues preventing approval. Each has: check_id, severity (critical), "
        "message (specific issue), suggested_fix (how to fix). Empty list [] if no critical issues."
    )
    warnings: list[ValidationCheckItem] = dspy.OutputField(
        desc="0-10 non-blocking issues (improvements recommended). Each has: check_id, severity (warning), "
        "message, suggested_fix. Include: missing optional sections, suboptimal examples, style issues."
    )
    suggestions: list[str] = dspy.OutputField(
        desc="0-5 optional improvement suggestions beyond validation. "
        "Format: concrete, actionable advice (e.g., 'Add more edge case examples'). "
        "Empty list [] if skill already excellent."
    )
    overall_score: float = dspy.OutputField(
        desc="Quality score 0.0-1.0 from skill_quality_metric. >0.80 = excellent (approve), "
        "0.60-0.80 = good (minor fixes), <0.60 = needs revision. "
        "Matches quality scoring used in optimization metrics."
    )


# =============================================================================
# Step 3.2: Analyze Validation Issues
# =============================================================================


class AnalyzeValidationIssues(dspy.Signature):
    """
    Categorize validation issues and plan fixes.

    Determine: auto-fixable vs. needs user input, fix strategies, priority, grouped fixes.
    Enable efficient batch processing of issues.
    """

    # Inputs
    validation_report: str = dspy.InputField(
        desc="JSON ValidationReport with all issues, warnings, and quality scores"
    )
    skill_content: str = dspy.InputField(desc="Current SKILL.md content that has validation issues")

    # Outputs
    auto_fixable_issues: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues fixable without user input (e.g., missing frontmatter, kebab-case conversion, "
        "markdown formatting). Each has: check_id, severity, suggested_fix. Typical: 0-5 items."
    )
    user_input_needed: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues requiring user decision (e.g., scope ambiguity, missing domain knowledge, "
        "conflicting requirements). Each has: check_id, severity, suggested_fix, question_for_user. "
        "Empty list [] if all issues are auto-fixable."
    )
    fix_strategies: dict[str, str] = dspy.OutputField(
        desc="Fix strategy mapping {issue_id: 'specific fix approach'}. "
        "Be concrete: 'Add YAML frontmatter with name and description' not 'Fix frontmatter'. "
        "Include for ALL issues (auto-fixable + user-input)."
    )
    estimated_fix_time: str = dspy.OutputField(
        desc="Time estimate for all fixes: quick (<1 min, formatting only), "
        "moderate (1-5 min, add sections), significant (>5 min, major content revision)"
    )


# =============================================================================
# Step 3.3: Refine Skill from Feedback
# =============================================================================


class RefineSkillFromFeedback(dspy.Signature):
    """
    Apply fixes to skill content addressing validation issues and user feedback.

    Prioritize critical issues, maintain quality, preserve strengths.
    Use iterative refinement with dspy.Refine module. Stop when quality threshold met.
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current SKILL.md content requiring refinement")
    validation_issues: str = dspy.InputField(
        desc="JSON array of ValidationCheckItem objects ordered by severity (critical first)"
    )
    user_feedback: str = dspy.InputField(
        desc="User feedback from HITL review. Empty string '' for auto-fix mode. "
        "May include: additional requirements, tone preferences, example requests."
    )
    fix_strategies: str = dspy.InputField(
        desc="JSON dict mapping issue_id to fix_strategy from AnalyzeValidationIssues"
    )
    iteration_number: int = dspy.InputField(
        desc="Current iteration 1-5. Higher iterations should make smaller, targeted changes. "
        "Stop iterating if no progress after 2 rounds."
    )

    # Outputs
    refined_content: str = dspy.OutputField(
        desc="Improved SKILL.md content with fixes applied. Maintain: structure, style, quality indicators. "
        "Only change what's needed to address issues. Preserve good sections unchanged."
    )
    issues_resolved: list[str] = dspy.OutputField(
        desc="Issue IDs fully resolved this iteration (e.g., ['missing_frontmatter', 'invalid_name']). "
        "Be conservative - only mark as resolved if truly fixed."
    )
    issues_remaining: list[str] = dspy.OutputField(
        desc="Issue IDs still unresolved after this iteration. Empty list [] means ready for acceptance. "
        "Include new issues discovered while fixing if any."
    )
    changes_summary: str = dspy.OutputField(
        desc="2-5 sentence summary of changes: what was fixed, how, why. "
        "Use past tense: 'Added frontmatter with...', 'Fixed kebab-case name...'. For user review."
    )
    ready_for_acceptance: bool = dspy.OutputField(
        desc="True if: (1) all critical issues resolved, (2) quality_score >0.60, (3) no blocking errors. "
        "False if any critical issues remain or score too low. Conservative evaluation."
    )


# =============================================================================
# Step 3.4: Generate Auto-Fix
# =============================================================================


class GenerateAutoFix(dspy.Signature):
    """
    Generate automatic fix for a single validation issue.

    Apply targeted fix without affecting other content. Common fixes: frontmatter, kebab-case,
    markdown format, missing sections, broken links. Preserve quality and style.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Current SKILL.md content with validation issue")
    issue: ValidationCheckItem = dspy.InputField(
        desc="Specific issue to fix (has: check_id, severity, message, suggested_fix)"
    )
    fix_strategy: str = dspy.InputField(
        desc="Concrete fix strategy from AnalyzeValidationIssues (how to fix this issue)"
    )

    # Outputs
    fixed_content: str = dspy.OutputField(
        desc="SKILL.md content with ONLY this issue fixed. Preserve all other content exactly. "
        "Maintain markdown formatting, code blocks, and quality. Min changes to fix issue."
    )
    fix_applied: str = dspy.OutputField(
        desc="1-2 sentence description of change made. Be specific: 'Added YAML frontmatter with name=X and description=Y' "
        "not 'Fixed frontmatter'. Use past tense."
    )
    verification: str = dspy.OutputField(
        desc="How to verify this fix worked (for automated re-validation). "
        "Format: 'Check that...' or 'Verify...'. Enable automated confirmation."
    )


# =============================================================================
# Step 3.5: Quality Assessment
# =============================================================================


class AssessSkillQuality(dspy.Signature):
    """
    Assess content quality beyond structural validation.

    Evaluate: example clarity, writing engagement, explanation depth, practical usefulness.
    Use skill_quality_metric criteria. Provide actionable feedback for refinement.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete SKILL.md content to assess")
    skill_metadata: SkillMetadata = dspy.InputField(
        desc="Metadata for context: name, description, target audience"
    )
    target_level: str = dspy.InputField(
        desc="Target expertise level: beginner/intermediate/advanced/expert. "
        "Used to check if content complexity matches audience."
    )

    # Outputs
    quality_score: float = dspy.OutputField(
        desc="Quality score 0.0-1.0 using skill_quality_metric algorithm. "
        ">0.80 = excellent (has core principle, strong guidance, ❌/✅ contrasts), "
        "0.60-0.80 = good (minor gaps), <0.60 = needs work (missing critical elements). "
        "Includes penalty multiplier for missing quality indicators."
    )
    strengths: list[str] = dspy.OutputField(
        desc="3-5 specific strengths. Examples: 'Excellent ❌/✅ contrast patterns', "
        "'Clear core principle statement', 'Production-ready code examples'. "
        "Reference actual content, not generic praise."
    )
    weaknesses: list[str] = dspy.OutputField(
        desc="3-5 specific weaknesses with concrete details. Examples: 'Missing error handling in examples', "
        "'No strong guidance (Iron Law style)', 'Lacks real-world edge cases'. "
        "Be constructive and specific."
    )
    recommendations: list[str] = dspy.OutputField(
        desc="3-5 actionable recommendations. Format: 'Add X to Y section', 'Improve Z by doing W'. "
        "Prioritize by impact. Include line/section references where possible."
    )
    audience_alignment: float = dspy.OutputField(
        desc="Target level alignment 0.0-1.0. >0.80 = well-matched complexity, "
        "0.60-0.80 = acceptable, <0.60 = mismatch (too simple or too advanced). "
        "Consider: terminology complexity, assumed knowledge, example sophistication."
    )
