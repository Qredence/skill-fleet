"""DSPy signatures for the agentic skills creation workflow."""

from __future__ import annotations

import dspy


class UnderstandTaskForSkill(dspy.Signature):
    """Extract task requirements and map to a taxonomy position."""

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


class PlanSkillStructure(dspy.Signature):
    """Design skill structure with taxonomy integration."""

    task_intent: str = dspy.InputField()
    taxonomy_path: str = dspy.InputField()
    parent_skills: str = dspy.InputField()
    dependency_analysis: str = dspy.InputField()

    skill_metadata: str = dspy.OutputField(
        desc="JSON metadata conforming to taxonomy schema (skill_id should equal taxonomy_path)"
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


class InitializeSkillSkeleton(dspy.Signature):
    """Create a skill skeleton matching taxonomy standards."""

    skill_metadata: str = dspy.InputField()
    capabilities: str = dspy.InputField()
    taxonomy_path: str = dspy.InputField()

    skill_skeleton: str = dspy.OutputField(
        desc="JSON description of full directory/file structure, relative to skills root"
    )
    validation_checklist: str = dspy.OutputField(desc="JSON array of validation points")


class EditSkillContent(dspy.Signature):
    """Generate comprehensive skill content with composition support."""

    skill_skeleton: str = dspy.InputField()
    parent_skills: str = dspy.InputField(desc="Content/metadata from parent/sibling skills")
    composition_strategy: str = dspy.InputField()

    skill_content: str = dspy.OutputField(desc="Full SKILL.md content")
    capability_implementations: str = dspy.OutputField(
        desc="JSON object mapping capabilities to documentation content"
    )
    usage_examples: str = dspy.OutputField(desc="JSON array of runnable usage examples")
    best_practices: str = dspy.OutputField(desc="JSON array of best practices")
    integration_guide: str = dspy.OutputField(desc="Integration notes and composition patterns")


class PackageSkillForApproval(dspy.Signature):
    """Validate and prepare a skill for approval."""

    skill_content: str = dspy.InputField()
    skill_metadata: str = dspy.InputField()
    taxonomy_path: str = dspy.InputField()
    capability_implementations: str = dspy.InputField()

    validation_report: str = dspy.OutputField(desc="JSON validation report for the skill package")
    integration_tests: str = dspy.OutputField(desc="JSON array of test cases for validation")
    packaging_manifest: str = dspy.OutputField(desc="JSON manifest describing the packaged output")
    quality_score: float = dspy.OutputField(desc="Overall quality score (0.0-1.0)")


class IterateSkillWithFeedback(dspy.Signature):
    """Manage HITL approval and skill evolution tracking."""

    packaged_skill: str = dspy.InputField()
    validation_report: str = dspy.InputField()
    human_feedback: str = dspy.InputField()
    usage_analytics: str = dspy.InputField()

    approval_status: str = dspy.OutputField(desc="One of: approved | needs_revision | rejected")
    revision_plan: str = dspy.OutputField(
        desc="If needs_revision: JSON object with changes required"
    )
    evolution_metadata: str = dspy.OutputField(desc="JSON object tracking skill evolution")
    next_steps: str = dspy.OutputField(desc="Concrete next steps based on approval status")
