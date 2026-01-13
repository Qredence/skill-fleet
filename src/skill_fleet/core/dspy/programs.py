"""DSPy programs for complete skill creation workflows.

Programs compose multiple modules into end-to-end workflows
with proper error handling and state management.

This module provides:
- SkillCreationProgram: Full workflow (Steps 1-5)
- SkillCreationProgramQA: Quality-assured version with Refine/BestOfN
- SkillRevisionProgram: Content revision (Steps 4-5)
- QuickSkillProgram: Fast generation (Steps 1-2-4)

Async Support:
All programs support async execution via the aforward() method.

Approved LLM Models:
- gemini-3-flash-preview: Primary model for all steps
- gemini-3-pro-preview: For GEPA reflection
- deepseek-v3.2: Cost-effective alternative
- Nemotron-3-Nano-30B-A3B: Lightweight operations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import dspy

from ...common.utils import json_serialize
from .modules import (
    EditModule,
    EditModuleQA,
    GatherExamplesModule,  # ADD THIS
    InitializeModule,
    PackageModule,
    PackageModuleQA,
    PlanModule,
    PlanModuleQA,
    UnderstandModule,
    UnderstandModuleQA,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# =============================================================================
# Standard Skill Creation Program
# =============================================================================


class SkillCreationProgram(dspy.Module):
    """Complete skill creation program (Steps 1-5).

    This program executes the core creation workflow without
    the HITL iteration step.
    """

    def __init__(self, quality_assured: bool = False):
        """Initialize skill creation program.

        Args:
            quality_assured: If True, use Refine/BestOfN wrappers for
                            higher quality outputs (slower, more LLM calls)
        """
        super().__init__()
        self._quality_assured = quality_assured

        if quality_assured:
            self.gather = GatherExamplesModule()  # No QA needed for interaction
            self.understand = UnderstandModuleQA()
            self.plan = PlanModuleQA()
            self.initialize = InitializeModule()  # No QA needed
            self.edit = EditModuleQA()
            self.package = PackageModuleQA()
        else:
            self.gather = GatherExamplesModule()
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
        parent_skills_getter: Callable[[str], Any],
        task_lms: dict[str, dspy.LM] | None = None,
        gathered_examples: list[dict] | None = None,
    ) -> dict:
        """Execute Steps 1-5 of skill creation.

        Args:
            task_description: User's task description
            existing_skills: Currently mounted skills
            taxonomy_structure: Relevant taxonomy branches
            parent_skills_getter: Function to get parent skills for a path
            task_lms: Dictionary of task-specific LMs
            gathered_examples: Optional examples collected from user (Step 0)

        Returns:
            Dict with all outputs from Steps 1-5
        """
        # Append examples to task description if provided
        final_task_description = task_description
        if gathered_examples:
            examples_text = "\n\nUser Provided Examples:\n"
            for ex in gathered_examples:
                examples_text += (
                    f"- {ex.get('input_description', '')} -> {ex.get('expected_output', '')}\n"
                )
            final_task_description += examples_text

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            understanding = self.understand(
                task_description=final_task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else dspy.settings.lm
        parent_skills = parent_skills_getter(understanding["taxonomy_path"])
        with dspy.context(lm=lm):
            plan = self.plan(
                task_intent=understanding["task_intent"],
                taxonomy_path=understanding["taxonomy_path"],
                parent_skills=parent_skills,
                dependency_analysis=understanding["dependency_analysis"],
            )

        # Step 3: INITIALIZE
        lm = task_lms.get("skill_initialize") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            skeleton = self.initialize(
                skill_metadata=plan["skill_metadata"],
                capabilities=plan["capabilities"],
                taxonomy_path=understanding["taxonomy_path"],
            )

        # Step 4: EDIT
        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            # Serialize parent_skills to JSON string (EditModule expects str, not list)
            parent_skills_str = json_serialize(understanding["parent_skills"])
            # Serialize composition_strategy to JSON string if it's a dict
            composition_strategy_str = json_serialize(plan.get("composition_strategy", ""))
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills_str,
                composition_strategy=composition_strategy_str,
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else dspy.settings.lm
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

    async def aforward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: Callable[[str], Any],
        task_lms: dict[str, dspy.LM] | None = None,
        gathered_examples: list[dict] | None = None,
    ) -> dict:
        """Async execution of Steps 1-5.

        Same as forward() but using async LM calls for better throughput.
        """
        # Append examples to task description if provided
        final_task_description = task_description
        if gathered_examples:
            examples_text = "\n\nUser Provided Examples:\n"
            for ex in gathered_examples:
                examples_text += (
                    f"- {ex.get('input_description', '')} -> {ex.get('expected_output', '')}\n"
                )
            final_task_description += examples_text

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            understanding = await self.understand.acall(
                task_description=final_task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else dspy.settings.lm
        parent_skills = parent_skills_getter(understanding["taxonomy_path"])
        with dspy.context(lm=lm):
            plan = await self.plan.acall(
                task_intent=understanding["task_intent"],
                taxonomy_path=understanding["taxonomy_path"],
                parent_skills=parent_skills,
                dependency_analysis=understanding["dependency_analysis"],
            )

        # Step 3: INITIALIZE
        lm = task_lms.get("skill_initialize") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            skeleton = await self.initialize.acall(
                skill_metadata=plan["skill_metadata"],
                capabilities=plan["capabilities"],
                taxonomy_path=understanding["taxonomy_path"],
            )

        # Step 4: EDIT
        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            # Serialize parent_skills to JSON string (EditModule expects str, not list)
            parent_skills_str = json_serialize(understanding["parent_skills"])
            # Serialize composition_strategy to JSON string if it's a dict
            composition_strategy_str = json_serialize(plan.get("composition_strategy", ""))
            content = await self.edit.acall(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills_str,
                composition_strategy=composition_strategy_str,
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            package = await self.package.acall(
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


# =============================================================================
# Quality-Assured Skill Creation Program (Convenience Alias)
# =============================================================================


class SkillCreationProgramQA(SkillCreationProgram):
    """Quality-assured skill creation program.

    Convenience class that initializes SkillCreationProgram
    with quality_assured=True.
    """

    def __init__(self):
        super().__init__(quality_assured=True)


# =============================================================================
# Skill Revision Program
# =============================================================================


class SkillRevisionProgram(dspy.Module):
    """Program for revising existing skill content (Steps 4-5).

    Used when iteration requires content regeneration.
    """

    def __init__(self, quality_assured: bool = False):
        super().__init__()
        if quality_assured:
            self.edit = EditModuleQA()
            self.package = PackageModuleQA()
        else:
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
        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills,
                composition_strategy=composition_strategy,
                revision_feedback=revision_feedback,
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            package = self.package(
                skill_content=content["skill_content"],
                skill_metadata=plan["skill_metadata"],
                taxonomy_path=taxonomy_path,
                capability_implementations=content["capability_implementations"],
            )

        return {"content": content, "package": package}

    async def aforward(
        self,
        skeleton: dict,
        parent_skills: str,
        composition_strategy: str,
        plan: dict,
        taxonomy_path: str,
        revision_feedback: str | None = None,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Async regeneration and repackaging."""

        # Step 4: EDIT (with feedback)
        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            content = await self.edit.acall(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills,
                composition_strategy=composition_strategy,
                revision_feedback=revision_feedback,
            )

        # Step 5: PACKAGE
        lm = task_lms.get("skill_package") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            package = await self.package.acall(
                skill_content=content["skill_content"],
                skill_metadata=plan["skill_metadata"],
                taxonomy_path=taxonomy_path,
                capability_implementations=content["capability_implementations"],
            )

        return {"content": content, "package": package}


# =============================================================================
# Quick Skill Program
# =============================================================================


class QuickSkillProgram(dspy.Module):
    """Streamlined program for rapid skill generation.

    Optimized for speed with minimal validation, useful for
    bootstrap and development scenarios.
    """

    def __init__(self, quality_assured: bool = False):
        super().__init__()
        if quality_assured:
            self.understand = UnderstandModuleQA()
            self.plan = PlanModuleQA()
            self.edit = EditModuleQA()
        else:
            self.understand = UnderstandModule()
            self.plan = PlanModule()
            self.edit = EditModule()

    def forward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: Callable[[str], Any],
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Quick skill generation (Steps 1-2-4 only).

        Skips initialization and packaging for speed.
        """

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            understanding = self.understand(
                task_description=task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else dspy.settings.lm
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

        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            # Serialize parent_skills to JSON string (EditModule expects str, not list)
            parent_skills_str = json_serialize(understanding["parent_skills"])
            # Serialize composition_strategy to JSON string if it's a dict
            composition_strategy_str = json_serialize(plan.get("composition_strategy", ""))
            content = self.edit(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills_str,
                composition_strategy=composition_strategy_str,
            )

        return {"understanding": understanding, "plan": plan, "content": content}

    async def aforward(
        self,
        task_description: str,
        existing_skills: list,
        taxonomy_structure: dict,
        parent_skills_getter: Callable[[str], Any],
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict:
        """Async quick skill generation."""

        # Step 1: UNDERSTAND
        lm = task_lms.get("skill_understand") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            understanding = await self.understand.acall(
                task_description=task_description,
                existing_skills=existing_skills,
                taxonomy_structure=taxonomy_structure,
            )

        # Step 2: PLAN
        lm = task_lms.get("skill_plan") if task_lms else dspy.settings.lm
        parent_skills = parent_skills_getter(understanding["taxonomy_path"])
        with dspy.context(lm=lm):
            plan = await self.plan.acall(
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

        lm = task_lms.get("skill_edit") if task_lms else dspy.settings.lm
        with dspy.context(lm=lm):
            # Serialize parent_skills to JSON string (EditModule expects str, not list)
            parent_skills_str = json_serialize(understanding["parent_skills"])
            # Serialize composition_strategy to JSON string if it's a dict
            composition_strategy_str = json_serialize(plan.get("composition_strategy", ""))
            content = await self.edit.acall(
                skill_skeleton=skeleton["skill_skeleton"],
                parent_skills=parent_skills_str,
                composition_strategy=composition_strategy_str,
            )

        return {"understanding": understanding, "plan": plan, "content": content}


# =============================================================================
# Program Factory
# =============================================================================


def create_skill_creation_program(
    quality_assured: bool = False,
    quick: bool = False,
) -> dspy.Module:
    """Create a skill creation program.

    Args:
        quality_assured: Use Refine/BestOfN for higher quality
        quick: Use QuickSkillProgram (skips init/package)

    Returns:
        Appropriate program instance
    """
    if quick:
        return QuickSkillProgram(quality_assured=quality_assured)
    return SkillCreationProgram(quality_assured=quality_assured)
