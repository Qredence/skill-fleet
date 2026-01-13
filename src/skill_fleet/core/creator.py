"""High-level skill creation orchestrator.

This module provides the main interface for skill creation,
coordinating DSPy programs, taxonomy operations, and feedback.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import dspy

from ..common.utils import json_serialize
from ..taxonomy.manager import TaxonomyManager
from ..validators.skill_validator import SkillValidator
from .dspy.modules import IterateModule
from .dspy.programs import SkillCreationProgram, SkillRevisionProgram
from .hitl import FeedbackHandler, create_feedback_handler
from .optimization import WorkflowOptimizer

logger = logging.getLogger(__name__)


class TaxonomySkillCreator(dspy.Module):
    """High-level orchestrator for skill creation.

    Coordinates DSPy programs, taxonomy management, validation,
    and human feedback to create skills end-to-end.
    """

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        feedback_handler: FeedbackHandler | None = None,
        validator: SkillValidator | None = None,
        lm: dspy.LM | None = None,
        optimizer: WorkflowOptimizer | None = None,
        verbose: bool = True,
        reasoning_tracer: Any | None = None,  # TODO: Type properly when available
    ):
        """Initialize skill creator.

        Args:
            taxonomy_manager: Taxonomy management instance
            feedback_handler: Handler for human feedback (default: auto-approval)
            validator: Skill validator (creates default if None)
            lm: Language model (uses dspy.settings if None)
            optimizer: Workflow optimizer for caching (optional)
            verbose: Whether to print progress
            reasoning_tracer: Optional tracer for Phase 1/2 reasoning visibility
        """
        super().__init__()
        self.taxonomy = taxonomy_manager
        self.optimizer = optimizer
        self.verbose = verbose
        self.reasoning_tracer = reasoning_tracer

        # Initialize feedback handler
        self.feedback_handler = feedback_handler or create_feedback_handler("auto")

        # Initialize validator
        self.validator = validator or SkillValidator(skills_root=taxonomy_manager.skills_root)

        # Configure LM
        if lm:
            dspy.settings.configure(lm=lm)

        # Initialize DSPy programs
        self.creation_program = SkillCreationProgram()
        self.revision_program = SkillRevisionProgram()
        self.iterate_module = IterateModule()

        # Statistics
        self.stats = {"total": 0, "successful": 0, "failed": 0, "avg_iterations": 0.0}

    def forward(
        self,
        task_description: str,
        user_context: dict[str, Any],
        max_iterations: int = 3,
        auto_approve: bool = False,
        feedback_type: str = "interactive",
        feedback_kwargs: dict[str, Any] | None = None,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict[str, Any]:
        """Execute full skill creation workflow (DSPy compatibility).

        Args:
            task_description: User's task or capability requirement
            user_context: Dict with user_id and other context
            max_iterations: Maximum HITL iterations
            auto_approve: If True, use auto-approval (shortcut for feedback_type="auto")
            feedback_type: Type of feedback handler ("auto", "cli", "interactive", "webhook")
            feedback_kwargs: Additional kwargs for feedback handler (e.g., min_rounds, max_rounds)
            task_lms: Dictionary of task-specific LMs

        Returns:
            Result dictionary with status and metadata
        """
        # Determine feedback handler based on parameters
        if auto_approve:
            self.feedback_handler = create_feedback_handler("auto")
        else:
            handler_kwargs = feedback_kwargs or {}
            self.feedback_handler = create_feedback_handler(feedback_type, **handler_kwargs)

        return self.create_skill(
            task_description=task_description,
            user_context=user_context,
            max_iterations=max_iterations,
            task_lms=task_lms,
        )

    def create_skill(
        self,
        task_description: str,
        user_context: dict[str, Any],
        max_iterations: int = 3,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict[str, Any]:
        """Create a new skill from task description.

        Args:
            task_description: User's task or capability requirement
            user_context: Dict with user_id and other context
            max_iterations: Maximum HITL iterations
            task_lms: Dictionary of task-specific LMs

        Returns:
            Result dictionary with status and metadata
        """
        self.stats["total"] += 1

        if self.verbose:
            self._print_header("Skill Creation")
            print(f"📝 Task: {task_description}")
            print(f"👤 User: {user_context.get('user_id', 'unknown')}\n")

        try:
            # Execute main creation program
            result = self.creation_program(
                task_description=task_description,
                existing_skills=self.taxonomy.get_mounted_skills(
                    user_context.get("user_id", "default")
                ),
                taxonomy_structure=self.taxonomy.get_relevant_branches(task_description),
                parent_skills_getter=self.taxonomy.get_parent_skills,
                task_lms=task_lms,
            )

            # Preserve task_description in result for feedback handler
            result["task_description"] = task_description

            understanding = result["understanding"]
            plan = result["plan"]
            package = result["package"]

            # Check if skill exists
            if self.taxonomy.skill_exists(understanding["taxonomy_path"]):
                return {
                    "status": "exists",
                    "path": understanding["taxonomy_path"],
                    "message": "Skill already exists in taxonomy",
                }

            # Validate dependencies
            if not self._validate_plan(plan):
                return {"status": "error", "message": "Invalid dependencies or circular reference"}

            # Check initial validation
            report = package["validation_report"]
            passed_statuses = ["passed", "validated", "approved", "success"]
            is_passed = (
                report.get("passed", False) or report.get("status", "").lower() in passed_statuses
            )

            if not is_passed:
                return {"status": "validation_failed", "errors": report.get("errors", [])}

            # HITL iteration
            approval = self._iterate_for_approval(
                result=result, max_iterations=max_iterations, task_lms=task_lms
            )

            if approval["status"] == "approved":
                self.stats["successful"] += 1

                # Track usage
                self.taxonomy.track_usage(
                    skill_id=approval["skill_id"],
                    user_id=user_context.get("user_id", "default"),
                    success=True,
                    metadata={
                        "event_type": "creation",
                        "quality_score": approval.get("quality_score", 0.0),
                    },
                )
            else:
                self.stats["failed"] += 1

            return approval

        except Exception as e:
            logger.exception("Error creating skill")
            self.stats["failed"] += 1
            return {"status": "error", "message": str(e)}

    def _validate_plan(self, plan: dict[str, Any]) -> bool:
        """Validate skill plan (dependencies, circular refs)."""

        dependencies = plan.get("dependencies", [])
        dep_ids = []
        for d in dependencies:
            if isinstance(d, str):
                dep_ids.append(d)
            elif hasattr(d, "skill_id"):
                dep_ids.append(d.skill_id)
            elif isinstance(d, dict):
                dep_ids.append(d.get("skill_id"))

        dep_ids = [d for d in dep_ids if d]  # filter out None

        # Check dependencies exist
        valid, missing = self.taxonomy.validate_dependencies(dep_ids)
        if not valid:
            if self.verbose:
                print(f"⚠️ Missing dependencies: {missing}")
            # We allow missing dependencies with a warning (matching previous behavior)
            pass

        # Check for cycles
        skill_id = plan["skill_metadata"].get("skill_id")
        if skill_id:
            has_cycle, path = self.taxonomy.detect_circular_dependencies(skill_id, dep_ids)
            if has_cycle:
                if self.verbose:
                    print(f"❌ Circular dependency: {' -> '.join(path)}")
                return False

        return True

    def _iterate_for_approval(
        self,
        result: dict[str, Any],
        max_iterations: int,
        task_lms: dict[str, dspy.LM] | None = None,
    ) -> dict[str, Any]:
        """Iterate with human feedback until approved or max iterations."""

        understanding = result["understanding"]
        plan = result["plan"]
        skeleton = result["skeleton"]
        content = result["content"]
        package = result["package"]

        total_iters = 0
        for iteration in range(1, max_iterations + 1):
            total_iters = iteration
            if self.verbose:
                print(f"\n📋 Iteration {iteration}/{max_iterations}")

            # Get human feedback
            # Merge quality_score into validation_report for display
            validation_with_score = {
                **package["validation_report"],
                "quality_score": package.get("quality_score", 0.0),
            }
            feedback = self.feedback_handler.get_feedback(
                package["packaging_manifest"],
                validation_with_score,
                skill_content=content.get("skill_content", ""),
                task_description=result.get("task_description", ""),
            )

            # Process feedback
            lm = task_lms.get("skill_validate") if task_lms else None
            with dspy.context(lm=lm):
                decision = self.iterate_module(
                    packaged_skill=package["packaging_manifest"],
                    validation_report=package["validation_report"],
                    human_feedback=feedback,
                )

            if decision["approval_status"] == "approved":
                # Prepare extra files for registration
                extra_files = {
                    "capability_implementations": content.get("capability_implementations"),
                    "usage_examples": content.get("usage_examples"),
                    "integration_tests": package.get("integration_tests"),
                    "best_practices": content.get("best_practices"),
                    "integration_guide": content.get("integration_guide"),
                    "resource_requirements": plan.get("resource_requirements"),
                }

                # Register skill
                success = self.taxonomy.register_skill(
                    path=understanding["taxonomy_path"],
                    metadata=plan["skill_metadata"],
                    content=content["skill_content"],
                    evolution=decision["evolution_metadata"],
                    extra_files=extra_files,
                )

                if success:
                    if self.verbose:
                        print("✅ Skill approved and registered!")

                    return {
                        "status": "approved",
                        "skill_id": plan["skill_metadata"]["skill_id"],
                        "path": understanding["taxonomy_path"],
                        "version": plan["skill_metadata"]["version"],
                        "quality_score": package["quality_score"],
                        "iterations": iteration,
                    }
                else:
                    return {"status": "error", "message": "Registration failed"}

            elif decision["approval_status"] == "needs_revision":
                if iteration < max_iterations:
                    # Revise and repackage
                    if self.verbose:
                        print("🔄 Revising skill...")

                    revised = self.revision_program(
                        skeleton=skeleton,
                        parent_skills=understanding["parent_skills"],
                        composition_strategy=plan["composition_strategy"],
                        plan=plan,
                        taxonomy_path=understanding["taxonomy_path"],
                        revision_feedback=json_serialize(decision["revision_plan"]),
                        task_lms=task_lms,
                    )

                    content = revised["content"]
                    package = revised["package"]
                else:
                    if self.verbose:
                        print("❌ Maximum iterations reached without approval.")

            else:  # rejected
                return {
                    "status": "rejected",
                    "reason": decision["revision_plan"],
                    "iterations": iteration,
                }

        return {
            "status": "max_iterations",
            "message": f"Not approved after {max_iterations} iterations",
            "iterations": total_iters,
        }

    def _print_header(self, title: str):
        """Print formatted header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def get_stats(self) -> dict[str, Any]:
        """Get creation statistics."""
        return self.stats.copy()


# Convenience function
def create_skill(
    task_description: str,
    user_id: str = "default",
    skills_root: str = "./skills",
    verbose: bool = True,
) -> dict[str, Any]:
    """Convenience function for quick skill creation."""
    from ..taxonomy.manager import TaxonomyManager

    taxonomy = TaxonomyManager(Path(skills_root))
    creator = TaxonomySkillCreator(taxonomy_manager=taxonomy, verbose=verbose)

    return creator.create_skill(
        task_description=task_description, user_context={"user_id": user_id}
    )
