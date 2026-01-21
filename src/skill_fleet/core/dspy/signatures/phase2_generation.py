"""DSPy signatures for Phase 2: Content Generation.

Phase 2 generates the actual skill content based on the plan from Phase 1.
Uses BestOfN pattern for quality assurance.

Workflow:
1. GenerateSkillContent (main generation, used with BestOfN)
2. HITL: GeneratePreview (show user preview)
3. IncorporateFeedback (refine based on user feedback)

All signatures use Pydantic models for type safety.

v2 Golden Standard (Jan 2026):
- Supports 3 skill styles: navigation_hub, comprehensive, minimal
- Progressive disclosure via subdirectory files (references/, guides/, etc.)
- Simplified frontmatter (no metadata.json required)
"""

from __future__ import annotations

from typing import Literal

import dspy

from ...models import (
    BestPractice,
    Capability,
    SkillMetadata,
    TestCase,
    UsageExample,
)

# =============================================================================
# Skill Style Type
# =============================================================================

SkillStyle = Literal["navigation_hub", "comprehensive", "minimal"]

# =============================================================================
# Step 2.1: Generate Skill Content (Main Generation)
# =============================================================================


class GenerateSkillContent(dspy.Signature):
    """Generate production-ready SKILL.md following agentskills.io v2 Golden Standard (Jan 2026).

    Create comprehensive, well-structured documentation with ❌/✅ contrast patterns,
    core principles, actionable guidance, and real-world impact.

    FRONTMATTER (v0.2): Keep minimal - name + description ONLY.
    - name: kebab-case, max 64 chars (must match directory)
    - description: Triggering conditions (WHEN to use), not workflow summary. Max 1024 chars.
    - NO metadata block in SKILL.md (move to metadata.json for tooling)

    REQUIRED SECTIONS: When to Use, Quick Start, Core Patterns with ❌/✅, Real-World Impact, Validation.
    QUALITY INDICATORS: Core principle statement, Iron Law style guidance, paired Good/Bad examples.

    Match style to content:
    - navigation_hub (~100-300 lines): Complex topics, use subdirectory references
    - comprehensive (~400-800 lines): Self-contained workflows and procedures
    - minimal (~50-150 lines): Focused single-purpose guidance
    """

    # Inputs
    skill_metadata: SkillMetadata = dspy.InputField(
        desc="Complete skill metadata from Phase 1 synthesis"
    )
    skill_style: SkillStyle = dspy.InputField(
        desc="Skill style: navigation_hub (short + subdirs), comprehensive (long inline), "
        "or minimal (focused). Determines SKILL.md length and subdirectory usage."
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

    # Outputs - Core content
    skill_content: str = dspy.OutputField(
        desc="Complete SKILL.md with minimal YAML frontmatter (v0.2: name + description only). "
        "MUST include: (1) **Core principle:** statement, "
        "(2) When to Use section (triggering conditions), (3) Quick Start (copy-paste ready), "
        "(4) Core Patterns with ❌ anti-patterns and ✅ production patterns, "
        "(5) Real-World Impact (measurable outcomes), (6) Validation section with CLI commands. "
        "For navigation_hub: reference subdirectory files. For comprehensive: inline all content. "
        "Use strong imperative guidance (ALWAYS/NEVER/MUST). Min 50 lines, production-ready quality."
    )
    usage_examples: list[UsageExample] = dspy.OutputField(
        desc="3-5 concrete, executable usage examples. Each must be copy-paste ready with clear context, "
        "expected output, and common variations. Prefer real-world scenarios over toy examples."
    )
    best_practices: list[BestPractice] = dspy.OutputField(
        desc="5-10 actionable best practices with specific guidance. Include gotchas, common mistakes, "
        "and red flags. Each should be concrete (not generic) with examples where relevant."
    )
    test_cases: list[TestCase] = dspy.OutputField(
        desc="2-5 test cases to verify skill understanding. Include: input scenario, expected approach, "
        "and success criteria. Optional but recommended for procedural skills."
    )
    estimated_reading_time: int = dspy.OutputField(
        desc="Estimated reading time in minutes (integer 1-30). Calculate based on word count: "
        "~200 words per minute for technical content."
    )

    # Outputs - Subdirectory files (for navigation_hub and some comprehensive skills)
    reference_files: dict[str, str] = dspy.OutputField(
        desc="Files for references/ directory. Format: {'filename.md': 'content'}. "
        "Each file: complete, self-contained reference doc (API details, pattern catalogs, concept guides). "
        "Use kebab-case filenames. Empty dict {} if not using progressive disclosure. "
        "Typical for navigation_hub style (2-5 reference files)."
    )
    guide_files: dict[str, str] = dspy.OutputField(
        desc="Files for guides/ directory. Format: {'filename.md': 'content'}. "
        "Each file: step-by-step workflow or troubleshooting guide with numbered steps. "
        "Include prerequisites, expected outcomes, and common pitfalls. "
        "Empty dict {} if not needed. Typical for comprehensive skills with multiple workflows."
    )
    template_files: dict[str, str] = dspy.OutputField(
        desc="Files for templates/ directory. Format: {'filename.ext': 'content'}. "
        "Production-ready boilerplate code files. Must be copy-paste ready, include comments, "
        "and handle edge cases. Use appropriate file extensions (.py, .js, .yaml, etc.). "
        "Empty dict {} if no boilerplate needed."
    )
    script_files: dict[str, str] = dspy.OutputField(
        desc="Files for scripts/ directory. Format: {'filename.ext': 'content'}. "
        "Executable utility scripts with clear usage instructions in header comments. "
        "Include error handling and helpful output messages. Empty dict {} if no scripts needed."
    )


# =============================================================================
# Step 2.2: Generate Content Sections (Chunked Generation Alternative)
# =============================================================================


class GenerateSkillSection(dspy.Signature):
    """Generate one section with consistent style and quality.

    Use for very large skills that exceed token limits when generated all at once.
    Maintain coherence with previous sections and overall skill plan.
    """

    # Inputs
    section_name: str = dspy.InputField(
        desc="Section name (e.g., 'Core Concepts', 'Advanced Patterns', 'Common Mistakes')"
    )
    section_topics: list[str] = dspy.InputField(
        desc="Specific topics to cover in this section (2-7 topics typical)"
    )
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata for context and naming")
    previous_sections: str = dspy.InputField(
        desc="Already generated sections for style consistency and avoiding repetition"
    )
    style_guide: str = dspy.InputField(
        desc="Style requirements: tone, depth, code example format, ❌/✅ usage"
    )

    # Outputs
    section_content: str = dspy.OutputField(
        desc="Complete markdown section content with header, paragraphs, code blocks, and examples. "
        "Include ❌/✅ contrasts where relevant. Min 100 words, max 1000 words. "
        "Use clear subheadings (###) for organization."
    )
    code_examples: list[str] = dspy.OutputField(
        desc="Standalone code examples from this section (copy-paste ready, include language tags)"
    )
    internal_links: list[str] = dspy.OutputField(
        desc="References to other sections or skills mentioned (format: 'section_name' or 'skill_name')"
    )


# =============================================================================
# Step 2.3: Incorporate User Feedback
# =============================================================================


class IncorporateFeedback(dspy.Signature):
    """Refine skill content based on user feedback from HITL review.

    Make targeted improvements while maintaining overall quality and structure.
    Address all feedback points systematically. If feedback conflicts with
    quality standards, explain why in unaddressed_feedback.
    """

    # Inputs
    current_content: str = dspy.InputField(desc="Current skill content")
    current_subdirectory_files: str = dspy.InputField(
        desc="Current subdirectory files as JSON: "
        "{'references': {...}, 'guides': {...}, 'templates': {...}, 'scripts': {...}}. "
        "Empty {} if no subdirectory files."
    )
    user_feedback: str = dspy.InputField(
        desc="User's feedback (free-form text or structured change requests)"
    )
    change_requests: str = dspy.InputField(
        desc="JSON structured change requests from AnalyzeFeedback"
    )
    skill_metadata: SkillMetadata = dspy.InputField(desc="Skill metadata for context")
    skill_style: SkillStyle = dspy.InputField(
        desc="Skill style: navigation_hub, comprehensive, or minimal"
    )

    # Outputs
    refined_content: str = dspy.OutputField(
        desc="Refined SKILL.md incorporating all addressable feedback. Maintain core principles, "
        "When to Use section, and ❌/✅ contrasts. Ensure changes improve quality score."
    )
    refined_reference_files: dict[str, str] = dspy.OutputField(
        desc="Updated references/ files. Only include files that changed. "
        "Empty dict {} if no changes to subdirectory references."
    )
    refined_guide_files: dict[str, str] = dspy.OutputField(
        desc="Updated guides/ files. Only include files that changed. "
        "Empty dict {} if no changes to guides."
    )
    refined_template_files: dict[str, str] = dspy.OutputField(
        desc="Updated templates/ files. Only include files that changed. "
        "Empty dict {} if no changes to templates."
    )
    refined_script_files: dict[str, str] = dspy.OutputField(
        desc="Updated scripts/ files. Only include files that changed. "
        "Empty dict {} if no changes to scripts."
    )
    changes_made: list[str] = dspy.OutputField(
        desc="Specific changes made (1-10 items). Format: 'Added X section', 'Fixed Y example', etc. "
        "Be concrete and actionable for user review."
    )
    unaddressed_feedback: list[str] = dspy.OutputField(
        desc="Feedback not addressed with clear explanation why. Format: 'Feedback: X - Reason: Y'. "
        "Empty list [] if all feedback addressed."
    )
    improvement_score: float = dspy.OutputField(
        desc="Self-assessment 0.0-1.0 of how much this revision improves the skill. "
        ">0.7 = significant improvement, >0.9 = major improvement. Consider: "
        "added missing sections, improved clarity, better examples, fixed errors."
    )


# =============================================================================
# Step 2.4: Generate Capability Implementations
# =============================================================================


# Target level for capability implementation
TargetLevel = Literal["beginner", "intermediate", "advanced", "expert"]


class GenerateCapabilityImplementation(dspy.Signature):
    """Generate production-ready implementation guide for one capability.

    Create detailed, actionable guidance with executable code examples,
    configuration options, and error handling. Match complexity to target level.
    """

    # Inputs
    capability: Capability = dspy.InputField(
        desc="Capability to implement (includes name, description, rationale)"
    )
    skill_context: str = dspy.InputField(
        desc="Overall skill context: metadata, related capabilities, dependencies"
    )
    target_level: TargetLevel = dspy.InputField(
        desc="Target audience level: beginner (step-by-step), intermediate (assumes basics), "
        "advanced (concise), expert (edge cases and optimizations)"
    )

    # Outputs
    implementation_guide: str = dspy.OutputField(
        desc="Complete markdown implementation guide (200-800 words). Include: overview, "
        "prerequisites, step-by-step instructions, code examples with language tags, "
        "expected outcomes. Match detail level to target_level."
    )
    code_snippets: list[str] = dspy.OutputField(
        desc="2-5 standalone, executable code snippets (copy-paste ready). Include comments, "
        "error handling, and clear variable names. Each snippet should be self-contained."
    )
    configuration: dict = dspy.OutputField(
        desc="Configuration options as dict: {option_name: effect_description}. "
        "Include default values and common variations. Empty dict {} if no configuration."
    )
    common_errors: list[str] = dspy.OutputField(
        desc="3-7 common errors users encounter. Format: 'Error: X - Solution: Y'. "
        "Include error messages/symptoms and concrete fixes. Prioritize by frequency."
    )
