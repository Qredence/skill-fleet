"""
DSPy signature for validating skill structure against Anthropic's published requirements.

This signature validates skills against the requirements documented in the
Claude Skill Building Guide, including naming conventions, description format,
security restrictions, and size recommendations.
"""

import dspy


class ValidateSkillStructure(dspy.Signature):
    """
    Validate skill structure against Anthropic's published requirements.

    Checks naming conventions (kebab-case), description requirements (trigger phrases,
    length limits), security restrictions (no XML tags, reserved names), and
    size recommendations. Returns a validation report with specific errors and
    actionable fixes.

    Example:
        Input:
            skill_name: "My Cool Skill"
            description: "Helps with projects"
            skill_content: "# My Skill\n..."

        Output:
            name_valid: False
            name_errors: ["Name 'My Cool Skill' contains capital letters",
                         "Name 'My Cool Skill' contains spaces"]
            description_valid: False
            description_errors: ["Description missing trigger conditions"]
            overall_valid: False

    """

    # Inputs
    skill_name: str = dspy.InputField(
        desc="Proposed skill name as provided by the user or suggested by requirements gathering"
    )
    description: str = dspy.InputField(
        desc="Skill description from frontmatter or requirements. Should include what the skill does and when to use it."
    )
    skill_content: str = dspy.InputField(
        desc="Full SKILL.md content including frontmatter and body. Empty string if not yet generated.",
        default="",
    )

    # Name validation outputs
    name_valid: bool = dspy.OutputField(
        desc="True if skill name follows kebab-case (lowercase, hyphens, no spaces)"
    )
    name_errors: list[str] = dspy.OutputField(
        desc="List of naming issues found. Empty list if name_valid is True."
    )

    # Description validation outputs
    description_valid: bool = dspy.OutputField(
        desc="True if description meets all requirements (length, trigger conditions, no XML)"
    )
    description_errors: list[str] = dspy.OutputField(
        desc="Specific description issues preventing validation. Empty if description_valid is True."
    )
    description_warnings: list[str] = dspy.OutputField(
        desc="Suggested improvements for the description even if valid. May include tips for better trigger phrases."
    )

    # Content analysis outputs
    has_trigger_conditions: bool = dspy.OutputField(
        desc="True if description includes 'Use when', 'For when', or equivalent trigger condition indicators"
    )

    estimated_word_count: int = dspy.OutputField(
        desc="Approximate word count of skill_content. 0 if skill_content is empty."
    )

    size_recommendation: str = dspy.OutputField(
        desc="One of: 'optimal' (<3000 words), 'acceptable' (3000-5000), 'consider_splitting' (>5000)"
    )

    # Security validation outputs
    security_issues: list[str] = dspy.OutputField(
        desc="Security concerns found: XML angle brackets, reserved names ('claude', 'anthropic'), etc."
    )

    # Overall validation
    overall_valid: bool = dspy.OutputField(
        desc="True only if name_valid, description_valid are True and no security_issues exist"
    )
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for structure validation")
