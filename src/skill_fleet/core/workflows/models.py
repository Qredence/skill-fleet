"""
Typed models for skill creation workflow phases.

Defines explicit contracts between workflow phases to replace implicit dict structures.
These models provide type safety, validation, and clear documentation of data flow.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# =============================================================================
# Quality Configuration (Centralized)
# =============================================================================


class QualityThresholds(BaseModel):
    """
    Centralized quality thresholds for skill creation.

    All quality-related thresholds should be defined here to avoid
    scattered magic numbers throughout the codebase.
    """

    # Validation thresholds
    validation_pass_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum quality score to pass validation",
    )

    # Refinement thresholds
    refinement_target_quality: float = Field(
        default=0.80,
        ge=0.0,
        le=1.0,
        description="Target quality score for content refinement",
    )
    refinement_max_iterations: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum refinement iterations",
    )

    # Taxonomy confidence
    taxonomy_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence for taxonomy path recommendation",
    )

    # Test case thresholds
    trigger_coverage_target: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
        description="Target trigger phrase coverage in test cases",
    )

    # Content size thresholds
    optimal_word_count_min: int = Field(
        default=500,
        ge=100,
        description="Minimum word count for optimal skill size",
    )
    optimal_word_count_max: int = Field(
        default=3000,
        ge=500,
        description="Maximum word count for optimal skill size",
    )
    acceptable_word_count_max: int = Field(
        default=5000,
        ge=1000,
        description="Maximum word count before size warning",
    )

    # Verbosity thresholds
    verbosity_warning_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Verbosity score above which to warn (0=concise, 1=verbose)",
    )


# Global default thresholds instance
DEFAULT_QUALITY_THRESHOLDS = QualityThresholds()


# =============================================================================
# Module Output Models (Granular)
# =============================================================================


class RequirementsOutput(BaseModel):
    """Output from GatherRequirementsModule."""

    domain: Literal["technical", "cognitive", "domain_knowledge", "tool", "meta"] = Field(
        default="technical",
        description="Primary domain category",
    )
    category: str = Field(
        default="general",
        description="Specific category within domain (kebab-case)",
    )
    target_level: Literal["beginner", "intermediate", "advanced", "expert"] = Field(
        default="intermediate",
        description="Target expertise level",
    )
    topics: list[str] = Field(
        default_factory=list,
        description="3-7 specific topics covered",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Technical constraints or limitations",
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Items needing clarification (triggers HITL if non-empty)",
    )
    suggested_skill_name: str = Field(
        default="",
        description="Suggested kebab-case skill name",
    )
    trigger_phrases: list[str] = Field(
        default_factory=list,
        description="5-7 natural language trigger phrases",
    )
    negative_triggers: list[str] = Field(
        default_factory=list,
        description="Contexts where skill should NOT trigger",
    )
    skill_category: Literal[
        "document_creation", "workflow_automation", "mcp_enhancement", "analysis", "other"
    ] = Field(
        default="other",
        description="Skill behavior category",
    )
    requires_mcp: bool = Field(
        default=False,
        description="Whether skill requires MCP server",
    )
    suggested_mcp_server: str = Field(
        default="",
        description="Suggested MCP server if requires_mcp is True",
    )
    reasoning: str = Field(
        default="",
        description="LLM reasoning for requirements analysis",
    )

    def has_ambiguities(self) -> bool:
        """Check if clarification is needed."""
        return len(self.ambiguities) > 0


class IntentOutput(BaseModel):
    """Output from AnalyzeIntentModule."""

    purpose: str = Field(
        default="",
        description="Primary purpose of the skill",
    )
    problem_statement: str = Field(
        default="",
        description="Specific problem the skill addresses",
    )
    target_audience: str = Field(
        default="Developers",
        description="Target user persona",
    )
    value_proposition: str = Field(
        default="",
        description="Unique value provided",
    )
    skill_type: Literal[
        "how_to", "reference", "concept", "workflow", "checklist", "troubleshooting"
    ] = Field(
        default="how_to",
        description="Type of skill content",
    )
    scope: str = Field(
        default="",
        description="Skill boundaries (what it does and doesn't cover)",
    )
    success_criteria: list[str] = Field(
        default_factory=list,
        description="Measurable success criteria",
    )
    reasoning: str = Field(
        default="",
        description="LLM reasoning for intent analysis",
    )


class TaxonomyOutput(BaseModel):
    """Output from FindTaxonomyPathModule."""

    recommended_path: str = Field(
        default="general/uncategorized",
        description="Recommended taxonomy path (e.g., 'technical/frontend/react')",
    )
    alternative_paths: list[str] = Field(
        default_factory=list,
        description="Alternative valid paths",
    )
    path_rationale: str = Field(
        default="",
        description="Explanation for path recommendation",
    )
    new_directories: list[str] = Field(
        default_factory=list,
        description="New directories that would need to be created",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for recommendation",
    )
    reasoning: str = Field(
        default="",
        description="LLM reasoning for taxonomy analysis",
    )
    fallback: bool = Field(
        default=False,
        description="Whether this is a fallback result due to analysis failure",
    )


class DependencyOutput(BaseModel):
    """Output from AnalyzeDependenciesModule."""

    prerequisite_skills: list[str] = Field(
        default_factory=list,
        description="Skills that must be learned first (hard dependencies)",
    )
    complementary_skills: list[str] = Field(
        default_factory=list,
        description="Skills that enhance but aren't required",
    )
    conflicting_skills: list[str] = Field(
        default_factory=list,
        description="Skills that may conflict with this one",
    )
    missing_prerequisites: list[str] = Field(
        default_factory=list,
        description="Required skills not currently available",
    )
    dependency_rationale: str = Field(
        default="",
        description="Explanation for dependency analysis",
    )
    reasoning: str = Field(
        default="",
        description="LLM reasoning for dependency analysis",
    )


class PlanOutput(BaseModel):
    """Output from SynthesizePlanModule."""

    skill_name: str = Field(
        description="Final kebab-case skill name",
    )
    skill_description: str = Field(
        description="Skill description (max 1024 chars)",
    )
    taxonomy_path: str = Field(
        description="Final taxonomy path",
    )
    content_outline: list[str] = Field(
        default_factory=list,
        description="Ordered list of sections for SKILL.md",
    )
    generation_guidance: str = Field(
        default="",
        description="Specific guidance for content generation",
    )
    success_criteria: list[str] = Field(
        default_factory=list,
        description="Success criteria from intent analysis",
    )
    estimated_length: str = Field(
        default="medium",
        description="Estimated skill length (short/medium/long)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Search tags for discovery",
    )
    rationale: str = Field(
        default="",
        description="Rationale for plan decisions",
    )
    reasoning: str = Field(
        default="",
        description="LLM reasoning for plan synthesis",
    )

    # Metadata for skill.json
    skill_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for skill.json",
    )


class StructureValidationOutput(BaseModel):
    """Output from ValidateStructureModule."""

    valid: bool = Field(
        description="Whether structure passed validation",
    )
    name_errors: list[str] = Field(
        default_factory=list,
        description="Skill naming errors",
    )
    description_errors: list[str] = Field(
        default_factory=list,
        description="Description validation errors",
    )
    security_issues: list[str] = Field(
        default_factory=list,
        description="Security concerns found",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Improvement suggestions",
    )


# =============================================================================
# Phase Output Models (Aggregated)
# =============================================================================


class Phase1UnderstandingOutput(BaseModel):
    """
    Complete output from Phase 1: Understanding Workflow.

    Aggregates all understanding module outputs into a single typed model.
    """

    status: Literal["completed", "pending_user_input", "failed"] = Field(
        description="Phase completion status",
    )

    # Module outputs
    requirements: RequirementsOutput = Field(
        default_factory=RequirementsOutput,
        description="Requirements gathering output",
    )
    intent: IntentOutput = Field(
        default_factory=IntentOutput,
        description="Intent analysis output",
    )
    taxonomy: TaxonomyOutput = Field(
        default_factory=TaxonomyOutput,
        description="Taxonomy path finding output",
    )
    dependencies: DependencyOutput = Field(
        default_factory=DependencyOutput,
        description="Dependency analysis output",
    )
    plan: PlanOutput | None = Field(
        default=None,
        description="Synthesized plan (None if pending_user_input)",
    )

    # Structure validation
    structure_validation: StructureValidationOutput | None = Field(
        default=None,
        description="Early structure validation result",
    )

    # HITL context (populated when status == 'pending_user_input')
    hitl_type: str | None = Field(
        default=None,
        description="Type of HITL interaction needed (clarify, structure_fix)",
    )
    hitl_data: dict[str, Any] | None = Field(
        default=None,
        description="Data for HITL interaction (questions, context)",
    )

    # Execution metadata
    execution_time_ms: float | None = Field(
        default=None,
        description="Total execution time in milliseconds",
    )

    def is_ready_for_generation(self) -> bool:
        """Check if phase 1 completed successfully and ready for phase 2."""
        return self.status == "completed" and self.plan is not None

    def to_generation_input(self) -> dict[str, Any]:
        """Convert to input format expected by GenerationWorkflow."""
        if not self.is_ready_for_generation():
            raise ValueError("Phase 1 not completed - cannot convert to generation input")

        return {
            "plan": self.plan.model_dump() if self.plan else {},
            "understanding": {
                "requirements": self.requirements.model_dump(),
                "intent": self.intent.model_dump(),
                "taxonomy": self.taxonomy.model_dump(),
                "dependencies": dependencies_to_generation_list(self.dependencies),
                "dependency_analysis": self.dependencies.model_dump(),
            },
        }


class Phase2GenerationOutput(BaseModel):
    """
    Complete output from Phase 2: Generation Workflow.

    Contains generated SKILL.md content and metadata.
    """

    status: Literal["completed", "pending_user_input", "failed"] = Field(
        description="Phase completion status",
    )

    # Generated content
    skill_content: str = Field(
        default="",
        description="Generated SKILL.md content",
    )
    sections_generated: list[str] = Field(
        default_factory=list,
        description="List of sections generated",
    )
    code_examples_count: int = Field(
        default=0,
        description="Number of code examples included",
    )
    estimated_reading_time: int = Field(
        default=0,
        description="Estimated reading time in minutes",
    )

    # Quality metrics from generation
    initial_quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Quality score before refinement",
    )
    final_quality_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Quality score after refinement",
    )
    refinement_iterations: int = Field(
        default=0,
        description="Number of refinement iterations performed",
    )

    # HITL context (for preview checkpoint)
    hitl_type: str | None = Field(
        default=None,
        description="Type of HITL interaction (preview)",
    )
    hitl_data: dict[str, Any] | None = Field(
        default=None,
        description="Preview data for HITL",
    )

    # Execution metadata
    execution_time_ms: float | None = Field(
        default=None,
        description="Total execution time in milliseconds",
    )

    def is_ready_for_validation(self) -> bool:
        """Check if ready for validation phase."""
        return self.status == "completed" and bool(self.skill_content)


class TestCasesOutput(BaseModel):
    """Test cases generated for skill validation."""

    positive_tests: list[str] = Field(
        default_factory=list,
        description="Queries that should trigger the skill",
    )
    negative_tests: list[str] = Field(
        default_factory=list,
        description="Queries that should NOT trigger the skill",
    )
    edge_cases: list[str] = Field(
        default_factory=list,
        description="Ambiguous edge case queries",
    )
    functional_tests: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Scenario-based functional tests",
    )
    trigger_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Coverage of trigger phrases by tests",
    )


class QualityAssessmentOutput(BaseModel):
    """Quality assessment from AssessQualityModule."""

    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall quality score",
    )
    completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Content completeness score",
    )
    clarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Content clarity score",
    )
    usefulness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Practical usefulness score",
    )
    accuracy: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Technical accuracy score",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="Identified strengths",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Identified weaknesses",
    )
    feedback: str = Field(
        default="",
        description="Detailed feedback for improvement",
    )

    # Size metrics
    word_count: int = Field(
        default=0,
        description="Total word count",
    )
    size_assessment: Literal["optimal", "acceptable", "too_large", "too_small"] = Field(
        default="acceptable",
        description="Size category assessment",
    )
    verbosity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Verbosity score (0=concise, 1=verbose)",
    )


class ValidationReportOutput(BaseModel):
    """Validation report from Phase 3."""

    passed: bool = Field(
        description="Whether validation passed",
    )
    compliance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Compliance validation score",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Critical errors that must be fixed",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-critical warnings",
    )
    auto_fixable: list[str] = Field(
        default_factory=list,
        description="Issues that can be auto-fixed",
    )

    # Sub-reports
    structure_validation: StructureValidationOutput | None = Field(
        default=None,
        description="Structure validation details",
    )
    test_cases: TestCasesOutput | None = Field(
        default=None,
        description="Generated test cases",
    )
    quality_assessment: QualityAssessmentOutput | None = Field(
        default=None,
        description="Quality assessment details",
    )


class Phase3ValidationOutput(BaseModel):
    """
    Complete output from Phase 3: Validation Workflow.

    Contains validation results and potentially refined content.
    """

    status: Literal["completed", "needs_improvement", "pending_user_input", "failed"] = Field(
        description="Phase completion status",
    )

    # Validation results
    passed: bool = Field(
        description="Whether validation passed",
    )
    validation_report: ValidationReportOutput = Field(
        default_factory=ValidationReportOutput,
        description="Detailed validation report",
    )

    # Potentially refined content
    skill_content: str = Field(
        default="",
        description="Skill content (may be refined from Phase 2)",
    )
    was_refined: bool = Field(
        default=False,
        description="Whether content was refined during validation",
    )
    refinement_improvements: list[str] = Field(
        default_factory=list,
        description="Improvements made during refinement",
    )

    # HITL context (for review checkpoint)
    hitl_type: str | None = Field(
        default=None,
        description="Type of HITL interaction (review)",
    )
    hitl_data: dict[str, Any] | None = Field(
        default=None,
        description="Review data for HITL",
    )

    # Execution metadata
    execution_time_ms: float | None = Field(
        default=None,
        description="Total execution time in milliseconds",
    )


# =============================================================================
# Helper Functions
# =============================================================================


def dict_to_requirements(data: dict[str, Any]) -> RequirementsOutput:
    """Convert dict to RequirementsOutput with safe defaults."""
    return RequirementsOutput(
        domain=data.get("domain", "technical"),
        category=data.get("category", "general"),
        target_level=data.get("target_level", "intermediate"),
        topics=data.get("topics", []),
        constraints=data.get("constraints", []),
        ambiguities=data.get("ambiguities", []),
        suggested_skill_name=data.get("suggested_skill_name", ""),
        trigger_phrases=data.get("trigger_phrases", []),
        negative_triggers=data.get("negative_triggers", []),
        skill_category=data.get("skill_category", "other"),
        requires_mcp=data.get("requires_mcp", False),
        suggested_mcp_server=data.get("suggested_mcp_server", ""),
        reasoning=data.get("reasoning", ""),
    )


def dict_to_intent(data: dict[str, Any]) -> IntentOutput:
    """Convert dict to IntentOutput with safe defaults."""
    return IntentOutput(
        purpose=data.get("purpose", ""),
        problem_statement=data.get("problem_statement", ""),
        target_audience=data.get("target_audience", "Developers"),
        value_proposition=data.get("value_proposition", ""),
        skill_type=data.get("skill_type", "how_to"),
        scope=data.get("scope", ""),
        success_criteria=data.get("success_criteria", []),
        reasoning=data.get("reasoning", ""),
    )


def dict_to_taxonomy(data: dict[str, Any]) -> TaxonomyOutput:
    """Convert dict to TaxonomyOutput with safe defaults."""
    return TaxonomyOutput(
        recommended_path=data.get("recommended_path", "general/uncategorized"),
        alternative_paths=data.get("alternative_paths", []),
        path_rationale=data.get("path_rationale", ""),
        new_directories=data.get("new_directories", []),
        confidence=data.get("confidence", 0.0),
        reasoning=data.get("reasoning", ""),
        fallback=data.get("fallback", False),
    )


def dict_to_dependencies(data: dict[str, Any]) -> DependencyOutput:
    """Convert dict to DependencyOutput with safe defaults."""
    return DependencyOutput(
        prerequisite_skills=data.get("prerequisite_skills", []),
        complementary_skills=data.get("complementary_skills", []),
        conflicting_skills=data.get("conflicting_skills", []),
        missing_prerequisites=data.get("missing_prerequisites", []),
        dependency_rationale=data.get("dependency_rationale", ""),
        reasoning=data.get("reasoning", ""),
    )


def dependencies_to_generation_list(dependencies: Any) -> list[str]:
    """
    Normalize dependency output into a list format expected by generation.

    Phase 1 dependency analysis returns a dict-shaped object with keys like
    'prerequisite_skills'. Phase 2 content generation expects `dependencies`
    as a simple list of prerequisite skill IDs/strings.
    """
    if dependencies is None:
        return []
    if isinstance(dependencies, list):
        return [d for d in dependencies if isinstance(d, str)]
    if isinstance(dependencies, dict):
        prereqs = dependencies.get("prerequisite_skills", [])
        if isinstance(prereqs, list):
            return [d for d in prereqs if isinstance(d, str)]
        return []
    prerequisite_skills = getattr(dependencies, "prerequisite_skills", None)
    if isinstance(prerequisite_skills, list):
        return [d for d in prerequisite_skills if isinstance(d, str)]
    return []


def dict_to_plan(data: dict[str, Any]) -> PlanOutput:
    """Convert dict to PlanOutput with safe defaults."""
    return PlanOutput(
        skill_name=data.get("skill_name", "unnamed-skill"),
        skill_description=data.get("skill_description", ""),
        taxonomy_path=data.get("taxonomy_path", "general/uncategorized"),
        content_outline=data.get("content_outline", []),
        generation_guidance=data.get("generation_guidance", ""),
        success_criteria=data.get("success_criteria", []),
        estimated_length=data.get("estimated_length", "medium"),
        tags=data.get("tags", []),
        rationale=data.get("rationale", ""),
        reasoning=data.get("reasoning", ""),
        skill_metadata=data.get("skill_metadata", {}),
    )


# =============================================================================
# Export
# =============================================================================


__all__ = [
    # Configuration
    "QualityThresholds",
    "DEFAULT_QUALITY_THRESHOLDS",
    # Module outputs
    "RequirementsOutput",
    "IntentOutput",
    "TaxonomyOutput",
    "DependencyOutput",
    "PlanOutput",
    "StructureValidationOutput",
    "TestCasesOutput",
    "QualityAssessmentOutput",
    "ValidationReportOutput",
    # Phase outputs
    "Phase1UnderstandingOutput",
    "Phase2GenerationOutput",
    "Phase3ValidationOutput",
    # Helpers
    "dict_to_requirements",
    "dict_to_intent",
    "dict_to_taxonomy",
    "dict_to_dependencies",
    "dict_to_plan",
]
