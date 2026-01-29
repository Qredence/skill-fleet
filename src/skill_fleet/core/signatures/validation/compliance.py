"""
DSPy signatures for Phase 3: Validation & Quality Assurance.

These signatures validate skill compliance, assess quality,
and suggest refinements.
"""

import dspy


class ValidateCompliance(dspy.Signature):
    """
    Validate agentskills.io compliance of skill content.

    Check YAML frontmatter, file structure, naming conventions,
    and required sections.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete SKILL.md content to validate")
    taxonomy_path: str = dspy.InputField(desc="Expected taxonomy path (e.g., 'python/async')")

    # Outputs
    passed: bool = dspy.OutputField(desc="Whether skill passes all compliance checks")
    compliance_score: float = dspy.OutputField(desc="Score 0.0-1.0 of compliance level")
    issues: list[str] = dspy.OutputField(desc="List of compliance issues found (empty if passed)")
    critical_issues: list[str] = dspy.OutputField(desc="Issues that MUST be fixed (blocking)")
    warnings: list[str] = dspy.OutputField(desc="Non-blocking issues that should be addressed")
    auto_fixable: list[str] = dspy.OutputField(desc="Issues that can be automatically fixed")


class AssessQuality(dspy.Signature):
    """
    Assess overall quality of skill content.

    Evaluate completeness, clarity, usefulness, and accuracy
    of the generated skill.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete SKILL.md content")
    plan: str = dspy.InputField(desc="Original plan for comparison")
    success_criteria: list[str] = dspy.InputField(
        desc="Success criteria from plan to check against"
    )

    # Outputs
    overall_score: float = dspy.OutputField(desc="Overall quality score 0.0-1.0")
    completeness: float = dspy.OutputField(desc="Completeness score 0.0-1.0")
    clarity: float = dspy.OutputField(desc="Clarity score 0.0-1.0")
    usefulness: float = dspy.OutputField(desc="Usefulness score 0.0-1.0")
    accuracy: float = dspy.OutputField(desc="Technical accuracy score 0.0-1.0")
    strengths: list[str] = dspy.OutputField(desc="3-5 content strengths")
    weaknesses: list[str] = dspy.OutputField(desc="3-5 areas for improvement")
    meets_success_criteria: list[str] = dspy.OutputField(desc="Which success criteria are met")
    missing_success_criteria: list[str] = dspy.OutputField(
        desc="Which success criteria are not met"
    )


class RefineSkill(dspy.Signature):
    """
    Refine skill content based on quality assessment.

    Apply targeted improvements to address weaknesses while
    preserving strengths.
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current SKILL.md content")
    weaknesses: list[str] = dspy.InputField(desc="Quality weaknesses to address")
    target_score: float = dspy.InputField(desc="Target quality score to achieve", default=0.8)

    # Outputs
    refined_content: str = dspy.OutputField(desc="Improved SKILL.md content")
    improvements_made: list[str] = dspy.OutputField(desc="Specific improvements applied")
    new_score_estimate: float = dspy.OutputField(
        desc="Estimated new quality score after refinements"
    )
    requires_another_pass: bool = dspy.OutputField(desc="Whether another refinement pass is needed")


class SuggestValidationTests(dspy.Signature):
    """
    Suggest tests to validate skill correctness.

    Generate test cases that verify the skill's code examples
    work correctly.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Complete SKILL.md content")
    code_examples: list[str] = dspy.InputField(
        desc="List of code example titles/names in the skill"
    )

    # Outputs
    test_cases: list[dict] = dspy.OutputField(
        desc="List of test cases: [{name, description, input, expected_output}]"
    )
    test_coverage: float = dspy.OutputField(
        desc="Estimated test coverage of code examples (0.0-1.0)"
    )
    manual_verification_needed: list[str] = dspy.OutputField(
        desc="Examples that need manual testing (can't be automated)"
    )
