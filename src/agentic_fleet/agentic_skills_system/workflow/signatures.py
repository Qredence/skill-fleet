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

from .models import (
    BestPractice,
    Capability,
    CapabilityImplementation,
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
    ValidationCheckItem,
    ValidationReport,
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
# Legacy Signatures (String-based, for backward compatibility)
# =============================================================================
# These can be removed once all modules are updated to use typed signatures


class UnderstandTaskForSkillLegacy(dspy.Signature):
    """Legacy signature with string outputs for backward compatibility."""

    task_description: str = dspy.InputField(desc="User task or capability requirement")
    existing_skills: str = dspy.InputField(desc="JSON list of currently mounted skill_ids")
    taxonomy_structure: str = dspy.InputField(
        desc="JSON object with relevant portions of the hierarchical taxonomy"
    )

    task_intent: str = dspy.OutputField(desc="Core intent and requirements extracted from task")
    taxonomy_path: str = dspy.OutputField(
        desc="Proposed taxonomy path (e.g., 'technical_skills/programming/languages/python')"
    )
    parent_skills: str = dspy.OutputField(
        desc="JSON list of parent/sibling skills in taxonomy for context"
    )
    dependency_analysis: str = dspy.OutputField(
        desc="JSON object analyzing required dependency skills not yet mounted"
    )
    confidence_score: float = dspy.OutputField(desc="Confidence in taxonomy placement (0.0-1.0)")


class PlanSkillStructureLegacy(dspy.Signature):
    """Legacy signature with string outputs for backward compatibility."""

    task_intent: str = dspy.InputField()
    taxonomy_path: str = dspy.InputField()
    parent_skills: str = dspy.InputField()
    dependency_analysis: str = dspy.InputField()

    skill_metadata: str = dspy.OutputField(
        desc="""JSON metadata with required fields:
        - skill_id: taxonomy path (e.g., 'technical_skills/programming/languages/python/decorators')
        - name: kebab-case name for agentskills.io (e.g., 'python-decorators'), max 64 chars, lowercase
        - description: 1-2 sentence description (max 1024 chars) of what skill does and when to use it
        - version: semver format '1.0.0'
        - type: one of 'cognitive|technical|domain|tool|mcp|specialization|task_focus|memory'
        - weight: one of 'lightweight|medium|heavyweight'
        - load_priority: one of 'always|task_specific|on_demand|dormant'
        - dependencies: list of skill_ids
        - capabilities: list of capability names"""
    )
    dependencies: str = dspy.OutputField(
        desc="JSON array of dependency skill_ids with justification for each"
    )
    capabilities: str = dspy.OutputField(desc="JSON array of discrete, testable capabilities")
    resource_requirements: str = dspy.OutputField(
        desc="JSON object of external resources (APIs, tools, files) needed"
    )
    compatibility_constraints: str = dspy.OutputField(
        desc="JSON object with constraints, conflicts, platform requirements"
    )
    composition_strategy: str = dspy.OutputField(desc="How this skill composes with other skills")
