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
    """Collect concrete usage examples from user before creating skill.

    Ground skills in real use cases, not assumptions. Ask focused questions
    about functionality, triggering conditions, and edge cases.

    Conclude when: readiness_score >= threshold AND min_examples collected.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="Initial task description from user (what skill they need)"
    )
    user_responses: str = dspy.InputField(
        desc="JSON array of previous user responses: [{question_id, answer_text}, ...]. "
        "Empty array [] on first round."
    )
    collected_examples: str = dspy.InputField(
        desc="JSON array of UserExample objects collected: [{input_description, expected_output, context}, ...]. "
        "Empty array [] on first round."
    )
    config: str = dspy.InputField(
        desc="JSON ExampleGatheringConfig: {min_examples: 3, readiness_threshold: 0.8, max_questions: 10}"
    )

    # Outputs
    clarifying_questions: list[ClarifyingQuestion] = dspy.OutputField(
        desc="1-3 focused questions (fewer better). Each has: question_text, context, suggested_answers. "
        "Ask about: specific use cases, triggering conditions, edge cases. "
        "Empty list [] when ready to proceed (readiness_score >= threshold)."
    )
    new_examples: list[UserExample] = dspy.OutputField(
        desc="New examples extracted from latest user responses. Each has: input_description, expected_output, context. "
        "Add to collected_examples for cumulative gathering. Empty list [] if no new examples this round."
    )
    terminology_updates: dict[str, str] = dspy.OutputField(
        desc="Domain-specific terms learned this round: {term: definition}. "
        "Use for consistent vocabulary in generated skill. Empty dict {} if no new terms."
    )
    refined_task: str = dspy.OutputField(
        desc="Updated task description incorporating user responses and examples. "
        "More specific than original. Use this for Phase 1 Understanding step."
    )
    readiness_score: float = dspy.OutputField(
        desc="Readiness 0.0-1.0. Score based on: example diversity (0-0.4), clarity (0-0.3), "
        "edge case coverage (0-0.3). >= threshold (default 0.8) means proceed to Phase 1."
    )
    readiness_reasoning: str = dspy.OutputField(
        desc="1-2 sentence explanation of score. If ready: what we learned. "
        "If not ready: what specific information still missing. Be concrete."
    )


# =============================================================================
# Step 1: Understand - Task Analysis
# =============================================================================


class UnderstandTaskForSkill(dspy.Signature):
    """Analyze task requirements and determine taxonomy placement.

    Extract core intent, find optimal taxonomy path, identify related skills,
    and analyze dependencies. Be thorough but concise.
    """

    # Inputs
    task_description: str = dspy.InputField(
        desc="User's task description (what skill to create and why)"
    )
    existing_skills: str = dspy.InputField(
        desc="JSON array of current skill_ids: ['python/async', 'web/react', ...]. "
        "Use to avoid duplication and find related skills."
    )
    taxonomy_structure: str = dspy.InputField(
        desc="JSON taxonomy tree with categories and existing skills. "
        "Format: {category: {subcategory: [skill_ids], ...}, ...}"
    )

    # Outputs
    task_intent: str = dspy.OutputField(
        desc="Core intent (1-3 sentences): what user wants to achieve, why this skill is needed, "
        "what problem it solves. Be specific and actionable."
    )
    taxonomy_path: str = dspy.OutputField(
        desc="Proposed path in v0.2 format: 'category/skill-name' (2-level structure). "
        "Use kebab-case. Examples: 'python/async-patterns', 'web/react-hooks'. "
        "Prefer existing categories, justify new ones."
    )
    parent_skills: list[ParentSkillInfo] = dspy.OutputField(
        desc="0-5 related skills in same category/parent category. Each has: skill_id, relationship (parent/sibling/related). "
        "Use for understanding existing patterns and avoiding duplication. Empty list [] if creating new category."
    )
    dependency_analysis: DependencyAnalysis = dspy.OutputField(
        desc="Dependency analysis object with: required (list of prerequisite skill_ids), "
        "recommended (complementary skill_ids), conflicts (incompatible skill_ids), rationale"
    )
    confidence_score: float = dspy.OutputField(
        desc="Confidence 0.0-1.0 in analysis quality. >0.8 = high confidence (clear requirements), "
        "0.6-0.8 = moderate, <0.6 = low (may need HITL clarification). "
        "Consider: task clarity, taxonomy fit, dependency certainty."
    )


# =============================================================================
# Step 2: Plan - Skill Structure Design
# =============================================================================


class PlanSkillStructure(dspy.Signature):
    """Design complete skill structure ensuring agentskills.io compliance.

    Create metadata, define capabilities, specify dependencies, and plan composition.
    All outputs must be production-ready and validation-compliant.
    """

    # Inputs
    task_intent: str = dspy.InputField(
        desc="Core intent from understand step (purpose, problem, value)"
    )
    taxonomy_path: str = dspy.InputField(
        desc="Validated taxonomy path in v0.2 format: 'category/skill-name'"
    )
    parent_skills: str = dspy.InputField(
        desc="JSON array of related ParentSkillInfo objects for pattern consistency"
    )
    dependency_analysis: str = dspy.InputField(
        desc="JSON DependencyAnalysis with prerequisites, complementary skills, conflicts"
    )

    # Outputs - typed for validation
    skill_metadata: SkillMetadata = dspy.OutputField(
        desc="Metadata object: name (kebab-case matching taxonomy path leaf), "
        "description (starts with 'Use when...', 10-30 words, specific triggers), "
        "taxonomy_path, tags (3-7 keywords), version (1.0.0 for new skills). "
        "MUST pass agentskills.io validation."
    )
    dependencies: list[DependencyRef] = dspy.OutputField(
        desc="0-5 dependencies (prerequisites + key complementary skills). Each has: skill_id, reason. "
        "Order by importance. Include only dependencies that significantly impact skill usage."
    )
    capabilities: list[Capability] = dspy.OutputField(
        desc="3-7 discrete, testable capabilities this skill provides. Each has: name, description, rationale. "
        "Each capability should map to a major skill section or pattern. "
        "Be specific (not 'handle async' but 'implement async/await with error handling')."
    )
    resource_requirements: ResourceRequirements = dspy.OutputField(
        desc="External resources object: apis (external APIs needed), tools (CLI tools), "
        "files (config files), packages (language packages). Specify versions where relevant. "
        "Empty fields for self-contained skills."
    )
    compatibility_constraints: CompatibilityConstraints = dspy.OutputField(
        desc="Compatibility object: python_version, platforms (list), conflicts (incompatible skills/tools). "
        "Be specific: '>= 3.10' not '3.x'. Empty/null fields if no constraints."
    )
    composition_strategy: str = dspy.OutputField(
        desc="1-2 paragraphs on skill composition: how this skill works with dependencies, "
        "when to load with other skills, common skill combinations. "
        "Include concrete examples: 'Load with python/basics when...'. Empty string '' if standalone."
    )


# =============================================================================
# Step 3: Initialize - Skeleton Creation
# =============================================================================


class InitializeSkillSkeleton(dspy.Signature):
    """Create a skill skeleton matching taxonomy standards.

    Generates the directory structure and file list for the skill,
    following the v2 Golden Standard layout:
    - metadata.json
    - SKILL.md
    - references/ (v2 standard, replaces capabilities/)
    - guides/ (v2 standard, replaces resources/)
    - templates/ (v2 standard)
    - scripts/
    - examples/
    - tests/
    - assets/

    Legacy directories (capabilities/, resources/) may be created for backward compatibility.
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
    """Generate production-ready SKILL.md with all required sections and quality indicators.

    MUST include: When to Use This Skill, Quick Start, ❌/✅ contrast patterns, core principle.
    Follow v2 Golden Standard. YAML frontmatter added automatically.
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
        desc="Complete SKILL.md body (frontmatter added separately). Required sections: "
        "(1) ## When to Use This Skill - specific triggers, (2) ## Quick Start - copy-paste examples, "
        "(3) ## Patterns - with ❌ anti-patterns and ✅ production patterns. "
        "Include: **Core principle:** statement, strong guidance (ALWAYS/NEVER/MUST), "
        "executable code blocks with language tags. Min 50 lines, production quality."
    )
    capability_implementations: list[CapabilityImplementation] = dspy.OutputField(
        desc="Implementation docs for each capability (matches capabilities from plan). "
        "Each has: capability_id, content (markdown with code examples), code_snippets (standalone). "
        "Min 1, typically 3-7 implementations."
    )
    usage_examples: list[UsageExample] = dspy.OutputField(
        desc="3-5 executable usage examples. Each has: title, description, code (copy-paste ready), "
        "expected_output, notes. Real-world scenarios preferred over toy examples."
    )
    best_practices: list[BestPractice] = dspy.OutputField(
        desc="5-10 actionable best practices. Each has: title, description, rationale. "
        "Include common mistakes (❌) and correct patterns (✅). Order by importance."
    )
    integration_guide: str = dspy.OutputField(
        desc="Integration and composition guidance (1-2 paragraphs). How to combine with other skills, "
        "when to load together, common workflows. Include specific skill names. "
        "Empty string '' if skill is standalone."
    )


# =============================================================================
# Step 5: Package - Validation & Packaging
# =============================================================================


class PackageSkillForApproval(dspy.Signature):
    """Validate skill and prepare for approval with quality assessment.

    Run agentskills.io validation, quality scoring, and test generation.
    Ensure skill meets minimum quality threshold before packaging.
    """

    # Inputs
    skill_content: str = dspy.InputField(desc="Generated SKILL.md content")
    skill_metadata: str = dspy.InputField(desc="JSON skill metadata")
    taxonomy_path: str = dspy.InputField(desc="Taxonomy path")
    capability_implementations: str = dspy.InputField(desc="JSON capability documentation")

    # Outputs - typed for structured validation
    validation_report: ValidationReport = dspy.OutputField(
        desc="Validation object: passed (bool), errors (list of issues blocking approval), "
        "warnings (list of non-blocking issues), compliance_checks (agentskills.io validation results)"
    )
    integration_tests: list[TestCase] = dspy.OutputField(
        desc="2-5 test cases for skill verification. Each has: name, test_input, expected_behavior, "
        "assertion. Tests should verify: (1) core capability works, (2) examples are executable, "
        "(3) error handling works. Empty list [] if skill is pure documentation."
    )
    packaging_manifest: PackagingManifest = dspy.OutputField(
        desc="Packaging manifest with: skill_id, version, file_list (SKILL.md + subdirectories), "
        "dependencies, compatibility, checksum. Used for skill distribution and versioning."
    )
    quality_score: float = dspy.OutputField(
        desc="Overall quality 0.0-1.0 using skill_quality_metric. >0.80 = excellent (approve), "
        "0.60-0.80 = good (minor improvements), <0.60 = needs revision. "
        "Based on: structure completeness, pattern quality, code examples, quality indicators."
    )


# =============================================================================
# Step 6: Iterate - Feedback & Evolution
# =============================================================================


class IterateSkillWithFeedback(dspy.Signature):
    """Process HITL feedback and determine next action.

    Analyze feedback to decide: approved (ship it), needs_revision (specific changes),
    rejected (fundamental issues). Generate concrete revision plan if needed.
    """

    # Inputs
    packaged_skill: str = dspy.InputField(desc="JSON packaging manifest")
    validation_report: str = dspy.InputField(desc="JSON validation report")
    human_feedback: str = dspy.InputField(desc="Human reviewer feedback")
    usage_analytics: str = dspy.InputField(desc="JSON usage analytics (if available)")

    # Outputs - typed for structured decisions
    approval_status: Literal["approved", "needs_revision", "rejected"] = dspy.OutputField(
        desc="Decision: approved (quality_score >0.80 AND no critical errors), "
        "needs_revision (fixable issues OR 0.60-0.80 score), "
        "rejected (fundamental problems OR quality_score <0.60). "
        "Be conservative with approval - quality matters."
    )
    revision_plan: RevisionPlan = dspy.OutputField(
        desc="Revision plan object (required if needs_revision, null otherwise): "
        "changes_needed (specific list), priority (high/medium/low), estimated_effort. "
        "Be concrete: 'Add error handling section' not 'Improve quality'."
    )
    evolution_metadata: EvolutionMetadata = dspy.OutputField(
        desc="Evolution tracking object: version, revision_count, quality_history (scores over time), "
        "feedback_summary. Used for skill lifecycle management and continuous improvement."
    )
    next_steps: str = dspy.OutputField(
        desc="1-3 concrete next steps based on status. Approved: 'Promote to production', "
        "Needs revision: 'Address errors in revision_plan', Rejected: 'Restart with clearer requirements'. "
        "Be actionable and specific."
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
