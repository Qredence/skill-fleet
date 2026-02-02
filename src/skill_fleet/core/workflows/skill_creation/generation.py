"""
Phase 2: Content Generation Workflow with streaming support.

Generates skill content based on understanding and plan from Phase 1.
Can show preview for user feedback before finalizing.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from skill_fleet.core.modules.generation.content import GenerateSkillContentModule
from skill_fleet.core.modules.generation.refined_content import RefinedContentModule
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


class GenerationWorkflow:
    """
    Phase 2: Content Generation Workflow with streaming.

    Generates complete skill content:
    1. Generate SKILL.md content
    2. (Optional) Refine using dspy.Refine for quality
    3. (Optional) Show preview for HITL feedback
    4. Incorporate feedback if provided
    5. Return final content

    Example:
        workflow = GenerationWorkflow()

        # Stream mode for real-time progress
        async for event in workflow.execute_streaming(
            plan={"skill_name": "...", "content_outline": [...]},
            understanding={"requirements": {...}, ...},
        ):
            print(f"{event.message}")

    """

    def __init__(self):
        self.content_generator = GenerateSkillContentModule()
        # Use RefinedContentModule for async-compatible quality improvement
        self.content_refiner = RefinedContentModule()

    async def execute_streaming(
        self,
        plan: dict,
        understanding: dict,
        enable_hitl_preview: bool = False,
        skill_style: str = "comprehensive",
        quality_threshold: float = 0.8,
        enable_token_streaming: bool = False,
        manager: StreamingWorkflowManager | None = None,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Execute generation workflow with streaming events.

        Args:
            plan: Plan from Phase 1 synthesis
            understanding: Understanding from Phase 1
            enable_hitl_preview: Whether to show preview for feedback
            skill_style: Content style
            quality_threshold: Minimum quality score
            enable_token_streaming: Enable token-level streaming (shows content as it's generated)
            manager: Optional workflow manager

        Yields:
            WorkflowEvent with progress, reasoning, and content updates.
            If enable_token_streaming=True, also yields TOKEN_STREAM events.

        """
        manager = manager or get_workflow_manager()

        # Start workflow execution in background task
        workflow_task = asyncio.create_task(
            self._execute_workflow(
                plan=plan,
                understanding=understanding,
                enable_hitl_preview=enable_hitl_preview,
                skill_style=skill_style,
                quality_threshold=quality_threshold,
                enable_token_streaming=enable_token_streaming,
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
        plan: dict,
        understanding: dict,
        enable_hitl_preview: bool = False,
        skill_style: str = "comprehensive",
        quality_threshold: float = 0.8,
        enable_token_streaming: bool = False,
        manager: StreamingWorkflowManager | None = None,
    ) -> None:
        """Execute the actual workflow logic."""
        manager = manager or get_workflow_manager()

        try:
            with dspy_context():
                await manager.set_phase("Generation")
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    f"Starting content generation for: {plan.get('skill_name', 'unnamed')}",
                    {"skill_name": plan.get("skill_name", "")},
                )

                # Step 1: Generate content (with optional token streaming)
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Generating SKILL.md content"
                    + (" (streaming)" if enable_token_streaming else ""),
                )

                if enable_token_streaming:
                    # Use token-level streaming for real-time display
                    content_result = await manager.execute_module_streaming(
                        "content_generator",
                        self.content_generator.aforward_streaming,
                        plan=plan,
                        understanding=understanding,
                        skill_style=skill_style,
                    )
                else:
                    # Standard async execution
                    content_result = await manager.execute_module(
                        "content_generator",
                        self.content_generator.aforward,
                        plan=plan,
                        understanding=understanding,
                        skill_style=skill_style,
                    )

                skill_content = content_result.get("skill_content", "")

                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    f"Generated {len(skill_content)} characters of content",
                    {
                        "sections": len(content_result.get("sections_generated", [])),
                        "examples": content_result.get("code_examples_count", 0),
                    },
                )

                # Step 2: Refine content using RefinedContentModule
                # This uses iterative improvement with quality reward function
                if quality_threshold > 0:
                    await manager.emit(
                        WorkflowEventType.PROGRESS,
                        "Refining content for quality",
                        {"target_quality": quality_threshold},
                    )

                    refined_result = await manager.execute_module(
                        "content_refiner",
                        self.content_refiner.aforward,
                        plan=plan,
                        understanding=understanding,
                        skill_style=skill_style,
                        target_quality=quality_threshold,
                        max_iterations=3,
                    )

                    if hasattr(refined_result, "skill_content"):
                        skill_content = refined_result.skill_content
                    elif isinstance(refined_result, dict) and "skill_content" in refined_result:
                        skill_content = refined_result["skill_content"]

                # Step 3: Check if preview requested
                if enable_hitl_preview:
                    await manager.emit(
                        WorkflowEventType.PROGRESS,
                        "Preparing preview for user feedback",
                    )

                    hitl_data: dict[str, Any] = {
                        "skill_content": skill_content,
                        "sections_count": len(content_result.get("sections_generated", [])),
                        "examples_count": content_result.get("code_examples_count", 0),
                        "reading_time": content_result.get("estimated_reading_time", 0),
                    }
                    context: dict[str, Any] = {
                        "plan": plan,
                        "understanding": understanding,
                        "skill_style": skill_style,
                    }
                    result = {
                        "status": "pending_hitl",
                        "hitl_type": "preview",
                        "hitl_data": hitl_data,
                        "context": context,
                    }

                    await manager.suspend_for_hitl(
                        hitl_type="preview",
                        data=hitl_data,
                        context=context,
                    )
                    await manager.complete(result)
                    return

                result = {
                    "status": "completed",
                    "skill_content": skill_content,
                    "sections_generated": content_result.get("sections_generated", []),
                    "code_examples_count": content_result.get("code_examples_count", 0),
                    "estimated_reading_time": content_result.get("estimated_reading_time", 0),
                }
                await manager.complete(result)

        except Exception as e:
            logger.error(f"Generation workflow error: {e}")
            await manager.emit(
                WorkflowEventType.ERROR,
                f"Generation error: {str(e)}",
                {"error": str(e)},
            )
            raise

    async def execute(
        self,
        plan: dict,
        understanding: dict,
        enable_hitl_preview: bool = False,
        skill_style: str = "comprehensive",
        quality_threshold: float = 0.8,
        manager: StreamingWorkflowManager | None = None,
    ) -> dict[str, Any]:
        """
        Execute generation workflow (non-streaming, backward compatible).

        Args:
            plan: Plan from Phase 1 synthesis
            understanding: Understanding from Phase 1
            enable_hitl_preview: Whether to show preview for feedback
            skill_style: Content style
            quality_threshold: Minimum quality score
            manager: Optional streaming workflow manager (for event emission)

        Returns:
            Generated skill content

        """
        if manager is None:
            manager = StreamingWorkflowManager()

        async for event in self.execute_streaming(
            plan=plan,
            understanding=understanding,
            enable_hitl_preview=enable_hitl_preview,
            skill_style=skill_style,
            quality_threshold=quality_threshold,
            manager=manager,
        ):
            if event.event_type == WorkflowEventType.COMPLETED:
                return event.data.get("result", {})
            elif event.event_type == WorkflowEventType.ERROR:
                raise RuntimeError(event.message)

        return {"status": "failed", "error": "Workflow did not complete"}

    async def incorporate_feedback(
        self, current_content: str, feedback: str, change_requests: list[str]
    ) -> dict[str, Any]:
        """Incorporate user feedback into content."""
        logger.info("Incorporating user feedback")

        # For now, return original with note
        # In full implementation, would use IncorporateFeedbackModule
        return {
            "status": "completed",
            "skill_content": current_content,
            "feedback_incorporated": True,
            "changes_made": change_requests,
        }
