"""DSPy signatures for Phase 3: Validation & Refinement.

Phase 3 validates the generated skill content and iteratively refines
it based on validation results and user feedback.

Workflow:
1. ValidateSkill (check agentskills.io compliance, content quality)
2. HITL: FormatValidationResults (show results to user)
3. RefineSkillFromFeedback (iterative refinement with dspy.Refine)

All signatures use Pydantic models for type safety.
"""

from __future__ import annotations

import dspy

from ...models import (
    SkillMetadata,
    ValidationCheckItem,
    ValidationReport,
)

# =============================================================================
# Step 3.1: Validate Skill
# =============================================================================


class ValidateSkill(dspy.Signature):
    """Comprehensive validation of generated skill content.

    Validate against multiple criteria:
    1. **agentskills.io Compliance**:
       - YAML frontmatter present and valid
       - Name in kebab-case
       - Description present

    2. **Content Quality**:
       - All planned sections present
       - Sufficient examples (at least 3 per major section)
       - Code examples are valid and runnable
       - Best practices included

    3. **Structural Integrity**:
       - Proper markdown formatting
       - No broken links
       - Consistent heading levels

    4. **Metadata Consistency**:
       - Metadata matches content
       - Tags appropriate
       - Dependencies correctly referenced

    Return a structured validation report with specific issues
    and suggested fixes.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete SKILL.md content to validate")
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata")
    content_plan: str = dspy.InputField(
        desc="Original content plan from Phase 1 (to verify all planned content is present)"
    )
    validation_rules: str = dspy.InputField(desc="JSON validation rules and thresholds")

    # Outputs
    validation_report: ValidationReport = dspy.OutputField(
        desc="Complete validation report with: passed, checks, issues, warnings"
    )
    critical_issues: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues that MUST be fixed (blocks skill acceptance)"
    )
    warnings: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues that SHOULD be fixed but not blocking"
    )
    suggestions: list[str] = dspy.OutputField(desc="Optional suggestions for improvement")
    overall_score: float = dspy.OutputField(
        desc="Overall quality score 0-1. >0.8 means high quality"
    )


# =============================================================================
# Step 3.2: Analyze Validation Issues
# =============================================================================


class AnalyzeValidationIssues(dspy.Signature):
    """Analyze validation issues and determine fix strategy.

    For each validation issue, determine:
    - Can it be auto-fixed?
    - What's the fix strategy?
    - What's the priority?
    - Are there related issues that should be fixed together?
    """

    # Inputs
    validation_report: str = dspy.InputField(desc="JSON validation report with all issues")
    skill_content: str = dspy.InputField(desc="Current skill content")

    # Outputs
    auto_fixable_issues: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues that can be automatically fixed without user input"
    )
    user_input_needed: list[ValidationCheckItem] = dspy.OutputField(
        desc="Issues that require user input or decision"
    )
    fix_strategies: dict[str, str] = dspy.OutputField(
        desc="Fix strategy for each issue: {issue_id: strategy}"
    )
    estimated_fix_time: str = dspy.OutputField(
        desc="Estimated fix time: 'quick' (<1 min), 'moderate' (1-5 min), 'significant' (>5 min)"
    )


# =============================================================================
# Step 3.3: Refine Skill from Feedback
# =============================================================================


class RefineSkillFromFeedback(dspy.Signature):
    """Refine skill content based on validation issues and user feedback.

    This signature is used with dspy.Refine for iterative improvement.
    Each iteration should:
    1. Address highest priority issues first
    2. Maintain consistency with existing content
    3. Preserve what's working well
    4. Re-validate after changes

    Continue refining until:
    - All critical issues resolved
    - User is satisfied (via HITL)
    - Max iterations reached
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current skill content")
    validation_issues: str = dspy.InputField(desc="JSON list of validation issues to address")
    user_feedback: str = dspy.InputField(
        desc="User's feedback on what to change (may be empty for auto-fix)"
    )
    fix_strategies: str = dspy.InputField(desc="JSON fix strategies from AnalyzeValidationIssues")
    iteration_number: int = dspy.InputField(desc="Current iteration number (1, 2, 3, ...)")

    # Outputs
    refined_content: str = dspy.OutputField(desc="Refined skill content with issues addressed")
    issues_resolved: list[str] = dspy.OutputField(
        desc="List of issue IDs that were resolved in this iteration"
    )
    issues_remaining: list[str] = dspy.OutputField(
        desc="List of issue IDs still remaining (empty if all resolved)"
    )
    changes_summary: str = dspy.OutputField(
        desc="Summary of changes made in this iteration (for user review)"
    )
    ready_for_acceptance: bool = dspy.OutputField(
        desc="True if all critical issues resolved and ready for user acceptance"
    )


# =============================================================================
# Step 3.4: Generate Auto-Fix
# =============================================================================


class GenerateAutoFix(dspy.Signature):
    """Generate automatic fixes for common validation issues.

    For issues that don't require user input, generate the fix automatically:
    - Add missing YAML frontmatter
    - Convert name to kebab-case
    - Fix markdown formatting
    - Add missing sections (with placeholder content)
    - Fix broken links
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Current skill content with issues")
    issue: ValidationCheckItem = dspy.InputField(desc="The specific validation issue to auto-fix")
    fix_strategy: str = dspy.InputField(desc="Strategy for fixing this issue")

    # Outputs
    fixed_content: str = dspy.OutputField(desc="Skill content with this specific issue fixed")
    fix_applied: str = dspy.OutputField(desc="Description of what was changed")
    verification: str = dspy.OutputField(desc="How to verify the fix worked (for re-validation)")


# =============================================================================
# Step 3.5: Quality Assessment
# =============================================================================


class AssessSkillQuality(dspy.Signature):
    """Assess overall quality of skill content beyond validation.

    While ValidateSkill checks compliance and structure, this signature
    evaluates content quality:
    - Are examples clear and helpful?
    - Is the writing engaging?
    - Are explanations thorough?
    - Is the skill actually useful?

    Provides qualitative feedback for refinement.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete skill content")
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata")
    target_level: str = dspy.InputField(desc="Target level: beginner/intermediate/advanced")

    # Outputs
    quality_score: float = dspy.OutputField(
        desc="Overall quality score 0-1. >0.8 is excellent, 0.6-0.8 is good, <0.6 needs improvement"
    )
    strengths: list[str] = dspy.OutputField(desc="What's good about this skill (3-5 points)")
    weaknesses: list[str] = dspy.OutputField(desc="What could be improved (3-5 points)")
    recommendations: list[str] = dspy.OutputField(desc="Specific recommendations for improvement")
    audience_alignment: float = dspy.OutputField(
        desc="How well content matches target level 0-1. >0.8 means well-aligned"
    )
