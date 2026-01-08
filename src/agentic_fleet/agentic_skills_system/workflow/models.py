"""Pydantic models for DSPy workflow structured outputs.

These models provide type-safe interfaces for all workflow steps,
replacing JSON-string outputs with validated Pydantic models.
Follows agentskills.io specification for skill metadata.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Step 1: Understand - Task Analysis Models
# =============================================================================


class DependencyAnalysis(BaseModel):
    """Analysis of required skill dependencies."""

    missing_skills: list[str] = Field(
        default_factory=list, description="Skills required but not mounted"
    )
    optional_skills: list[str] = Field(
        default_factory=list, description="Skills that would enhance but aren't required"
    )
    integration_notes: str = Field(
        default="", description="Notes on how dependencies integrate"
    )


class ParentSkillInfo(BaseModel):
    """Information about a related skill in the taxonomy."""

    skill_id: str = Field(description="Path-style skill identifier")
    name: str = Field(description="Kebab-case skill name")
    relationship: Literal["parent", "sibling", "dependency"] = Field(
        description="Relationship to the new skill"
    )


class UnderstandingResult(BaseModel):
    """Result from the Understand step (Step 1)."""

    task_intent: str = Field(description="Core intent and requirements extracted from task")
    taxonomy_path: str = Field(
        description="Proposed taxonomy path (e.g., 'technical_skills/programming/languages/python')"
    )
    parent_skills: list[ParentSkillInfo] = Field(
        default_factory=list, description="Parent/sibling skills for context"
    )
    dependency_analysis: DependencyAnalysis = Field(
        default_factory=DependencyAnalysis, description="Analysis of required dependencies"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence in taxonomy placement"
    )


# =============================================================================
# Step 2: Plan - Skill Structure Models
# =============================================================================


class SkillMetadata(BaseModel):
    """Metadata for a skill following agentskills.io spec.

    All skills must have:
    - skill_id: Internal path-style identifier
    - name: Kebab-case name (1-64 chars, lowercase alphanumeric + hyphens)
    - description: 1-1024 character description
    """

    skill_id: str = Field(
        description="Path-style identifier (e.g., 'technical_skills/programming/languages/python')"
    )
    name: str = Field(
        max_length=64,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="Kebab-case name per agentskills.io spec",
    )
    description: str = Field(
        max_length=1024, description="What the skill does and when to use it"
    )
    version: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version",
    )
    type: Literal[
        "cognitive", "technical", "domain", "tool", "mcp", "specialization", "task_focus", "memory"
    ] = Field(description="Skill category")
    weight: Literal["lightweight", "medium", "heavyweight"] = Field(
        description="Resource intensity"
    )
    load_priority: Literal["always", "task_specific", "on_demand", "dormant"] = Field(
        default="task_specific", description="When to load the skill"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Required skill_ids"
    )
    capabilities: list[str] = Field(
        default_factory=list, description="Discrete capability names"
    )


class Capability(BaseModel):
    """A discrete, testable capability within a skill."""

    name: str = Field(description="Capability name (snake_case)")
    description: str = Field(description="What this capability provides")
    test_criteria: str = Field(
        default="", description="How to verify this capability works"
    )


class DependencyRef(BaseModel):
    """Reference to a dependency with justification."""

    skill_id: str = Field(description="Path-style skill identifier")
    justification: str = Field(description="Why this dependency is needed")
    required: bool = Field(default=True, description="Whether strictly required")


class ResourceRequirements(BaseModel):
    """External resources needed by a skill."""

    apis: list[str] = Field(default_factory=list, description="Required API endpoints")
    tools: list[str] = Field(default_factory=list, description="Required tools/CLIs")
    files: list[str] = Field(default_factory=list, description="Required files/configs")
    environment: list[str] = Field(
        default_factory=list, description="Required environment variables"
    )


class CompatibilityConstraints(BaseModel):
    """Compatibility and platform requirements."""

    python_version: str = Field(default=">=3.12", description="Python version requirement")
    platforms: list[str] = Field(
        default_factory=lambda: ["linux", "macos", "windows"],
        description="Supported platforms",
    )
    conflicts: list[str] = Field(
        default_factory=list, description="Conflicting skill_ids"
    )
    notes: str = Field(default="", description="Additional compatibility notes")


class PlanResult(BaseModel):
    """Result from the Plan step (Step 2)."""

    skill_metadata: SkillMetadata
    dependencies: list[DependencyRef] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    resource_requirements: ResourceRequirements = Field(default_factory=ResourceRequirements)
    compatibility_constraints: CompatibilityConstraints = Field(
        default_factory=CompatibilityConstraints
    )
    composition_strategy: str = Field(
        description="How this skill composes with other skills"
    )


# =============================================================================
# Step 3: Initialize - Skeleton Models
# =============================================================================


class FileSpec(BaseModel):
    """Specification for a file to create."""

    path: str = Field(description="Relative path from skill root")
    content_type: Literal["markdown", "json", "python", "yaml", "text"] = Field(
        default="text"
    )
    description: str = Field(default="", description="Purpose of this file")


class SkillSkeleton(BaseModel):
    """Directory and file structure for a skill."""

    root_path: str = Field(description="Path relative to skills root")
    files: list[FileSpec] = Field(default_factory=list, description="Files to create")
    directories: list[str] = Field(
        default_factory=lambda: ["capabilities/", "examples/", "tests/", "resources/"],
        description="Directories to create",
    )


class ValidationCheckItem(BaseModel):
    """A single validation check."""

    check: str = Field(description="What to validate")
    required: bool = Field(default=True, description="Whether this check is required")


class InitializeResult(BaseModel):
    """Result from the Initialize step (Step 3)."""

    skill_skeleton: SkillSkeleton
    validation_checklist: list[ValidationCheckItem] = Field(default_factory=list)


# =============================================================================
# Step 4: Edit - Content Generation Models
# =============================================================================


class UsageExample(BaseModel):
    """A runnable usage example."""

    title: str = Field(description="Example title")
    description: str = Field(description="What this example demonstrates")
    code: str = Field(description="Example code")
    expected_output: str = Field(default="", description="Expected result")
    language: str = Field(default="python", description="Programming language")


class BestPractice(BaseModel):
    """A best practice recommendation."""

    title: str = Field(description="Best practice title")
    description: str = Field(description="What to do and why")
    example: str = Field(default="", description="Example demonstrating the practice")


class CapabilityImplementation(BaseModel):
    """Documentation content for a capability."""

    name: str = Field(description="Capability name")
    content: str = Field(description="Markdown documentation content")


class EditResult(BaseModel):
    """Result from the Edit step (Step 4)."""

    skill_content: str = Field(
        description="Full SKILL.md markdown body content (frontmatter added automatically)"
    )
    capability_implementations: list[CapabilityImplementation] = Field(default_factory=list)
    usage_examples: list[UsageExample] = Field(default_factory=list)
    best_practices: list[BestPractice] = Field(default_factory=list)
    integration_guide: str = Field(default="", description="Integration notes and patterns")


# =============================================================================
# Step 5: Package - Validation Models
# =============================================================================


class ValidationReport(BaseModel):
    """Validation results for a skill package."""

    passed: bool = Field(description="Whether all required checks passed")
    status: Literal["passed", "failed", "warnings"] = Field(
        description="Overall validation status"
    )
    errors: list[str] = Field(default_factory=list, description="Critical errors")
    warnings: list[str] = Field(default_factory=list, description="Non-critical issues")
    checks_performed: list[str] = Field(
        default_factory=list, description="List of checks that were run"
    )


class TestCase(BaseModel):
    """An integration test case."""

    name: str = Field(description="Test name")
    description: str = Field(description="What this test verifies")
    input_data: str = Field(default="", description="Test input")
    expected_result: str = Field(default="", description="Expected outcome")


class PackagingManifest(BaseModel):
    """Manifest describing the packaged skill."""

    skill_id: str
    name: str
    version: str
    files: list[str] = Field(default_factory=list, description="Files included")
    checksum: str = Field(default="", description="Content checksum for verification")


class PackageResult(BaseModel):
    """Result from the Package step (Step 5)."""

    validation_report: ValidationReport
    integration_tests: list[TestCase] = Field(default_factory=list)
    packaging_manifest: PackagingManifest
    quality_score: float = Field(ge=0.0, le=1.0, description="Overall quality score")


# =============================================================================
# Step 6: Iterate - Feedback Models
# =============================================================================


class RevisionPlan(BaseModel):
    """Plan for revising a skill based on feedback."""

    changes: list[str] = Field(default_factory=list, description="Changes to make")
    priority: Literal["high", "medium", "low"] = Field(
        default="medium", description="Revision priority"
    )
    estimated_effort: Literal["quick", "medium", "extensive"] = Field(
        default="medium", description="Estimated effort level"
    )
    notes: str = Field(default="", description="Additional revision notes")


class EvolutionMetadata(BaseModel):
    """Skill evolution tracking metadata."""

    skill_id: str
    version: str
    status: Literal["approved", "needs_revision", "rejected"]
    timestamp: str = Field(description="ISO 8601 timestamp")
    previous_versions: list[str] = Field(default_factory=list)
    change_summary: str = Field(default="", description="Summary of changes in this version")


class IterateResult(BaseModel):
    """Result from the Iterate step (Step 6)."""

    approval_status: Literal["approved", "needs_revision", "rejected"]
    revision_plan: RevisionPlan | None = Field(
        default=None, description="Plan if needs_revision"
    )
    evolution_metadata: EvolutionMetadata
    next_steps: str = Field(description="Concrete next steps based on approval status")


# =============================================================================
# Composite Models for Full Workflow Results
# =============================================================================


class SkillCreationResult(BaseModel):
    """Complete result from the skill creation workflow (Steps 1-5)."""

    understanding: UnderstandingResult
    plan: PlanResult
    skeleton: InitializeResult
    content: EditResult
    package: PackageResult


class SkillRevisionResult(BaseModel):
    """Result from skill revision workflow (Steps 4-5)."""

    content: EditResult
    package: PackageResult


class QuickSkillResult(BaseModel):
    """Result from quick skill generation (Steps 1-2-4)."""

    understanding: UnderstandingResult
    plan: PlanResult
    content: EditResult
