"""DSPy signatures for the agentic skills creation workflow.

These signatures define the input/output contracts for each workflow step.
Where possible, we use Pydantic models for type-safe, validated outputs.

Approved LLM Models:
- gemini-3-flash-preview: Primary model for all steps
- gemini-3-pro-preview: For GEPA reflection
- deepseek-v3.2: Cost-effective alternative
- Nemotron-3-Nano-30B-A3B: Lightweight operations
"""

from __future__ import annotations

from typing import Literal

import dspy

from ...models import (
    BestPractice,
    Capability,
    CapabilityImplementation,
    ClarifyingQuestion,
    CompatibilityConstraints,
    DependencyAnalysis,
    DependencyRef,
    EvolutionMetadata,
    PackagingManifest,
    ParentSkillInfo,
    ResourceRequirements,
    RevisionPlan,
    SkillMetadata,
    SkillSkeleton,
    TestCase,
    UsageExample,
    UserExample,
    ValidationCheckItem,
    ValidationReport,
)

# =============================================================================
# Step 0: Gather Examples - Understanding Before Creation
# =============================================================================


class GatherExamplesForSkill(dspy.Signature):
    """Gather concrete usage examples from the user before skill creation.

    This step runs BEFORE UnderstandTaskForSkill to ensure we build skills
    grounded in real use cases, not assumptions. Skip only when usage
    patterns are already clearly understood.

    Key questions to explore:
    - "What functionality should this skill support?"
    - "Can you give examples of how this skill would be used?"
    - "What would a user say that should trigger this skill?"
    - "What are the edge cases or limitations?"

    Conclude when readiness_score >= threshold (default 0.8) and
    at least min_examples (default 3) concrete examples are collected.
    """

    # Inputs
    task_description: str = dspy.InputField(desc="Initial task description from user")
    user_responses: str = dspy.InputField(
        desc="JSON list of user responses to previous clarifying questions (empty [] on first call)"
    )
    collected_examples: str = dspy.InputField(
        desc="JSON list of UserExample objects collected so far (empty [] on first call)"
    )
    config: str = dspy.InputField(
        desc="JSON ExampleGatheringConfig with min_examples, readiness_threshold, max_questions"
    )

    # Outputs
    clarifying_questions: list[ClarifyingQuestion] = dspy.OutputField(
        desc="1-3 focused questions to ask the user (fewer is better). Empty list if ready to proceed."
    )
    new_examples: list[UserExample] = dspy.OutputField(
        desc="New examples extracted from user responses (add to collected_examples)"
    )
    terminology_updates: dict[str, str] = dspy.OutputField(
        desc="Key terms and definitions learned from this round"
    )
    refined_task: str = dspy.OutputField(
        desc="Updated task description incorporating insights from examples"
    )
    readiness_score: float = dspy.OutputField(
        desc="0.0-1.0 score. >= threshold means ready to proceed. Based on example coverage, clarity, and edge cases."
    )
    readiness_reasoning: str = dspy.OutputField(
        desc="Brief explanation of readiness score (why ready or what's missing)"
    )


# =============================================================================
# Step 1: Understand - Task Analysis
# =============================================================================


class UnderstandTaskForSkill(dspy.Signature):
    """Extract task requirements and map to a taxonomy position.

    Analyzes the user's task description and determines:
    - Core intent and requirements
    - Best taxonomy path for the skill
    - Related skills in the taxonomy
    - Missing dependencies
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User task or capability requirement to create a skill for"
    )
    existing_skills: str = dspy.InputField(desc="JSON list of currently mounted skill_ids")
    taxonomy_structure: str = dspy.InputField(
        desc="JSON object with relevant portions of the hierarchical taxonomy"
    )

    # Outputs - mix of typed and string for flexibility
    task_intent: str = dspy.OutputField(
        desc="Core intent and requirements extracted from task (1-3 sentences)"
    )
    taxonomy_path: str = dspy.OutputField(
        desc="Proposed taxonomy path using forward slashes (e.g., 'technical_skills/programming/languages/python')"
    )
    parent_skills: list[ParentSkillInfo] = dspy.OutputField(
        desc="List of related parent/sibling skills in taxonomy for context"
    )
    dependency_analysis: DependencyAnalysis = dspy.OutputField(
        desc="Analysis of required dependency skills not yet mounted"
    )
    confidence_score: float = dspy.OutputField(desc="Confidence in taxonomy placement (0.0-1.0)")


# =============================================================================
# Step 2: Plan - Skill Structure Design
# =============================================================================


class PlanSkillStructure(dspy.Signature):
    """Design skill structure with taxonomy integration and agentskills.io compliance.

    Creates the complete metadata and structure for a new skill, ensuring:
    - Valid agentskills.io kebab-case name
    - Proper dependency declarations
    - Well-defined capabilities
    """

    # Inputs
    task_intent: str = dspy.InputField(desc="Core intent from understand step")
    taxonomy_path: str = dspy.InputField(desc="Proposed taxonomy path")
    parent_skills: str = dspy.InputField(desc="JSON list of related skills")
    dependency_analysis: str = dspy.InputField(desc="JSON dependency analysis")

    # Outputs - typed for validation
    skill_metadata: SkillMetadata = dspy.OutputField(
        desc="Complete skill metadata following agentskills.io spec"
    )
    dependencies: list[DependencyRef] = dspy.OutputField(
        desc="List of dependency skill_ids with justification"
    )
    capabilities: list[Capability] = dspy.OutputField(
        desc="List of discrete, testable capabilities (3-7 recommended)"
    )
    resource_requirements: ResourceRequirements = dspy.OutputField(
        desc="External resources (APIs, tools, files) needed"
    )
    compatibility_constraints: CompatibilityConstraints = dspy.OutputField(
        desc="Platform requirements and conflicts"
    )
    composition_strategy: str = dspy.OutputField(
        desc="How this skill composes with other skills (1-2 paragraphs)"
    )


# =============================================================================
# Step 3: Initialize - Skeleton Creation
# =============================================================================


class InitializeSkillSkeleton(dspy.Signature):
    """Create a skill skeleton matching taxonomy standards.

    Generates the directory structure and file list for the skill,
    following the standard layout:
    - metadata.json
    - SKILL.md
    - capabilities/
    - examples/
    - tests/
    - resources/
    """

    # Inputs
    skill_metadata: str = dspy.InputField(desc="JSON skill metadata")
    capabilities: str = dspy.InputField(desc="JSON array of capabilities")
    taxonomy_path: str = dspy.InputField(desc="Taxonomy path for the skill")

    # Outputs - typed
    skill_skeleton: SkillSkeleton = dspy.OutputField(
        desc="Directory and file structure for the skill"
    )
    validation_checklist: list[ValidationCheckItem] = dspy.OutputField(
        desc="List of validation checks to perform"
    )


# =============================================================================
# Step 4: Edit - Content Generation
# =============================================================================


class EditSkillContent(dspy.Signature):
    """Generate comprehensive skill content with composition support.

    Creates the main SKILL.md content and supporting documentation.
    Note: YAML frontmatter will be added automatically during registration.

    The skill_content MUST include these sections:
    - # Title (skill name as heading)
    - ## Overview (what the skill does)
    - ## Capabilities (list of discrete capabilities)
    - ## Dependencies (required skills or 'No dependencies')
    - ## Usage Examples (code examples with expected output)
    """

    # Inputs
    skill_skeleton: str = dspy.InputField(desc="JSON skill skeleton structure")
    parent_skills: str = dspy.InputField(
        desc="Content/metadata from parent/sibling skills for context"
    )
    composition_strategy: str = dspy.InputField(desc="How this skill composes with others")
    revision_feedback: str = dspy.InputField(
        default="",
        desc="User feedback from previous revision to incorporate (empty if initial generation)",
    )

    # Outputs - skill_content stays as string for long-form markdown
    skill_content: str = dspy.OutputField(
        desc="""Full SKILL.md markdown body content (frontmatter added automatically).
        Must include: # Title, ## Overview, ## Capabilities, ## Dependencies, ## Usage Examples.
        Include code blocks with syntax highlighting (```python, ```bash, etc.)."""
    )
    capability_implementations: list[CapabilityImplementation] = dspy.OutputField(
        desc="Documentation content for each capability"
    )
    usage_examples: list[UsageExample] = dspy.OutputField(
        desc="Runnable usage examples with code and expected output"
    )
    best_practices: list[BestPractice] = dspy.OutputField(
        desc="Best practice recommendations (3-5 items)"
    )
    integration_guide: str = dspy.OutputField(
        desc="Integration notes and composition patterns (1-2 paragraphs)"
    )


# =============================================================================
# Step 5: Package - Validation & Packaging
# =============================================================================


class PackageSkillForApproval(dspy.Signature):
    """Validate and prepare a skill for approval.

    Performs comprehensive validation and generates:
    - Validation report with errors/warnings
    - Integration test cases
    - Packaging manifest
    - Quality score
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Generated SKILL.md content")
    skill_metadata: str = dspy.InputField(desc="JSON skill metadata")
    taxonomy_path: str = dspy.InputField(desc="Taxonomy path")
    capability_implementations: str = dspy.InputField(desc="JSON capability documentation")

    # Outputs - typed for structured validation
    validation_report: ValidationReport = dspy.OutputField(
        desc="Validation results with pass/fail, errors, and warnings"
    )
    integration_tests: list[TestCase] = dspy.OutputField(
        desc="Test cases to verify skill functionality"
    )
    packaging_manifest: PackagingManifest = dspy.OutputField(
        desc="Manifest describing the packaged skill"
    )
    quality_score: float = dspy.OutputField(desc="Overall quality score (0.0-1.0)")


# =============================================================================
# Step 6: Iterate - Feedback & Evolution
# =============================================================================


class IterateSkillWithFeedback(dspy.Signature):
    """Manage HITL approval and skill evolution tracking.

    Processes human feedback to determine:
    - Approval status (approved, needs_revision, rejected)
    - Revision plan if changes needed
    - Evolution metadata for tracking
    """

    # Inputs
    packaged_skill: str = dspy.InputField(desc="JSON packaging manifest")
    validation_report: str = dspy.InputField(desc="JSON validation report")
    human_feedback: str = dspy.InputField(desc="Human reviewer feedback")
    usage_analytics: str = dspy.InputField(desc="JSON usage analytics (if available)")

    # Outputs - typed for structured decisions
    approval_status: Literal["approved", "needs_revision", "rejected"] = dspy.OutputField(
        desc="Final approval decision"
    )
    revision_plan: RevisionPlan = dspy.OutputField(
        desc="Plan for revisions if status is needs_revision"
    )
    evolution_metadata: EvolutionMetadata = dspy.OutputField(
        desc="Metadata tracking skill evolution"
    )
    next_steps: str = dspy.OutputField(
        desc="Concrete next steps based on approval status (1-3 bullet points)"
    )


# =============================================================================
# Dynamic Question Generation for Feedback
# =============================================================================


class GenerateDynamicFeedbackQuestions(dspy.Signature):
    """Generate contextual, domain-aware questions for skill feedback.

    Instead of using static template questions, this signature uses the LLM
    to generate dynamic questions that are:
    - Domain-aware (incorporating specific terminology from the task)
    - Contextual (referencing specific capabilities and content)
    - Task-specific (tailored to what the user actually requested)

    This replaces the hardcoded template questions in InteractiveFeedbackHandler.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's original task description - what they want to create"
    )
    skill_metadata: str = dspy.InputField(
        desc="JSON skill metadata including name, description, capabilities, type"
    )
    skill_content: str = dspy.InputField(
        desc="Generated SKILL.md content (first 500 chars for context)"
    )
    validation_report: str = dspy.InputField(
        desc="JSON validation report with errors, warnings, quality score"
    )
    round_number: int = dspy.InputField(
        desc="Current feedback round (1=alignment check, 2=quality, 3+=refinement)"
    )
    previous_feedback: str = dspy.InputField(
        desc="Previous feedback and responses (empty for round 1)", default=""
    )

    # Outputs - JSON formatted for compatibility with InteractiveFeedbackHandler
    questions_json: str = dspy.OutputField(
        desc="""JSON array of question objects. Each object must have:
        - "id": unique identifier (e.g., "scope_alignment", "capability_completeness")
        - "question": the actual question text (domain-specific, task-specific)
        - "context": explanation of why this question matters
        - "options": array of option objects with "id", "label", "description"

        Format: [{"id": "...", "question": "...", "context": "...", "options": [...]}]

        Requirements:
        - Round 1: Focus on scope alignment, capability completeness, dependencies
        - Round 2: Focus on content quality, examples, clarity
        - Round 3+: Focus on refinements, edge cases, improvements
        - Use domain-specific terminology from the task
        - Reference specific capabilities by name when relevant
        - Each question should have 2-4 options covering key concerns
        """
    )
