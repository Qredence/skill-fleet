"""DSPy signatures for Phase 2: Content Generation.

Phase 2 generates the actual skill content based on the plan from Phase 1.
Uses BestOfN pattern for quality assurance.

Workflow:
1. GenerateSkillContent (main generation, used with BestOfN)
2. HITL: GeneratePreview (show user preview)
3. IncorporateFeedback (refine based on user feedback)

All signatures use Pydantic models for type safety.
"""

from __future__ import annotations

import dspy

from ...models import (
    BestPractice,
    Capability,
    SkillMetadata,
    TestCase,
    UsageExample,
)

# =============================================================================
# Step 2.1: Generate Skill Content (Main Generation)
# =============================================================================


class GenerateSkillContent(dspy.Signature):
    """Generate complete SKILL.md content based on the plan.

    This is the main content generation step. Create comprehensive,
    well-structured skill documentation that follows agentskills.io format.

    Requirements:
    - YAML frontmatter at top (name in kebab-case, description)
    - Clear sections with headers
    - Code examples with explanations
    - Best practices and gotchas
    - Usage examples
    - Test cases where applicable

    This signature is used with dspy.BestOfN to generate multiple
    candidates and select the best one based on quality metrics.
    """

    # Inputs
    skill_metadata: SkillMetadata = dspy.InputField(
        desc="Complete skill metadata from Phase 1 synthesis"
    )
    content_plan: str = dspy.InputField(
        desc="Detailed content plan: sections, topics, example count"
    )
    generation_instructions: str = dspy.InputField(
        desc="Specific instructions for generation (style, tone, depth)"
    )
    parent_skills_content: str = dspy.InputField(
        desc="Content from parent skills for reference and consistency"
    )
    dependency_summaries: str = dspy.InputField(
        desc="Summaries of dependency skills (to reference appropriately)"
    )

    # Outputs
    skill_content: str = dspy.OutputField(
        desc="Complete SKILL.md content with YAML frontmatter, all sections, examples, and best practices"
    )
    usage_examples: list[UsageExample] = dspy.OutputField(
        desc="3-5 concrete usage examples showing how to use this skill"
    )
    best_practices: list[BestPractice] = dspy.OutputField(desc="5-10 best practices and gotchas")
    test_cases: list[TestCase] = dspy.OutputField(
        desc="Test cases to verify skill understanding (if applicable)"
    )
    estimated_reading_time: int = dspy.OutputField(desc="Estimated reading time in minutes")


# =============================================================================
# Step 2.2: Generate Content Sections (Chunked Generation Alternative)
# =============================================================================


class GenerateSkillSection(dspy.Signature):
    """Generate a single section of skill content.

    Alternative to generating all content at once. Can be used for
    very large skills where full generation would exceed token limits.

    Generate one section at a time, maintaining consistency with
    the overall skill plan and previously generated sections.
    """

    # Inputs
    section_name: str = dspy.InputField(
        desc="Name of section to generate (e.g., 'Core Concepts', 'Advanced Patterns')"
    )
    section_topics: list[str] = dspy.InputField(desc="Topics to cover in this section")
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata for context")
    previous_sections: str = dspy.InputField(desc="Previously generated sections for consistency")
    style_guide: str = dspy.InputField(desc="Style guide from generation instructions")

    # Outputs
    section_content: str = dspy.OutputField(
        desc="Complete markdown content for this section with examples"
    )
    code_examples: list[str] = dspy.OutputField(desc="Code examples included in this section")
    internal_links: list[str] = dspy.OutputField(
        desc="Links to other sections or skills (for later resolution)"
    )


# =============================================================================
# Step 2.3: Incorporate User Feedback
# =============================================================================


class IncorporateFeedback(dspy.Signature):
    """Incorporate user feedback from HITL preview checkpoint.

    User has reviewed the preview and provided feedback. Make changes
    to the skill content based on their suggestions.

    Changes might include:
    - Add missing sections or examples
    - Adjust tone or style
    - Expand or reduce scope
    - Fix inaccuracies

    This signature uses dspy.Refine for iterative improvement.
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current skill content")
    user_feedback: str = dspy.InputField(
        desc="User's feedback (free-form text or structured change requests)"
    )
    change_requests: str = dspy.InputField(
        desc="JSON structured change requests from AnalyzeFeedback"
    )
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata for context")

    # Outputs
    refined_content: str = dspy.OutputField(desc="Refined skill content incorporating all feedback")
    changes_made: list[str] = dspy.OutputField(desc="List of changes made (for user review)")
    unaddressed_feedback: list[str] = dspy.OutputField(
        desc="Any feedback that couldn't be addressed (with explanation why)"
    )
    improvement_score: float = dspy.OutputField(
        desc="Self-assessment of improvement 0-1. >0.7 means significant improvement"
    )


# =============================================================================
# Step 2.4: Generate Capability Implementations
# =============================================================================


class GenerateCapabilityImplementation(dspy.Signature):
    """Generate implementation details for a specific capability.

    Each skill has multiple capabilities. This signature generates
    detailed implementation guidance for one capability.

    Capability implementation includes:
    - Code examples
    - Configuration options
    - Common patterns
    - Error handling
    """

    # Inputs
    capability: Capability = dspy.InputField(desc="The capability to generate implementation for")
    skill_context: str = dspy.InputField(
        desc="Context from the overall skill (metadata, other capabilities)"
    )
    target_level: str = dspy.InputField(desc="Target skill level (beginner/intermediate/advanced)")

    # Outputs
    implementation_guide: str = dspy.OutputField(
        desc="Complete implementation guide with code examples and explanations"
    )
    code_snippets: list[str] = dspy.OutputField(
        desc="Standalone code snippets (can be extracted and run)"
    )
    configuration: dict = dspy.OutputField(desc="Configuration options and their effects")
    common_errors: list[str] = dspy.OutputField(desc="Common errors and how to fix them")
