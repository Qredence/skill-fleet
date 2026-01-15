"""Unified Pydantic models for skill-fleet.

Consolidated from workflow/models.py and core/config/models.py.
These models provide type-safe interfaces for all workflow steps,
HITL interactions, and configuration. Follows agentskills.io specification.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# HITL (Human-in-the-Loop) Models
# =============================================================================


class QuestionOption(BaseModel):
    """A single option for a multi-choice clarifying question."""

    id: str = Field(description="Option identifier (e.g., 'a', 'b', 'c')")
    label: str = Field(description="Short label for the option")
    description: str = Field(
        default="", description="Detailed description of what this option means"
    )


class ClarifyingQuestion(BaseModel):
    """A clarifying question to ask the user during skill creation."""

    id: str = Field(description="Unique question identifier")
    question: str = Field(description="The question text to display to the user")
    context: str = Field(default="", description="Why this question is being asked")
    options: list[QuestionOption] = Field(
        default_factory=list,
        description="Multi-choice options (if empty, expects free-form answer)",
    )
    allows_multiple: bool = Field(
        default=False, description="Whether multiple options can be selected"
    )
    required: bool = Field(default=True, description="Whether an answer is required")


class QuestionAnswer(BaseModel):
    """User's answer to a clarifying question."""

    question_id: str = Field(description="ID of the question being answered")
    selected_options: list[str] = Field(
        default_factory=list, description="IDs of selected options (for multi-choice)"
    )
    free_text: str = Field(default="", description="Free-form text answer")


class HITLRound(BaseModel):
    """A single round of HITL interaction."""

    round_number: int = Field(ge=1, le=4, description="Round number (1-4)")
    questions: list[ClarifyingQuestion] = Field(description="Questions asked in this round")
    answers: list[QuestionAnswer] = Field(
        default_factory=list, description="User's answers to the questions"
    )
    refinements_made: list[str] = Field(
        default_factory=list, description="List of refinements made based on answers"
    )


class HITLSession(BaseModel):
    """Complete HITL session tracking for skill creation."""

    min_rounds: int = Field(default=1, ge=1, description="Minimum required rounds")
    max_rounds: int = Field(default=4, le=4, description="Maximum allowed rounds")
    completed_rounds: list[HITLRound] = Field(
        default_factory=list, description="All completed HITL rounds"
    )
    is_complete: bool = Field(default=False, description="Whether HITL session is complete")
    final_approval: bool = Field(default=False, description="Whether user gave final approval")


# =============================================================================
# Step 0: Example Gathering - Understanding Before Creation
# =============================================================================


class UserExample(BaseModel):
    """A concrete example provided by the user showing desired skill behavior.

    Used in Step 0 to collect real-world usage patterns before skill creation.
    This ensures the skill is grounded in actual use cases, not assumptions.
    """

    input_description: str = Field(
        description="What the user provides or does (e.g., 'User asks to rotate an image 90 degrees')"
    )
    expected_output: str = Field(
        description="What should happen (e.g., 'Image is rotated clockwise, saved to same location')"
    )
    code_snippet: str = Field(
        default="", description="Optional code showing desired behavior or API usage"
    )
    trigger_phrase: str = Field(
        default="", description="What a user might say to invoke this (e.g., 'rotate this image')"
    )
    edge_case: bool = Field(
        default=False, description="Whether this is an edge case or corner scenario"
    )
    notes: str = Field(default="", description="Additional context or constraints from user")


class ExampleGatheringConfig(BaseModel):
    """Configuration for the example gathering process."""

    min_examples: int = Field(
        default=3, ge=1, le=10, description="Minimum examples required before proceeding"
    )
    readiness_threshold: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Readiness score threshold to proceed (0.8 = 80% confident)",
    )
    max_questions: int = Field(
        default=5, ge=1, le=10, description="Maximum clarifying questions per round"
    )
    max_rounds: int = Field(
        default=3, ge=1, le=5, description="Maximum rounds of Q&A before forcing proceed"
    )


class ExampleGatheringSession(BaseModel):
    """Session state for collecting examples from user before skill creation.

    This represents Step 0 of the workflow - understanding what the user
    actually wants through concrete examples before jumping to implementation.
    """

    task_description: str = Field(description="Original task description from user")
    config: ExampleGatheringConfig = Field(
        default_factory=ExampleGatheringConfig,
        description="Configuration for this gathering session",
    )
    questions_asked: list[ClarifyingQuestion] = Field(
        default_factory=list, description="All questions asked across all rounds"
    )
    user_responses: list[QuestionAnswer] = Field(
        default_factory=list, description="All user responses to questions"
    )
    collected_examples: list[UserExample] = Field(
        default_factory=list, description="Concrete examples gathered from user"
    )
    terminology: dict[str, str] = Field(
        default_factory=dict, description="Key terms and their definitions as understood from user"
    )
    refined_task: str = Field(
        default="", description="Task description refined based on gathered examples"
    )
    readiness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Score indicating if we have enough context to proceed",
    )
    is_ready: bool = Field(
        default=False, description="Whether enough examples collected to proceed"
    )
    current_round: int = Field(default=0, ge=0, description="Current Q&A round number")
    skip_reason: str = Field(default="", description="Reason if example gathering was skipped")


class ExampleGatheringResult(BaseModel):
    """Result from the example gathering step (Step 0)."""

    session: ExampleGatheringSession
    questions: list[ClarifyingQuestion] = Field(
        default_factory=list, description="Questions to ask in this round (empty if ready)"
    )
    proceed: bool = Field(default=False, description="Whether to proceed to skill creation")


# =============================================================================
# Phase 1: Understanding Models
# =============================================================================


class TaskIntent(BaseModel):
    """Structured analysis of user intent."""

    purpose: str = Field(description="Primary purpose of the skill")
    problem_statement: str = Field(description="What problem does it solve?")
    target_audience: str = Field(description="Who is the target user?")
    value_proposition: str = Field(description="What value does it provide?")


class DependencyRef(BaseModel):
    """Reference to a dependency with justification."""

    skill_id: str = Field(description="Path-style skill identifier")
    justification: str = Field(description="Why this dependency is needed")
    required: bool = Field(default=True, description="Whether strictly required")


class DependencyAnalysis(BaseModel):
    """Complete analysis of required skill dependencies.

    Merged from workflow (flat lists) and core (structured refs).
    """

    # From core (structured dependencies)
    required: list[DependencyRef] = Field(
        default_factory=list, description="Skills user must know first (hard prerequisites)"
    )
    recommended: list[DependencyRef] = Field(
        default_factory=list, description="Skills that complement this one (soft recommendations)"
    )
    conflicts: list[str] = Field(
        default_factory=list, description="Skills that might conflict with this one"
    )
    # From workflow (flat lists for backward compatibility)
    missing_skills: list[str] = Field(
        default_factory=list, description="Skills required but not mounted"
    )
    optional_skills: list[str] = Field(
        default_factory=list, description="Skills that would enhance but aren't required"
    )
    integration_notes: str = Field(default="", description="Notes on how dependencies integrate")


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
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in taxonomy placement")


# =============================================================================
# Step 2: Plan - Skill Structure Models
# =============================================================================


class SkillMetadata(BaseModel):
    """Metadata for a skill following agentskills.io spec.

    All skills must have:
    - skill_id: Internal path-style identifier
    - name: Kebab-case name (1-64 chars, lowercase alphanumeric + hyphens)
    - description: 1-1024 character description

    For scalable discovery (500+ skills):
    - category: Hierarchical category path for domain grouping
    - keywords: Search keywords for discovery
    - scope: What the skill does AND doesn't cover (for differentiation)
    - see_also: Related skills for cross-referencing
    """

    skill_id: str = Field(
        description="Path-style identifier (e.g., 'technical_skills/programming/languages/python')"
    )
    name: str = Field(
        max_length=64,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        description="Kebab-case name per agentskills.io spec",
    )
    description: str = Field(max_length=1024, description="What the skill does and when to use it")
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
    dependencies: list[str] = Field(default_factory=list, description="Required skill_ids")
    capabilities: list[str] = Field(default_factory=list, description="Discrete capability names")

    # Scalable discovery fields
    category: str = Field(
        default="", description="Hierarchical category path (e.g., 'tools/web' or 'memory_blocks')"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Search keywords for discovery (e.g., ['playwright', 'browser', 'testing', 'ui', 'e2e'])",
    )
    scope: str = Field(
        default="",
        description="What this skill covers AND doesn't cover for differentiation from similar skills",
    )
    see_also: list[str] = Field(
        default_factory=list,
        description="Related skill_ids for cross-referencing (e.g., ['tools/puppeteer-testing'])",
    )
    # From core version
    tags: list[str] = Field(default_factory=list, description="Search tags for discovery")
    taxonomy_path: str = Field(default="", description="Full path in taxonomy")


class Capability(BaseModel):
    """A discrete, testable capability within a skill."""

    name: str = Field(description="Capability name (snake_case)")
    description: str = Field(description="What this capability provides")
    test_criteria: str = Field(default="", description="How to verify this capability works")


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
    conflicts: list[str] = Field(default_factory=list, description="Conflicting skill_ids")
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
    composition_strategy: str = Field(description="How this skill composes with other skills")


# =============================================================================
# Step 3: Initialize - Skeleton Models
# =============================================================================


class FileSpec(BaseModel):
    """Specification for a file to create."""

    path: str = Field(description="Relative path from skill root")
    content_type: Literal["markdown", "json", "python", "yaml", "text"] = Field(default="text")
    description: str = Field(default="", description="Purpose of this file")


class SkillSkeleton(BaseModel):
    """Directory and file structure for a skill.

    Standard skill directory structure:
    skill-name/
    ├── SKILL.md                    # Main skill documentation
    ├── metadata.json               # Extended metadata
    ├── capabilities/               # Capability implementations
    │   └── README.md
    ├── examples/                   # Usage examples
    │   └── README.md
    ├── tests/                      # Integration tests
    │   └── README.md
    ├── resources/                  # Resource files
    │   └── README.md
    ├── references/                 # Reference documentation
    │   ├── README.md
    │   ├── quick-start.md
    │   ├── common-patterns.md
    │   ├── api-reference.md
    │   └── troubleshooting.md
    ├── scripts/                    # Utility scripts
    │   └── README.md
    └── assets/                     # Static assets
        └── README.md
    """

    root_path: str = Field(description="Path relative to skills root")
    files: list[FileSpec] = Field(default_factory=list, description="Files to create")
    directories: list[str] = Field(
        default_factory=lambda: [
            "capabilities/",
            "examples/",
            "tests/",
            "resources/",
            "references/",
            "scripts/",
            "assets/",
        ],
        description="Directories to create following agentskills.io standard structure",
    )


class ValidationCheckItem(BaseModel):
    """A single validation check result.

    Merged from workflow (simple) and core (detailed).
    """

    id: str = Field(default="", description="Unique check identifier")
    check: str = Field(description="Description of what was validated")
    passed: bool = Field(default=True, description="Whether the check passed")
    message: str = Field(default="", description="Validation message or error")
    severity: Literal["critical", "warning", "info"] = Field(default="info")
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
    """Validation results for a skill package.

    Merged from workflow (status-based) and core (score-based).
    """

    passed: bool = Field(description="Whether all required checks passed")
    status: Literal["passed", "failed", "warnings"] = Field(
        default="passed", description="Overall validation status"
    )
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall quality score")
    errors: list[str] = Field(default_factory=list, description="Critical errors")
    warnings: list[str] = Field(default_factory=list, description="Non-critical issues")
    checks_performed: list[str] = Field(
        default_factory=list, description="List of checks that were run"
    )
    checks: list[ValidationCheckItem] = Field(default_factory=list, description="Detailed checks")
    feedback: str = Field(default="", description="Consolidated feedback for refinement")


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
    revision_plan: RevisionPlan | None = Field(default=None, description="Plan if needs_revision")
    evolution_metadata: EvolutionMetadata
    next_steps: str = Field(description="Concrete next steps based on approval status")


# =============================================================================
# Composite Models for Full Workflow Results
# =============================================================================


class SkillCreationResult(BaseModel):
    """Complete result from the skill creation workflow.

    Merged from workflow (step-based) and core (status-based).
    Supports both the legacy step results and new status-based results.
    """

    # Core version fields (status-based)
    status: str = Field(
        default="completed",
        description="Status: 'completed', 'failed', 'cancelled', 'pending_review'",
    )
    skill_content: str | None = Field(default=None, description="Generated SKILL.md content")
    metadata: SkillMetadata | None = Field(default=None, description="Skill metadata")
    validation_report: ValidationReport | None = Field(default=None)
    quality_assessment: dict | None = Field(
        default=None, description="Quality assessment from Phase 3 validation"
    )
    error: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Extra files for subdirectory content (from Phase 2 generation)
    extra_files: dict | None = Field(
        default=None,
        description="Additional files for skill subdirectories: usage_examples, best_practices, "
        "test_cases, capability_implementations, scripts, assets, etc.",
    )

    # Workflow version fields (step-based, optional for backward compatibility)
    understanding: UnderstandingResult | None = Field(default=None)
    plan: PlanResult | None = Field(default=None)
    skeleton: InitializeResult | None = Field(default=None)
    content: EditResult | None = Field(default=None)
    package: PackageResult | None = Field(default=None)


class SkillRevisionResult(BaseModel):
    """Result from skill revision workflow (Steps 4-5)."""

    content: EditResult
    package: PackageResult


class QuickSkillResult(BaseModel):
    """Result from quick skill generation (Steps 1-2-4)."""

    understanding: UnderstandingResult
    plan: PlanResult
    content: EditResult


# =============================================================================
# Conversational Agent Models
# =============================================================================


class ChecklistState(BaseModel):
    """Tracks TDD checklist completion state for writing-skills TDD enforcement.

    This model enforces the mandatory TDD checklist from writing-skills skill.
    All phases must be complete before saving any skill.
    """

    # RED Phase - Write Failing Test
    red_scenarios_created: bool = Field(
        default=False,
        description="Pressure scenarios created (3+ combined pressures for discipline skills)",
    )
    baseline_tests_run: bool = Field(
        default=False, description="Baseline tests run WITHOUT skill present"
    )
    baseline_behavior_documented: bool = Field(
        default=False, description="Baseline behavior documented verbatim"
    )
    rationalization_patterns_identified: bool = Field(
        default=False, description="Patterns in rationalizations/failures identified"
    )

    # GREEN Phase - Verify Skill Works
    green_tests_run: bool = Field(default=False, description="Tests run WITH skill present")
    compliance_verified: bool = Field(
        default=False, description="Agents now comply with skill verified"
    )
    baseline_failures_addressed: bool = Field(
        default=False, description="Skill addresses specific baseline failures"
    )

    # REFACTOR Phase - Close Loopholes
    new_rationalizations_identified: bool = Field(
        default=False, description="NEW rationalizations from testing identified"
    )
    explicit_counters_added: bool = Field(
        default=False, description="Explicit counters added to skill (if discipline skill)"
    )
    retested_until_bulletproof: bool = Field(
        default=False, description="Re-tested until bulletproof against rationalizations"
    )
    rationalization_table_built: bool = Field(
        default=False, description="Rationalization table built from all test iterations"
    )

    # Quality Checks
    flowchart_present: bool = Field(
        default=False, description="Flowchart present (optional, only if decision non-obvious)"
    )
    quick_reference_included: bool = Field(
        default=False, description="Quick reference table included"
    )
    common_mistakes_included: bool = Field(
        default=False, description="Common mistakes section included"
    )
    no_narrative_storytelling: bool = Field(
        default=False, description="No narrative storytelling (checked and confirmed)"
    )
    supporting_files_appropriate: bool = Field(
        default=False,
        description="Supporting files only for tools or heavy reference (checked and confirmed)",
    )

    def is_complete(self) -> bool:
        """Check if all required items are complete.

        Returns:
            True if all mandatory checklist items are complete, False otherwise.
            flowchart_present is optional (only required if decision is non-obvious).
        """
        # All RED items required
        red_complete = (
            self.red_scenarios_created
            and self.baseline_tests_run
            and self.baseline_behavior_documented
            and self.rationalization_patterns_identified
        )

        # All GREEN items required
        green_complete = (
            self.green_tests_run and self.compliance_verified and self.baseline_failures_addressed
        )

        # All REFACTOR items required
        refactor_complete = (
            self.new_rationalizations_identified
            and self.explicit_counters_added
            and self.retested_until_bulletproof
            and self.rationalization_table_built
        )

        # All quality checks required (flowchart_present is optional)
        quality_complete = (
            self.quick_reference_included
            and self.common_mistakes_included
            and self.no_narrative_storytelling
            and self.supporting_files_appropriate
        )

        return red_complete and green_complete and refactor_complete and quality_complete

    def get_missing_items(self) -> list[str]:
        """Get list of incomplete checklist items.

        Returns:
            List of missing item descriptions for user presentation.
        """
        missing = []

        # RED Phase
        if not self.red_scenarios_created:
            missing.append("RED: Create pressure scenarios")
        if not self.baseline_tests_run:
            missing.append("RED: Run baseline tests without skill")
        if not self.baseline_behavior_documented:
            missing.append("RED: Document baseline behavior verbatim")
        if not self.rationalization_patterns_identified:
            missing.append("RED: Identify rationalization patterns")

        # GREEN Phase
        if not self.green_tests_run:
            missing.append("GREEN: Run tests with skill")
        if not self.compliance_verified:
            missing.append("GREEN: Verify agents comply with skill")
        if not self.baseline_failures_addressed:
            missing.append("GREEN: Verify skill addresses baseline failures")

        # REFACTOR Phase
        if not self.new_rationalizations_identified:
            missing.append("REFACTOR: Identify new rationalizations")
        if not self.explicit_counters_added:
            missing.append("REFACTOR: Add explicit counters (if discipline skill)")
        if not self.retested_until_bulletproof:
            missing.append("REFACTOR: Re-test until bulletproof")
        if not self.rationalization_table_built:
            missing.append("REFACTOR: Build rationalization table")

        # Quality Checks
        if not self.quick_reference_included:
            missing.append("Quality: Include quick reference table")
        if not self.common_mistakes_included:
            missing.append("Quality: Include common mistakes section")
        if not self.no_narrative_storytelling:
            missing.append("Quality: Remove narrative storytelling")
        if not self.supporting_files_appropriate:
            missing.append("Quality: Ensure supporting files appropriate")

        return missing
