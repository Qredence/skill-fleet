"""
Phase 1: Understanding Workflow with streaming support.

Orchestrates understanding modules to gather requirements,
analyze intent, find taxonomy path, identify dependencies,
and synthesize a complete plan. Uses async operations for better performance.
Can suspend for HITL clarification if ambiguities are detected.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from skill_fleet.core.modules.hitl.questions import GenerateClarifyingQuestionsModule
from skill_fleet.core.modules.understanding.dependencies import AnalyzeDependenciesModule
from skill_fleet.core.modules.understanding.intent import AnalyzeIntentModule
from skill_fleet.core.modules.understanding.plan import SynthesizePlanModule
from skill_fleet.core.modules.understanding.requirements import GatherRequirementsModule
from skill_fleet.core.modules.understanding.taxonomy import FindTaxonomyPathModule
from skill_fleet.core.modules.validation.structure import ValidateStructureModule
from skill_fleet.core.workflows.streaming import (
    StreamingWorkflowManager,
    WorkflowEventType,
    get_workflow_manager,
)
from skill_fleet.dspy import dspy_context

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from skill_fleet.core.workflows.streaming import WorkflowEvent

logger = logging.getLogger(__name__)


class UnderstandingWorkflow:
    """
    Phase 1: Understanding & Planning Workflow with streaming.

    Orchestrates understanding modules asynchronously:
    1. Gather requirements (always first - may trigger HITL)
    2. Analyze intent, find taxonomy path, analyze dependencies (parallel)
    3. Synthesize complete plan

    Can suspend for HITL clarification if ambiguities found.

    Example:
        workflow = UnderstandingWorkflow()

        # Stream mode for real-time progress
        async for event in workflow.execute_streaming(
            task_description="Build a React component library"
        ):
            print(f"{event.phase}: {event.message}")

    """

    def __init__(self):
        self.requirements = GatherRequirementsModule()
        self.intent = AnalyzeIntentModule()
        self.taxonomy = FindTaxonomyPathModule()
        self.dependencies = AnalyzeDependenciesModule()
        self.plan = SynthesizePlanModule()
        self.hitl_questions = GenerateClarifyingQuestionsModule()
        self.structure_validator = ValidateStructureModule()

    async def execute_streaming(
        self,
        task_description: str,
        user_context: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
        enable_hitl_confirm: bool = False,
        user_confirmation: str = "",
        manager: StreamingWorkflowManager | None = None,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Execute understanding workflow with streaming events.

        Args:
            task_description: User's task description
            user_context: Optional user context
            taxonomy_structure: Current taxonomy structure
            existing_skills: List of existing skill paths
            enable_hitl_confirm: Enable recap + confirm/revise/cancel checkpoint after plan synthesis
            user_confirmation: Feedback from the user when revising the recap/plan
            manager: Optional workflow manager

        Yields:
            WorkflowEvent with progress, reasoning, and status updates

        """
        manager = manager or get_workflow_manager()

        # Start workflow execution in background task
        workflow_task = asyncio.create_task(
            self._execute_workflow(
                task_description=task_description,
                user_context=user_context,
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
                enable_hitl_confirm=enable_hitl_confirm,
                user_confirmation=user_confirmation,
                manager=manager,
            )
        )

        # Yield events as they are emitted
        try:
            async for event in manager.get_events():
                yield event
        finally:
            # Ensure workflow task is cleaned up
            if not workflow_task.done():
                workflow_task.cancel()
                try:
                    await workflow_task
                except asyncio.CancelledError:
                    pass

    async def _execute_workflow(
        self,
        task_description: str,
        user_context: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
        enable_hitl_confirm: bool = False,
        user_confirmation: str = "",
        manager: StreamingWorkflowManager | None = None,
    ) -> None:
        """Execute the actual workflow logic."""
        manager = manager or get_workflow_manager()

        try:
            with dspy_context():
                await manager.set_phase("Understanding")
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Starting understanding workflow",
                    {"task": task_description[:100]},
                )

                # Step 1: Gather requirements (blocking - must complete first)
                requirements = await manager.execute_module(
                    "requirements",
                    self.requirements.aforward,
                    task_description=task_description,
                    user_context=user_context or {},
                )

                # If user provided structure fixes earlier, apply them before validation/HITL.
                # This avoids a loop where the model keeps proposing an invalid name/description.
                if user_context and isinstance(user_context, dict):
                    override = user_context.get("structure_fix")
                    if isinstance(override, dict):
                        fixed_name = override.get("skill_name")
                        fixed_desc = override.get("description")
                        if isinstance(fixed_name, str) and fixed_name.strip():
                            requirements["suggested_skill_name"] = fixed_name.strip()
                        if isinstance(fixed_desc, str) and fixed_desc.strip():
                            requirements["description"] = fixed_desc.strip()

                # Step 1b: Validate structure early to catch common errors
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Validating skill structure",
                    {"skill_name": requirements.get("suggested_skill_name", "")},
                )

                structure_validation = await manager.execute_module(
                    "structure_validator",
                    self.structure_validator.aforward,
                    skill_name=requirements.get("suggested_skill_name", ""),
                    description=requirements.get("description", ""),
                    skill_content="",
                )

                if not structure_validation.get("overall_valid", True):
                    await manager.emit(
                        WorkflowEventType.PROGRESS,
                        "Structure validation failed, preparing HITL",
                        {"errors": structure_validation.get("name_errors", [])},
                    )
                    result = await self._suspend_for_structure_fix(
                        task_description=task_description,
                        requirements=requirements,
                        user_context=user_context or {},
                        validation=structure_validation,
                        manager=manager,
                    )
                    await manager.complete(result)
                    return

                # Check if clarification needed
                if self._needs_clarification(requirements):
                    await manager.emit(
                        WorkflowEventType.PROGRESS,
                        f"Ambiguities detected: {len(requirements.get('ambiguities', []))} items",
                        {"ambiguities": requirements.get("ambiguities", [])},
                    )
                    result = await self._suspend_for_clarification(
                        task_description=task_description,
                        requirements=requirements,
                        user_context=user_context or {},
                        manager=manager,
                    )
                    await manager.complete(result)
                    return

                # Steps 2-4: Run in parallel for better performance
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Analyzing intent, taxonomy, and dependencies (parallel)",
                )

                intent_task = manager.execute_module(
                    "intent_analyzer",
                    self.intent.aforward,
                    task_description=task_description,
                    requirements=requirements,
                )
                taxonomy_task = manager.execute_module(
                    "taxonomy_finder",
                    self.taxonomy.aforward,
                    task_description=task_description,
                    requirements=requirements,
                    taxonomy_structure=taxonomy_structure or {},
                    existing_skills=existing_skills or [],
                )
                dependencies_task = manager.execute_module(
                    "dependency_analyzer",
                    self.dependencies.aforward,
                    task_description=task_description,
                    intent_analysis={},
                    taxonomy_path="",
                    existing_skills=existing_skills or [],
                )

                # Wait for all parallel tasks
                intent, taxonomy, dependencies = await asyncio.gather(
                    intent_task, taxonomy_task, dependencies_task
                )

                # Update dependencies with intent and taxonomy info
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Refining dependency analysis",
                )
                dependencies = await manager.execute_module(
                    "dependency_analyzer_refined",
                    self.dependencies.aforward,
                    task_description=task_description,
                    intent_analysis=intent,
                    taxonomy_path=taxonomy.get("recommended_path", ""),
                    existing_skills=existing_skills or [],
                )

                # Step 5: Synthesize plan
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Synthesizing complete plan",
                )
                plan = await manager.execute_module(
                    "plan_synthesizer",
                    self.plan.aforward,
                    requirements=requirements,
                    intent_analysis=intent,
                    taxonomy_analysis=taxonomy,
                    dependency_analysis=dependencies,
                    user_confirmation=user_confirmation,
                )

                result = {
                    "status": "completed",
                    "requirements": requirements,
                    "intent": intent,
                    "taxonomy": taxonomy,
                    "dependencies": dependencies,
                    "plan": plan,
                }
                if enable_hitl_confirm:
                    summary = self._build_recap_summary(
                        requirements=requirements,
                        intent=intent,
                        taxonomy=taxonomy,
                        plan=plan,
                    )
                    hitl_data = {
                        "summary": summary,
                        "path": str(
                            plan.get("taxonomy_path") or taxonomy.get("recommended_path") or ""
                        ),
                        "key_assumptions": self._build_key_assumptions(
                            requirements=requirements,
                            intent=intent,
                            plan=plan,
                        ),
                    }
                    context = {
                        "requirements": requirements,
                        "intent": intent,
                        "taxonomy": taxonomy,
                        "dependencies": dependencies,
                        "plan": plan,
                    }
                    pending = {
                        "status": "pending_hitl",
                        "hitl_type": "confirm",
                        "hitl_data": hitl_data,
                        "context": context,
                        "plan": plan,
                        "requirements": requirements,
                        "intent": intent,
                        "taxonomy": taxonomy,
                        "dependencies": dependencies,
                    }
                    await manager.suspend_for_hitl(
                        hitl_type="confirm",
                        data=hitl_data,
                        context=context,
                    )
                    await manager.complete(pending)
                    return

                await manager.complete(result)

        except Exception as e:
            logger.error(f"Understanding workflow error: {e}")
            await manager.emit(
                WorkflowEventType.ERROR,
                f"Workflow error: {str(e)}",
                {"error": str(e)},
            )
            raise

    async def execute(
        self,
        task_description: str,
        user_context: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
        enable_hitl_confirm: bool = False,
        user_confirmation: str = "",
        manager: StreamingWorkflowManager | None = None,
    ) -> dict[str, Any]:
        """
        Execute understanding workflow (non-streaming, backward compatible).

        Args:
            task_description: User's task description
            user_context: Optional user context
            taxonomy_structure: Current taxonomy structure
            existing_skills: List of existing skill paths
            enable_hitl_confirm: Enable recap + confirm/revise/cancel checkpoint after plan synthesis
            user_confirmation: Feedback from the user when revising the recap/plan
            manager: Optional streaming workflow manager (for event emission)

        Returns:
            Dictionary with understanding results or HITL checkpoint

        """
        if manager is None:
            manager = StreamingWorkflowManager()

        # Consume all events and return final result
        async for event in self.execute_streaming(
            task_description=task_description,
            user_context=user_context,
            taxonomy_structure=taxonomy_structure,
            existing_skills=existing_skills,
            enable_hitl_confirm=enable_hitl_confirm,
            user_confirmation=user_confirmation,
            manager=manager,
        ):
            if event.event_type == WorkflowEventType.COMPLETED:
                return event.data.get("result", {})
            elif event.event_type == WorkflowEventType.ERROR:
                raise RuntimeError(event.message)

        return {"status": "failed", "error": "Workflow did not complete"}

    @staticmethod
    def _build_recap_summary(
        *,
        requirements: dict[str, Any],
        intent: dict[str, Any],
        taxonomy: dict[str, Any],
        plan: dict[str, Any],
    ) -> str:
        """Build a human-readable recap for the confirm step (markdown-ish plain text)."""
        skill_name = (
            plan.get("skill_name") or requirements.get("suggested_skill_name") or "unnamed-skill"
        )
        desc = plan.get("skill_description") or requirements.get("description") or ""
        path = plan.get("taxonomy_path") or taxonomy.get("recommended_path") or ""
        topics = requirements.get("topics") if isinstance(requirements.get("topics"), list) else []
        target_level = requirements.get("target_level") or ""
        scope = intent.get("scope") or ""
        criteria = (
            plan.get("success_criteria") if isinstance(plan.get("success_criteria"), list) else []
        )

        lines: list[str] = []
        lines.append(f"Skill: {skill_name}")
        if desc:
            lines.append(f"Description: {desc}")
        if path:
            lines.append(f"Taxonomy path: {path}")
        if target_level:
            lines.append(f"Target level: {target_level}")
        if topics:
            lines.append(f"Topics: {', '.join(str(t) for t in topics[:8])}")
        if scope:
            lines.append("")
            lines.append("Scope:")
            lines.extend(str(scope).splitlines())
        if criteria:
            lines.append("")
            lines.append("Success criteria:")
            for c in criteria[:8]:
                lines.append(f"- {c}")
        return "\n".join(lines).strip()

    @staticmethod
    def _build_key_assumptions(
        *, requirements: dict[str, Any], intent: dict[str, Any], plan: dict[str, Any]
    ) -> list[str]:
        assumptions: list[str] = []
        target = requirements.get("target_level")
        if target:
            assumptions.append(f"Target level is {target}.")
        constraints = requirements.get("constraints")
        if isinstance(constraints, list) and constraints:
            assumptions.append(f"Constraints: {', '.join(str(c) for c in constraints[:4])}.")
        audience = intent.get("target_audience")
        if audience:
            assumptions.append(f"Audience: {audience}.")
        style = plan.get("estimated_length")
        if style:
            assumptions.append(f"Expected length: {style}.")
        return assumptions[:6]

    def _needs_clarification(self, requirements: dict) -> bool:
        """Determine if HITL clarification is needed."""
        ambiguities = requirements.get("ambiguities", [])
        if not ambiguities:
            return False
        significant_ambiguities = [a for a in ambiguities if len(str(a)) > 10]
        return len(significant_ambiguities) > 0

    async def _suspend_for_clarification(
        self,
        task_description: str,
        requirements: dict,
        user_context: dict,
        manager: StreamingWorkflowManager,
    ) -> dict[str, Any]:
        """Suspend workflow for HITL clarification."""
        await manager.emit(
            WorkflowEventType.PROGRESS,
            "Generating clarifying questions",
        )

        ambiguities = requirements.get("ambiguities", [])
        questions_result = await manager.execute_module(
            "hitl_questions",
            self.hitl_questions.aforward,
            task_description=task_description,
            ambiguities=ambiguities,
            initial_analysis=str(requirements),
        )

        follow_up_context = self._create_follow_up_context(requirements, questions_result)

        hitl_data: dict[str, Any] = {
            "questions": questions_result.get("questions", []),
            "priority": questions_result.get("priority", "important"),
            "rationale": questions_result.get("rationale", ""),
            "follow_up_context": follow_up_context,
        }
        context: dict[str, Any] = {
            "requirements": requirements,
            "user_context": user_context,
            "partial_understanding": {
                "domain": requirements.get("domain"),
                "topics": requirements.get("topics"),
                "target_level": requirements.get("target_level"),
            },
        }
        result = {
            "status": "pending_user_input",
            "hitl_type": "clarify",
            "hitl_data": hitl_data,
            "context": context,
        }

        await manager.suspend_for_hitl(
            hitl_type="clarify",
            data=hitl_data,
            context=context,
        )

        return result

    async def _suspend_for_structure_fix(
        self,
        task_description: str,
        requirements: dict,
        user_context: dict,
        validation: dict,
        manager: StreamingWorkflowManager,
    ) -> dict[str, Any]:
        """Suspend workflow for structure fixes."""
        all_issues = (
            validation.get("name_errors", [])
            + validation.get("description_errors", [])
            + validation.get("security_issues", [])
        )

        suggested_fixes = self._generate_structure_fixes(validation, requirements)

        hitl_data: dict[str, Any] = {
            "issues": all_issues,
            "warnings": validation.get("description_warnings", []),
            "suggested_fixes": suggested_fixes,
            "current_values": {
                "skill_name": requirements.get("suggested_skill_name", ""),
                "description": requirements.get("description", ""),
            },
        }
        context: dict[str, Any] = {
            "requirements": requirements,
            "user_context": user_context,
            "validation": validation,
            "can_proceed": validation["overall_valid"],
        }
        result = {
            "status": "pending_user_input",
            "hitl_type": "structure_fix",
            "hitl_data": hitl_data,
            "context": context,
        }

        await manager.suspend_for_hitl(
            hitl_type="structure_fix",
            data=hitl_data,
            context=context,
        )

        return result

    def _create_follow_up_context(
        self, requirements: dict, questions_result: dict
    ) -> dict[str, Any]:
        """Create context for follow-up after HITL."""
        return {
            "expected_improvements": [
                "Clearer topic definitions",
                "Specific technology choices",
                "Scope boundaries",
            ],
            "resume_strategy": "Re-run understanding with clarified requirements",
            "questions_asked": len(questions_result.get("questions", [])),
            "critical_gaps": requirements.get("ambiguities", [])[:3],
        }

    def _generate_structure_fixes(self, validation: dict, requirements: dict) -> list[dict]:
        """Generate suggested fixes for structure issues."""
        fixes = []

        if not validation.get("name_valid"):
            current_name = requirements.get("suggested_skill_name", "")
            suggested_name = current_name.lower().replace(" ", "-").replace("_", "-")
            fixes.append(
                {
                    "field": "skill_name",
                    "issue": "Invalid naming",
                    "current": current_name,
                    "suggested": suggested_name,
                    "explanation": "Use kebab-case: lowercase with hyphens",
                }
            )

        if not validation.get("description_valid"):
            current_desc = requirements.get("description", "")
            trigger_phrases = requirements.get("trigger_phrases", [])

            if not validation.get("has_trigger_conditions"):
                suggested_desc = current_desc
                if trigger_phrases:
                    suggested_desc += f" Use when user asks to {trigger_phrases[0]}."
                else:
                    suggested_desc += " Use when user asks to [specific task]."

                fixes.append(
                    {
                        "field": "description",
                        "issue": "Missing trigger conditions",
                        "current": current_desc,
                        "suggested": suggested_desc,
                        "explanation": "Add 'Use when...' clause with specific trigger phrases",
                    }
                )

        return fixes
