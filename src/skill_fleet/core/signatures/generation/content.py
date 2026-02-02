"""
DSPy signatures for Phase 2: Content Generation.

These signatures generate skill content including SKILL.md,
examples, and supporting documentation.
"""

from typing import Any

import dspy
from pydantic import BaseModel, Field


class ContentOutlineItem(BaseModel):
    """Single item in the content outline."""

    title: str = Field(description="Section title")
    description: str = Field(description="What this section covers")
    estimated_length: str = Field(default="medium", description="short/medium/long")


class SkillPlan(BaseModel):
    """Structured skill generation plan."""

    skill_name: str = Field(description="Name of the skill")
    skill_description: str = Field(description="Brief description of the skill")
    content_outline: list[ContentOutlineItem] = Field(description="Planned sections")
    generation_guidance: str = Field(default="", description="Specific guidance for generation")
    skill_category: str = Field(default="other", description="Category of the skill")
    required_sections: list[str] = Field(default_factory=list, description="Required sections")
    required_elements: list[str] = Field(default_factory=list, description="Required elements")
    example_skills: list[str] = Field(default_factory=list, description="Example skill names")


class SkillUnderstanding(BaseModel):
    """Structured understanding from Phase 1."""

    domain: str = Field(description="Skill domain")
    category: str = Field(description="Skill category")
    target_level: str = Field(description="Target expertise level")
    topics: list[str] = Field(description="Topics to cover")
    constraints: list[str] = Field(default_factory=list, description="Constraints")
    requirements: dict[str, Any] = Field(default_factory=dict, description="Requirements")
    intent: dict[str, Any] = Field(default_factory=dict, description="Intent analysis")
    taxonomy: dict[str, Any] = Field(default_factory=dict, description="Taxonomy info")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")


class GenerateSkillContent(dspy.Signature):
    """
    Generate complete SKILL.md content with YAML frontmatter.

    Create production-ready skill documentation following agentskills.io spec.
    Content should be practical, actionable, and include working examples.
    """

    # Inputs
    plan: SkillPlan = dspy.InputField(desc="Structured skill generation plan")
    understanding: SkillUnderstanding = dspy.InputField(
        desc="Structured understanding from Phase 1"
    )
    skill_style: str = dspy.InputField(
        desc="Style: 'comprehensive' (detailed), 'minimal' (concise), or 'navigation_hub' (short + subdirs)",
        default="comprehensive",
    )

    # Outputs
    skill_content: str = dspy.OutputField(
        desc="Complete SKILL.md content with YAML frontmatter (--- name: ... description: ... ---) followed by markdown"
    )
    sections_generated: list[str] = dspy.OutputField(
        desc="List of section titles actually generated"
    )
    code_examples_count: int = dspy.OutputField(desc="Number of code examples included")
    estimated_reading_time: int = dspy.OutputField(desc="Estimated reading time in minutes")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for content generation")


class GenerateSkillSection(dspy.Signature):
    """
    Generate a specific section of skill content.

    Used for generating individual sections when breaking up large skills,
    or for subdirectory files in navigation_hub style.
    """

    # Inputs
    section_title: str = dspy.InputField(desc="Title of the section to generate")
    section_outline: str = dspy.InputField(desc="Bullet points describing what to cover")
    plan: str = dspy.InputField(desc="Overall skill plan for context")
    examples_needed: bool = dspy.InputField(desc="Whether to include code examples", default=True)

    # Outputs
    section_content: str = dspy.OutputField(desc="Complete markdown content for this section")
    examples_included: list[str] = dspy.OutputField(
        desc="List of example titles/descriptions included"
    )
    key_points: list[str] = dspy.OutputField(desc="3-5 key takeaways from this section")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning process for section generation")


class IncorporateFeedback(dspy.Signature):
    """
    Revise skill content based on user feedback.

    Apply specific changes requested by user while maintaining
    overall structure and quality of the skill.
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current SKILL.md content")
    feedback: str = dspy.InputField(desc="User feedback with requested changes")
    change_requests: list[str] = dspy.InputField(desc="Specific change requests as bullet points")

    # Outputs
    revised_content: str = dspy.OutputField(desc="Updated SKILL.md with feedback incorporated")
    changes_made: list[str] = dspy.OutputField(desc="List of specific changes that were applied")
    changes_rejected: list[str] = dspy.OutputField(
        desc="Feedback items that couldn't be applied (with reasons)"
    )
    quality_impact: str = dspy.OutputField(
        desc="Assessment of how changes affect quality (improved/unchanged/degraded)"
    )
    reasoning: dspy.Reasoning = dspy.OutputField(
        desc="Reasoning process for feedback incorporation"
    )


class GenerateCodeExamples(dspy.Signature):
    """
    Generate practical code examples for a skill.

    Create working, tested code examples that demonstrate
    the concepts being taught.
    """

    # Inputs
    concept: str = dspy.InputField(desc="Concept or pattern to demonstrate")
    language: str = dspy.InputField(desc="Programming language (e.g., 'python', 'typescript')")
    difficulty: str = dspy.InputField(
        desc="Difficulty level: 'basic', 'intermediate', 'advanced'", default="intermediate"
    )
    include_tests: bool = dspy.InputField(desc="Whether to include test cases", default=True)

    # Outputs
    example_code: str = dspy.OutputField(desc="Complete, runnable code example with comments")
    explanation: str = dspy.OutputField(desc="Line-by-line or section explanation of the code")
    common_pitfalls: list[str] = dspy.OutputField(desc="Common mistakes and how to avoid them")
    test_cases: str = dspy.OutputField(
        desc="Test cases to verify the example works (if include_tests=True)"
    )
    reasoning: dspy.Reasoning = dspy.OutputField(
        desc="Reasoning process for code example generation"
    )
