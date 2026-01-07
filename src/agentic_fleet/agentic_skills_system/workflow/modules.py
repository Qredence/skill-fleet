"""DSPy modules for skill creation workflow steps.

Each module encapsulates one step of the workflow with its own
logic, validation, and error handling.
"""

import json
import logging

import dspy

from .signatures import (
    EditSkillContent,
    InitializeSkillSkeleton,
    IterateSkillWithFeedback,
    PackageSkillForApproval,
    PlanSkillStructure,
    UnderstandTaskForSkill,
)

logger = logging.getLogger(__name__)


class UnderstandModule(dspy.Module):
    """Module for Step 1: Understanding task and mapping to taxonomy."""

    def __init__(self):
        super().__init__()
        self.understand = dspy.ChainOfThought(UnderstandTaskForSkill)

    def forward(
        self, task_description: str, existing_skills: list[str], taxonomy_structure: dict
    ) -> dict:
        """Analyze task and determine taxonomy placement.

        Returns:
            Dict with task_intent, taxonomy_path, parent_skills,
            dependency_analysis, and confidence_score
        """
        result = self.understand(
            task_description=task_description,
            existing_skills=json.dumps(existing_skills, indent=2),
            taxonomy_structure=json.dumps(taxonomy_structure, indent=2),
        )

        return {
            "task_intent": result.task_intent,
            "taxonomy_path": result.taxonomy_path.strip(),
            "parent_skills": result.parent_skills,
            "dependency_analysis": result.dependency_analysis,
            "confidence_score": float(result.confidence_score),
        }


class PlanModule(dspy.Module):
    """Module for Step 2: Planning skill structure."""

    def __init__(self):
        super().__init__()
        self.plan = dspy.ChainOfThought(PlanSkillStructure)

    def forward(
        self,
        task_intent: str,
        taxonomy_path: str,
        parent_skills: list[dict],
        dependency_analysis: str,
    ) -> dict:
        """Design skill structure with dependencies.

        Returns:
            Dict with skill_metadata, dependencies, capabilities,
            resource_requirements, compatibility_constraints,
            and composition_strategy
        """
        result = self.plan(
            task_intent=task_intent,
            taxonomy_path=taxonomy_path,
            parent_skills=json.dumps(parent_skills, indent=2),
            dependency_analysis=dependency_analysis,
        )

        return {
            "skill_metadata": json.loads(result.skill_metadata),
            "dependencies": json.loads(result.dependencies),
            "capabilities": json.loads(result.capabilities),
            "resource_requirements": result.resource_requirements,
            "compatibility_constraints": result.compatibility_constraints,
            "composition_strategy": result.composition_strategy,
        }


class InitializeModule(dspy.Module):
    """Module for Step 3: Initializing skill skeleton."""

    def __init__(self):
        super().__init__()
        self.initialize = dspy.ChainOfThought(InitializeSkillSkeleton)

    def forward(self, skill_metadata: dict, capabilities: list[str], taxonomy_path: str) -> dict:
        """Create a skill file structure.

        Returns:
            Dict with skill_skeleton and validation_checklist
        """
        result = self.initialize(
            skill_metadata=json.dumps(skill_metadata, indent=2),
            capabilities=json.dumps(capabilities, indent=2),
            taxonomy_path=taxonomy_path,
        )

        return {
            "skill_skeleton": json.loads(result.skill_skeleton),
            "validation_checklist": result.validation_checklist,
        }


class EditModule(dspy.Module):
    """Module for Step 4: Editing skill content."""

    def __init__(self):
        super().__init__()
        self.edit = dspy.ChainOfThought(EditSkillContent)

    def forward(
        self,
        skill_skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        revision_feedback: str | None = None,
    ) -> dict:
        """Generate comprehensive skill content.

        Args:
            skill_skeleton: Directory structure
            parent_skills: Context from related skills
            composition_strategy: How skill composes with others
            revision_feedback: Optional feedback for regeneration

        Returns:
            Dict with skill_content, capability_implementations,
            usage_examples, best_practices, and integration_guide
        """
        # TODO: Incorporate revision_feedback into prompt
        result = self.edit(
            skill_skeleton=json.dumps(skill_skeleton, indent=2),
            parent_skills=parent_skills,
            composition_strategy=composition_strategy,
        )

        return {
            "skill_content": result.skill_content,
            "capability_implementations": result.capability_implementations,
            "usage_examples": result.usage_examples,
            "best_practices": result.best_practices,
            "integration_guide": result.integration_guide,
        }


class PackageModule(dspy.Module):
    """Module for Step 5: Packaging and validation."""

    def __init__(self):
        super().__init__()
        self.package = dspy.ChainOfThought(PackageSkillForApproval)

    def forward(
        self,
        skill_content: str,
        skill_metadata: dict,
        taxonomy_path: str,
        capability_implementations: str,
    ) -> dict:
        """Validate and package skill for approval.

        Returns:
            Dict with validation_report, integration_tests,
            packaging_manifest, and quality_score
        """
        result = self.package(
            skill_content=skill_content,
            skill_metadata=json.dumps(skill_metadata, indent=2),
            taxonomy_path=taxonomy_path,
            capability_implementations=capability_implementations,
        )

        report = json.loads(result.validation_report)

        return {
            "validation_report": report,
            "integration_tests": result.integration_tests,
            "packaging_manifest": result.packaging_manifest,
            "quality_score": float(result.quality_score),
        }


class IterateModule(dspy.Module):
    """Module for Step 6: Iteration with human feedback."""

    def __init__(self):
        super().__init__()
        self.iterate = dspy.ChainOfThought(IterateSkillWithFeedback)

    def forward(
        self,
        packaged_skill: str,
        validation_report: dict,
        human_feedback: str,
        usage_analytics: dict | None = None,
    ) -> dict:
        """Process human feedback and determine next steps.

        Returns:
            Dict with approval_status, revision_plan,
            evolution_metadata, and next_steps
        """
        result = self.iterate(
            packaged_skill=packaged_skill,
            validation_report=json.dumps(validation_report, indent=2),
            human_feedback=human_feedback,
            usage_analytics=json.dumps(usage_analytics or {}),
        )

        return {
            "approval_status": result.approval_status.strip().lower(),
            "revision_plan": result.revision_plan,
            "evolution_metadata": json.loads(result.evolution_metadata),
            "next_steps": result.next_steps,
        }
