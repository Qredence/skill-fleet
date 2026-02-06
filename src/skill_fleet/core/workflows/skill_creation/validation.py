"""
Phase 3: Validation Workflow with streaming support.

Validates generated skill content for compliance and quality.
Can refine content if quality is insufficient.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import dspy

from skill_fleet.core.modules.validation.compliance import (
    AssessQualityModule,
    RefineSkillModule,
    ValidateComplianceModule,
)
from skill_fleet.core.modules.validation.structure import ValidateStructureModule
from skill_fleet.core.modules.validation.test_cases import GenerateTestCasesModule
from skill_fleet.core.workflows.models import (
    DEFAULT_QUALITY_THRESHOLDS,
)
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


class ValidationWorkflow:
    """
    Phase 3: Validation & Quality Assurance Workflow with streaming.

    Validates skill content:
    1. Check agentskills.io compliance
    2. Assess overall quality
    3. Refine if below threshold using dspy.Refine
    4. Return validation report

    Example:
        workflow = ValidationWorkflow()

        # Stream mode for real-time progress
        async for event in workflow.execute_streaming(
            skill_content="# Skill\n...",
            plan={"success_criteria": [...]},
        ):
            print(f"{event.message}")

    """

    def __init__(self):
        self.compliance = ValidateComplianceModule()
        self.quality = AssessQualityModule()
        self.refinement = RefineSkillModule()
        self.structure_validator = ValidateStructureModule()
        self.test_generator = GenerateTestCasesModule()
        # Initialize Refine for quality-based refinement
        self.quality_refiner: dspy.Refine | None = None
        self._lock = asyncio.Lock()

    def _resolve_quality_threshold(self, quality_threshold: float | None) -> float:
        """
        Resolve the effective quality threshold.

        Args:
            quality_threshold: Optional override (uses defaults if None)

        Returns:
            Effective quality threshold

        """
        if quality_threshold is None:
            return DEFAULT_QUALITY_THRESHOLDS.validation_pass_threshold
        return quality_threshold

    async def execute_streaming(
        self,
        skill_content: str,
        plan: dict,
        taxonomy_path: str,
        enable_hitl_review: bool = False,
        quality_threshold: float | None = None,
        manager: StreamingWorkflowManager | None = None,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Execute validation workflow with streaming events.

        Args:
            skill_content: Generated SKILL.md content
            plan: Original plan with success criteria
            taxonomy_path: Expected taxonomy path
            enable_hitl_review: Whether to show for human review
            quality_threshold: Minimum quality score (uses DEFAULT_QUALITY_THRESHOLDS if None)
            manager: Optional workflow manager

        Yields:
            WorkflowEvent with validation progress and results

        """
        # Use centralized threshold if not provided
        quality_threshold = self._resolve_quality_threshold(quality_threshold)

        manager = manager or get_workflow_manager()

        # Start workflow execution in background task
        workflow_task = asyncio.create_task(
            self._execute_workflow(
                skill_content=skill_content,
                plan=plan,
                taxonomy_path=taxonomy_path,
                enable_hitl_review=enable_hitl_review,
                quality_threshold=quality_threshold,
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
        skill_content: str,
        plan: dict,
        taxonomy_path: str,
        enable_hitl_review: bool = False,
        quality_threshold: float | None = None,
        manager: StreamingWorkflowManager | None = None,
    ) -> None:
        """Execute the actual workflow logic."""
        # Use centralized threshold if not provided
        quality_threshold = self._resolve_quality_threshold(quality_threshold)

        manager = manager or get_workflow_manager()

        try:
            with dspy_context():
                await manager.set_phase("Validation")
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Starting validation workflow",
                    {"content_length": len(skill_content)},
                )

                # Step 0: Validate structure
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Validating skill structure",
                )

                skill_name = plan.get("skill_name", "")
                description = plan.get("skill_description", "")

                structure_result = await manager.execute_module(
                    "structure_validator",
                    self.structure_validator.aforward,
                    skill_name=skill_name,
                    description=description,
                    skill_content=skill_content,
                )

                # Step 1: Generate test cases
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Generating test cases",
                )

                trigger_phrases = plan.get("trigger_phrases", [])
                negative_triggers = plan.get("negative_triggers", [])
                skill_category = plan.get("skill_category", "other")

                test_cases_result = await manager.execute_module(
                    "test_generator",
                    self.test_generator.aforward,
                    skill_description=description,
                    trigger_phrases=trigger_phrases,
                    negative_triggers=negative_triggers,
                    skill_category=skill_category,
                )

                test_cases = self._to_plain_python(test_cases_result)
                if not isinstance(test_cases, dict):
                    logger.warning(f"Test generator returned non-dict: {type(test_cases).__name__}")
                    test_cases = {}

                trigger_coverage = self._assess_trigger_coverage(
                    test_cases.get("positive_tests", []), trigger_phrases
                )

                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    f"Generated {test_cases.get('total_tests', 0)} test cases",
                    {"trigger_coverage": trigger_coverage},
                )

                # Step 2: Validate compliance
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Checking agentskills.io compliance",
                )

                compliance_result = await manager.execute_module(
                    "compliance_validator",
                    self.compliance.aforward,
                    skill_content=skill_content,
                    taxonomy_path=taxonomy_path,
                )

                # Step 3: Assess quality
                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    "Assessing content quality",
                )

                quality_result = await manager.execute_module(
                    "quality_assessor",
                    self.quality.aforward,
                    skill_content=skill_content,
                    plan=plan,
                    success_criteria=plan.get("success_criteria", []),
                )

                quality_score = (
                    quality_result.get("overall_score", 0.0)
                    if isinstance(quality_result, dict)
                    else 0.0
                )

                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    f"Quality score: {quality_score:.2f}",
                    {"score": quality_score, "threshold": quality_threshold},
                )

                # Check if HITL review requested
                if enable_hitl_review:
                    result = self._create_review_checkpoint(
                        skill_content=skill_content,
                        compliance=compliance_result,
                        quality=quality_result,
                        structure=structure_result,
                        test_cases=test_cases,
                    )
                    await manager.suspend_for_hitl(
                        hitl_type="validate",
                        data=result["hitl_data"],
                        context=result["context"],
                    )
                    await manager.complete(result)
                    return

                # Step 4: Refine if needed using dspy.Refine
                (
                    final_content,
                    refinements_made,
                    refine_result,
                ) = await self._refine_if_needed(
                    skill_content=skill_content,
                    quality_result=quality_result,
                    quality_score=quality_score,
                    quality_threshold=quality_threshold,
                    manager=manager,
                )

                # Determine final status
                passed = (
                    compliance_result.get("passed", False)
                    if isinstance(compliance_result, dict)
                    else False
                ) and quality_score >= quality_threshold

                await manager.emit(
                    WorkflowEventType.PROGRESS,
                    f"Validation {'passed' if passed else 'failed'}",
                    {"passed": passed, "score": quality_score},
                )

                # Build validation report
                result = self._build_validation_result(
                    skill_content=final_content,
                    passed=passed,
                    quality_score=quality_score,
                    compliance_result=compliance_result,
                    quality_result=quality_result,
                    structure_result=structure_result,
                    test_cases=test_cases,
                    trigger_coverage=trigger_coverage,
                    refinements_made=refinements_made,
                    quality_threshold=quality_threshold,
                )

                await manager.complete(result)

        except Exception as e:
            logger.error(f"Validation workflow error: {e}")
            await manager.emit(
                WorkflowEventType.ERROR,
                f"Validation error: {str(e)}",
                {"error": str(e)},
            )
            raise

    async def execute(
        self,
        skill_content: str,
        plan: dict,
        taxonomy_path: str,
        enable_hitl_review: bool = False,
        quality_threshold: float | None = None,
        manager: StreamingWorkflowManager | None = None,
    ) -> dict[str, Any]:
        """
        Execute validation workflow (non-streaming, backward compatible).

        Args:
            skill_content: Generated SKILL.md content
            plan: Original plan with success criteria
            taxonomy_path: Expected taxonomy path
            enable_hitl_review: Whether to show for human review
            quality_threshold: Minimum quality score (uses DEFAULT_QUALITY_THRESHOLDS if None)
            manager: Optional streaming workflow manager (for event emission)

        Returns:
            Validation results

        """
        if manager is None:
            manager = StreamingWorkflowManager()

        async for event in self.execute_streaming(
            skill_content=skill_content,
            plan=plan,
            taxonomy_path=taxonomy_path,
            enable_hitl_review=enable_hitl_review,
            quality_threshold=quality_threshold,
            manager=manager,
        ):
            if event.event_type == WorkflowEventType.COMPLETED:
                return event.data.get("result", {})
            elif event.event_type == WorkflowEventType.ERROR:
                raise RuntimeError(event.message)

        return {"status": "failed", "error": "Workflow did not complete"}

    def _build_validation_result(
        self,
        skill_content: str,
        passed: bool,
        quality_score: float,
        compliance_result: Any,
        quality_result: Any,
        structure_result: Any,
        test_cases: dict,
        trigger_coverage: float,
        refinements_made: list[str],
        quality_threshold: float,
    ) -> dict[str, Any]:
        """Build comprehensive validation result."""
        # Extract errors
        errors = []
        if isinstance(compliance_result, dict) and not compliance_result.get("passed", False):
            errors.extend(compliance_result.get("issues", []))

        if isinstance(structure_result, dict) and not structure_result.get("overall_valid", False):
            errors.extend(structure_result.get("name_errors", []))
            errors.extend(structure_result.get("description_errors", []))
            errors.extend(structure_result.get("security_issues", []))

        # Extract warnings
        warnings = []
        if isinstance(quality_result, dict):
            warnings.extend(quality_result.get("weaknesses", [])[:5])
        if isinstance(structure_result, dict):
            warnings.extend(structure_result.get("description_warnings", [])[:3])

        return {
            "status": "completed" if passed else "needs_improvement",
            "passed": passed,
            "skill_content": skill_content,
            "validation_report": {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "score": quality_score,
                "errors": errors,
                "warnings": warnings,
                "checks_performed": [
                    "structure_validation",
                    "agentskills.io_compliance",
                    "quality_assessment",
                    "test_case_generation",
                    "content_refinement",
                ],
                "checks": [],
                "feedback": quality_result.get("feedback", "")
                if isinstance(quality_result, dict)
                else "",
                "structure_valid": structure_result.get("overall_valid", False)
                if isinstance(structure_result, dict)
                else False,
                "name_errors": structure_result.get("name_errors", [])
                if isinstance(structure_result, dict)
                else [],
                "description_errors": structure_result.get("description_errors", [])
                if isinstance(structure_result, dict)
                else [],
                "security_issues": structure_result.get("security_issues", [])
                if isinstance(structure_result, dict)
                else [],
                "test_cases": test_cases,
                "trigger_coverage": trigger_coverage,
                "word_count": quality_result.get("word_count", 0)
                if isinstance(quality_result, dict)
                else 0,
                "size_assessment": quality_result.get("size_assessment", "unknown")
                if isinstance(quality_result, dict)
                else "unknown",
                "verbosity_score": quality_result.get("verbosity_score", 0.0)
                if isinstance(quality_result, dict)
                else 0.0,
                "refinements_made": refinements_made,
                "validation_summary": "Passed" if passed else "Needs improvement",
            },
        }

    async def _refine_if_needed(
        self,
        *,
        skill_content: str,
        quality_result: Any,
        quality_score: float,
        quality_threshold: float,
        manager: StreamingWorkflowManager,
    ) -> tuple[str, list[str], dspy.Prediction | dict[str, Any] | None]:
        """
        Optionally refine content when below the quality threshold.

        Args:
            skill_content: Original skill content.
            quality_result: Quality assessment output.
            quality_score: Current quality score.
            quality_threshold: Required score threshold.
            manager: Workflow manager for emitting events.

        Returns:
            Tuple of (final_content, refinements_made, refine_result)

        """
        if quality_score >= quality_threshold:
            return skill_content, [], None

        await manager.emit(
            WorkflowEventType.PROGRESS,
            f"Quality {quality_score:.2f} below threshold {quality_threshold}, refining",
        )

        weakness_list = quality_result.get("weaknesses") if isinstance(quality_result, dict) else []
        if not weakness_list:
            return skill_content, [], None

        def quality_reward(kwargs: Any, pred: Any) -> float:
            """Calculate quality score for refinement."""
            content = getattr(pred, "refined_content", "")
            score = 0.5

            if len(content) > len(kwargs.get("current_content", "")) * 0.9:
                score += 0.2

            weaknesses = kwargs.get("weaknesses", [])
            if weaknesses and any(w not in content for w in weaknesses[:2]):
                score += 0.3

            return min(1.0, score)

        async with self._lock:
            if self.quality_refiner is None:
                self.quality_refiner = dspy.Refine(
                    module=self.refinement,
                    reward_fn=quality_reward,
                    N=2,
                    threshold=quality_threshold,
                )

        async def _refine_executor(**kwargs: Any) -> dspy.Prediction | dict[str, Any]:
            assert self.quality_refiner is not None
            return await asyncio.to_thread(self.quality_refiner.forward, **kwargs)

        refine_result = await manager.execute_module(
            "quality_refiner",
            _refine_executor,
            current_content=skill_content,
            weaknesses=weakness_list,
            target_score=quality_threshold,
        )

        if isinstance(refine_result, dict):
            final_content = refine_result.get("refined_content", skill_content)
            refinements_made = refine_result.get("improvements_made", [])
        elif hasattr(refine_result, "refined_content"):
            final_content = refine_result.refined_content
            refinements_made = getattr(refine_result, "improvements_made", [])
        else:
            final_content = skill_content
            refinements_made = []

        return final_content, refinements_made, refine_result

    def _create_review_checkpoint(
        self,
        skill_content: str,
        compliance: Any,
        quality: Any,
        structure: Any | None = None,
        test_cases: Any | None = None,
    ) -> dict[str, Any]:
        """Create HITL review checkpoint."""
        compliance_score = (
            compliance.get("compliance_score", 0.0) if isinstance(compliance, dict) else 0.0
        )
        quality_score = quality.get("overall_score", 0.0) if isinstance(quality, dict) else 0.0
        strengths = quality.get("strengths", [])[:3] if isinstance(quality, dict) else []
        weaknesses = quality.get("weaknesses", [])[:3] if isinstance(quality, dict) else []
        issues = compliance.get("issues", []) if isinstance(compliance, dict) else []

        passed = bool(compliance_score >= 0.9 and quality_score >= 0.75 and not issues)
        report_lines: list[str] = []
        report_lines.append(f"Compliance score: {compliance_score:.2f}")
        report_lines.append(f"Quality score: {quality_score:.2f}")
        report_lines.append("")
        if strengths:
            report_lines.append("Strengths:")
            report_lines.extend([f"- {s}" for s in strengths])
            report_lines.append("")
        if weaknesses:
            report_lines.append("Weaknesses:")
            report_lines.extend([f"- {w}" for w in weaknesses])
            report_lines.append("")
        if issues:
            report_lines.append("Compliance issues:")
            report_lines.extend([f"- {i}" for i in issues[:10]])

        hitl_data = {
            "report": "\n".join(report_lines).strip(),
            "passed": passed,
            "validation_score": round(min(compliance_score, quality_score), 3),
            "content": skill_content,
            "highlights": strengths or [],
            "issues": issues,
            "weaknesses": weaknesses,
        }

        if structure and isinstance(structure, dict):
            hitl_data["structure_valid"] = structure.get("overall_valid", False)
            hitl_data["structure_issues"] = structure.get("name_errors", []) + structure.get(
                "description_errors", []
            )

        if test_cases and isinstance(test_cases, dict):
            hitl_data["test_case_count"] = test_cases.get("total_tests", 0)
            hitl_data["test_cases_preview"] = test_cases.get("positive_tests", [])[:3]

        return {
            "status": "pending_hitl",
            "hitl_type": "validate",
            "hitl_data": hitl_data,
            "context": {
                "full_content": skill_content,
                "compliance": compliance,
                "quality": quality,
                "structure": structure,
                "test_cases": test_cases,
            },
        }

    def _assess_trigger_coverage(
        self, positive_tests: list[str], trigger_phrases: list[str]
    ) -> float:
        """Assess how well test cases cover trigger phrases."""
        if not trigger_phrases:
            return 0.0

        covered = 0
        for phrase in trigger_phrases:
            phrase_lower = phrase.lower()
            for test in positive_tests:
                if phrase_lower in test.lower():
                    covered += 1
                    break

        return covered / len(trigger_phrases)

    def _to_plain_python(self, value: Any) -> Any:
        """Convert structured objects to JSON-serializable Python types."""
        if value is None:
            return None
        if isinstance(value, dict):
            return {k: self._to_plain_python(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._to_plain_python(v) for v in value]
        if isinstance(value, tuple):
            return [self._to_plain_python(v) for v in value]
        if hasattr(value, "model_dump"):
            try:
                return self._to_plain_python(value.model_dump(mode="json"))
            except Exception:
                return self._to_plain_python(value.model_dump())
        if hasattr(value, "toDict"):
            try:
                return self._to_plain_python(value.toDict())
            except Exception:
                return value
        return value
