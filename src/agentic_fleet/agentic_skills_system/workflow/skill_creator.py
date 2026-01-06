"""DSPy-based skill creation workflow integrated with the taxonomy manager."""

from __future__ import annotations

import json
from typing import Any

import dspy

from ..taxonomy.manager import TaxonomyManager
from .signatures import (
    EditSkillContent,
    InitializeSkillSkeleton,
    IterateSkillWithFeedback,
    PackageSkillForApproval,
    PlanSkillStructure,
    UnderstandTaskForSkill,
)


class TaxonomySkillCreator(dspy.Module):
    """Skill creation workflow with taxonomy integration."""

    def __init__(self, taxonomy_manager: TaxonomyManager, lm: dspy.LM | None = None) -> None:
        super().__init__()
        self.taxonomy = taxonomy_manager

        if lm is not None:
            dspy.settings.configure(lm=lm)

        self.understand = dspy.ChainOfThought(UnderstandTaskForSkill)
        self.plan = dspy.ChainOfThought(PlanSkillStructure)
        self.initialize = dspy.ChainOfThought(InitializeSkillSkeleton)
        self.edit = dspy.ChainOfThought(EditSkillContent)
        self.package = dspy.ChainOfThought(PackageSkillForApproval)
        self.iterate = dspy.ChainOfThought(IterateSkillWithFeedback)

    def forward(
        self,
        task_description: str,
        user_context: dict[str, Any],
        max_iterations: int = 3,
        auto_approve: bool = False,
    ) -> dict[str, Any]:
        """Execute full skill creation workflow.

        Note: This workflow requires an LLM configured in DSPy. For unit tests,
        either skip invocation or provide a mocked LM/module stack.
        """
        user_id = str(user_context.get("user_id", "default"))

        understanding = self.understand(
            task_description=task_description,
            existing_skills=json.dumps(self.taxonomy.get_mounted_skills(user_id)),
            taxonomy_structure=json.dumps(self.taxonomy.get_relevant_branches(task_description)),
        )

        if self.taxonomy.skill_exists(understanding.taxonomy_path):
            return {
                "status": "exists",
                "path": understanding.taxonomy_path,
                "message": "Skill already exists in taxonomy",
            }

        plan = self.plan(
            task_intent=understanding.task_intent,
            taxonomy_path=understanding.taxonomy_path,
            parent_skills=understanding.parent_skills,
            dependency_analysis=understanding.dependency_analysis,
        )

        skill_metadata: dict[str, Any] = json.loads(plan.skill_metadata)
        dependencies: list[dict[str, Any]] = json.loads(plan.dependencies)

        # Validate dependencies before proceeding.
        deps_valid, missing_deps = self.taxonomy.validate_dependencies(
            [d["skill_id"] for d in dependencies if "skill_id" in d]
        )
        if not deps_valid:
            return {
                "status": "error",
                "message": f"Cannot resolve dependencies: {missing_deps}",
            }

        has_cycle, cycle_path = self.taxonomy.detect_circular_dependencies(
            skill_metadata["skill_id"],
            [d["skill_id"] for d in dependencies if "skill_id" in d],
        )
        if has_cycle:
            return {"status": "error", "message": f"Circular dependency: {cycle_path}"}

        skeleton = self.initialize(
            skill_metadata=plan.skill_metadata,
            capabilities=plan.capabilities,
            taxonomy_path=understanding.taxonomy_path,
        )

        content = self.edit(
            skill_skeleton=skeleton.skill_skeleton,
            parent_skills=understanding.parent_skills,
            composition_strategy=plan.composition_strategy,
        )

        package = self.package(
            skill_content=content.skill_content,
            skill_metadata=plan.skill_metadata,
            taxonomy_path=understanding.taxonomy_path,
            capability_implementations=content.capability_implementations,
        )

        validation = json.loads(package.validation_report)
        if validation.get("errors"):
            return {"status": "validation_failed", "errors": validation["errors"]}

        iteration_count = 0
        while iteration_count < max_iterations:
            if auto_approve:
                feedback = json.dumps(
                    {
                        "status": "approved",
                        "comments": "Auto-approved for testing",
                        "reviewer": "system",
                    }
                )
            else:
                feedback = self._get_human_feedback(package.packaging_manifest, validation)

            approval = self.iterate(
                packaged_skill=package.packaging_manifest,
                validation_report=package.validation_report,
                human_feedback=feedback,
                usage_analytics=json.dumps({}),
            )

            if approval.approval_status == "approved":
                success = self.taxonomy.register_skill(
                    path=understanding.taxonomy_path,
                    metadata=skill_metadata,
                    content=content.skill_content,
                    evolution=json.loads(approval.evolution_metadata),
                )
                if not success:
                    return {"status": "error", "message": "Failed to register skill in taxonomy"}

                return {
                    "status": "approved",
                    "skill_id": skill_metadata["skill_id"],
                    "path": understanding.taxonomy_path,
                    "version": skill_metadata["version"],
                    "quality_score": package.quality_score,
                }

            if approval.approval_status == "needs_revision":
                # TODO: incorporate revision feedback into EDIT and re-package.
                iteration_count += 1
                continue

            return {"status": "rejected", "reason": approval.revision_plan}

        return {
            "status": "max_iterations_reached",
            "message": f"Skill not approved after {max_iterations} iterations",
        }

    def _get_human_feedback(
        self, packaging_manifest: str, validation_report: dict[str, Any]
    ) -> str:
        """Get human feedback on packaged skill.

        Phase 1 default behaviour: auto-approve. Replace with a real HITL surface
        (CLI prompts, web UI, issue tracker integration, etc.).
        """
        _ = packaging_manifest
        _ = validation_report
        return json.dumps(
            {
                "status": "approved",
                "comments": "Automated approval - implement HITL interface",
                "reviewer": "system",
            }
        )
