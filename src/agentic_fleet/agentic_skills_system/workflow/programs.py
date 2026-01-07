"""DSPy programs for complete skill creation workflows.

Programs compose multiple modules into end-to-end workflows
with proper error handling and state management.
"""

import logging

import dspy

from .modules import (
    EditModule,
    InitializeModule,
    PackageModule,
    PlanModule,
    UnderstandModule,
)

logger = logging.getLogger(__name__)


class SkillCreationProgram(dspy.Module):
    """Complete skill creation program (Steps 1-5).

    This program executes the core creation workflow without
    the HITL iteration step.
    """

    def __init__(self):
        super().__init__()
        self.understand = UnderstandModule()
        self.plan = PlanModule()
        self.initialize = InitializeModule()
        self.edit = EditModule()
        self.package = PackageModule()

    def forward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: callable,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Execute Steps 1-5 of skill creation.

        Args:
            task_description: User's task description
            existing_skills: Currently mounted skills
            taxonomy_structure: Relevant taxonomy branches
            parent_skills_getter: Function to get parent skills for a path
            task_lms: Dictionary of task-specific LMs

        Returns:
            Dict with all outputs from Steps 1-5
        """

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else None
        with dspy.context(lm=lm):
            understanding = self.understand(
                task_description=task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else None
        parent_skills = parent_skills_getter(understanding["taxonomy_path"])
        with dspy.context(lm=lm):
            plan = self.plan(
                task_intent=understanding["task_intent"],
                taxonomy_path=understanding["taxonomy_path"],
                parent_skills=parent_skills,
                dependency_analysis=understanding["dependency_analysis"],
            )

        # Step 3: INITIALIZE
        lm = task_lms.get("skill_initialize") if task_lms else None
        with dspy.context(lm=lm):
            skeleton = self.initialize(
                skill_metadata=plan["skill_metadata"],
                capabilities=plan["capabilities"],
                taxonomy_path=understanding["taxonomy_path"],
            )

        # Step 4: EDIT
        lm = task_lms.get("skill_edit") if task_lms else None
        with dspy.context(lm=lm):
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=understanding["parent_skills"],
                composition_strategy=plan["composition_strategy"],
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else None
        with dspy.context(lm=lm):
            package = self.package(
                skill_content=content["skill_content"],
                skill_metadata=plan["skill_metadata"],
                taxonomy_path=understanding["taxonomy_path"],
                capability_implementations=content["capability_implementations"],
            )

        return {
            "understanding": understanding,
            "plan": plan,
            "skeleton": skeleton,
            "content": content,
            "package": package,
        }


class SkillRevisionProgram(dspy.Module):
    """Program for revising existing skill content (Steps 4-5).

    Used when iteration requires content regeneration.
    """

    def __init__(self):
        super().__init__()
        self.edit = EditModule()
        self.package = PackageModule()

    def forward(
        self,
        skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        plan: dict,
        taxonomy_path: str,
        revision_feedback: str | None = None,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Regenerate and repackage skill content.

        Returns:
            Dict with revised content and package
        """

        # Step 4: EDIT (with feedback)
        lm = task_lms.get("skill_edit") if task_lms else None
        with dspy.context(lm=lm):
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills,
                composition_strategy=composition_strategy,
                revision_feedback=revision_feedback,
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else None
        with dspy.context(lm=lm):
            package = self.package(
                skill_content=content["skill_content"],
                skill_metadata=plan["skill_metadata"],
                taxonomy_path=taxonomy_path,
                capability_implementations=content["capability_implementations"],
            )

        return {"content": content, "package": package}


class QuickSkillProgram(dspy.Module):
    """Streamlined program for rapid skill generation.

    Optimized for speed with minimal validation, useful for
    bootstrap and development scenarios.
    """

    def __init__(self):
        super().__init__()
        self.understand = UnderstandModule()
        self.plan = PlanModule()
        self.edit = EditModule()

    def forward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: callable,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Quick skill generation (Steps 1-2-4 only).

        Skips initialization and packaging for speed.
        """

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else None
        with dspy.context(lm=lm):
            understanding = self.understand(
                task_description=task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else None
        parent_skills = parent_skills_getter(understanding["taxonomy_path"])
        with dspy.context(lm=lm):
            plan = self.plan(
                task_intent=understanding["task_intent"],
                taxonomy_path=understanding["taxonomy_path"],
                parent_skills=parent_skills,
                dependency_analysis=understanding["dependency_analysis"],
            )

        # Step 4: EDIT (skip initialization)
        skeleton = {
            "skill_skeleton": {
                "root_path": f"skills/{understanding['taxonomy_path']}/",
                "files": [],
                "directories": ["capabilities/", "examples/", "tests/", "resources/"],
            }
        }

        lm = task_lms.get("skill_edit") if task_lms else None
        with dspy.context(lm=lm):
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=understanding["parent_skills"],
                composition_strategy=plan["composition_strategy"],
            )

        return {"understanding": understanding, "plan": plan, "content": content}
