"""Main SkillCreationProgram for the reworked architecture.

This program orchestrates the 3-phase workflow with integrated HITL:
1. Phase 1: Understanding & Planning (HITL clarifying questions + confirmation)
2. Phase 2: Content Generation (HITL preview + feedback)
3. Phase 3: Validation & Refinement (HITL results + iteration)

Supports a flexible HITL callback interface for CLI, API, or automated modes.
All phases support async execution.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import dspy

from ...common.async_utils import run_async
from ...common.paths import find_repo_root
from ..models import SkillCreationResult
from .modules.hitl import (
    ConfirmUnderstandingModule,
    FeedbackAnalyzerModule,
    HITLStrategyModule,
    PreviewGeneratorModule,
    ReadinessAssessorModule,
    RefinementPlannerModule,
    ValidationFormatterModule,
)
from .modules.phase1_understanding import Phase1UnderstandingModule
from .modules.phase2_generation import Phase2GenerationModule
from .modules.phase3_validation import Phase3ValidationModule

logger = logging.getLogger(__name__)


def _extract_hitl_text_response(response: Any) -> str:
    """Extract a human-readable text response from HITL callback payloads.

    The API/CLI HITL layer typically sends dict payloads like:
      {"answers": {"response": "..."}}
      {"response": "..."}

    This helper keeps the core program resilient to minor payload-shape changes.
    """
    if response is None:
        return ""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        answers = response.get("answers")
        if isinstance(answers, dict):
            direct = answers.get("response")
            if isinstance(direct, str):
                return direct
            for value in answers.values():
                if isinstance(value, str) and value.strip():
                    return value
        for key in ("response", "answer", "feedback"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return str(response)


def _load_skill_md_template() -> str | None:
    """Load the SKILL.md authoring template (repo-local) for generation guidance."""
    candidates: list[Path] = []
    for root in (find_repo_root(Path.cwd()), find_repo_root(Path(__file__).resolve())):
        if root:
            candidates.append(root / "config" / "templates" / "SKILL_md_template.md")

    for path in candidates:
        if path.exists():
            raw = path.read_text(encoding="utf-8")
            # Strip the large leading {{!-- ... --}} comment block (mustache comment),
            # keeping only the renderable portion of the template.
            marker = "## --}}"
            if marker in raw:
                raw = raw.split(marker, 1)[1].lstrip()
            return raw
    return None


class SkillCreationProgram(dspy.Module):
    """Complete 3-phase skill creation orchestrator with integrated HITL."""

    def __init__(self, quality_assured: bool = True, hitl_enabled: bool = True):
        super().__init__()
        self.hitl_enabled = hitl_enabled

        # Phase Orchestrators
        self.phase1 = Phase1UnderstandingModule()
        self.phase2 = Phase2GenerationModule(quality_assured=quality_assured)
        self.phase3 = Phase3ValidationModule()

        # HITL Utility Modules
        self.hitl_strategy = HITLStrategyModule()
        self.readiness = ReadinessAssessorModule()
        self.confirm_understanding = ConfirmUnderstandingModule()
        self.preview_generator = PreviewGeneratorModule()
        self.feedback_analyzer = FeedbackAnalyzerModule()
        self.validation_formatter = ValidationFormatterModule()
        self.refinement_planner = RefinementPlannerModule()

    async def aforward(
        self,
        task_description: str,
        user_context: dict[str, Any],
        taxonomy_structure: str,
        existing_skills: str,
        hitl_callback: Callable[[str, dict[str, Any]], Any] | None = None,
        **kwargs,
    ) -> SkillCreationResult:
        """Execute the 3-phase skill creation workflow with HITL.

        Args:
            task_description: Initial user task
            user_context: Context about the user
            taxonomy_structure: Current taxonomy tree
            existing_skills: List of existing skills
            hitl_callback: Async callback for human interaction

        Returns:
            SkillCreationResult with content and metadata
        """
        try:
            # ============================================================
            # PHASE 1: UNDERSTANDING & PLANNING
            # ============================================================
            logger.info("Starting Phase 1: Understanding & Planning")

            # HITL 1.1: Clarification (if needed)
            user_clarifications = ""
            if self.hitl_enabled and hitl_callback:
                # Initial analysis for clarification
                requirements = await self.phase1.gather_requirements.aforward(task_description)

                if requirements["ambiguities"]:
                    # Generate focused questions
                    hitl_module = dspy.ChainOfThought("requirements, task -> questions")
                    # Note: Using dspy.settings.lm if not provided
                    q_result = await hitl_module.acall(
                        requirements=json.dumps(requirements),
                        task=task_description,
                    )

                    # Ask user via callback
                    clarifications = await hitl_callback(
                        "clarify",
                        {
                            "questions": q_result.questions,
                            "rationale": getattr(q_result, "rationale", ""),
                        },
                    )
                    if (
                        isinstance(clarifications, dict)
                        and clarifications.get("action") == "cancel"
                    ):
                        return SkillCreationResult(status="cancelled")

                    user_clarifications = _extract_hitl_text_response(clarifications).strip()
                    if user_clarifications:
                        task_description = (
                            f"{task_description}\n\nClarifications: {user_clarifications}"
                        )

            # Execute Phase 1 analysis
            p1_result = await self.phase1.aforward(
                task_description=task_description,
                user_context=str(user_context),
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
            )

            # HITL 1.2: Confirmation
            if self.hitl_enabled and hitl_callback:
                # ConfirmUnderstanding signature expects `dependencies: list[str]`.
                # Phase 1 dependency analysis may return structured DependencyRef objects.
                raw_deps = p1_result.get("dependencies", {}).get("prerequisite_skills", [])
                dependencies: list[str] = []
                if isinstance(raw_deps, list):
                    for dep in raw_deps:
                        if hasattr(dep, "skill_id"):
                            dependencies.append(str(dep.skill_id))
                        elif isinstance(dep, dict):
                            dependencies.append(str(dep.get("skill_id") or dep.get("name") or dep))
                        else:
                            dependencies.append(str(dep))

                summary = await self.confirm_understanding.aforward(
                    task_description=task_description,
                    user_clarifications=user_clarifications,
                    intent_analysis=str(p1_result["intent"]),
                    taxonomy_path=p1_result["taxonomy"]["recommended_path"],
                    dependencies=dependencies,
                )

                # Confirm with user
                confirmation = await hitl_callback(
                    "confirm",
                    {
                        "summary": summary["summary"],
                        "path": p1_result["taxonomy"]["recommended_path"],
                    },
                )

                if confirmation.get("action") == "revise":
                    # Loop back or adjust
                    task_description = (
                        f"{task_description}\n\nRevision request: {confirmation.get('feedback')}"
                    )
                    return await self.aforward(
                        task_description,
                        user_context,
                        taxonomy_structure,
                        existing_skills,
                        hitl_callback,
                        **kwargs,
                    )
                elif confirmation.get("action") == "cancel":
                    return SkillCreationResult(status="cancelled")

            # ============================================================
            # PHASE 2: CONTENT GENERATION
            # ============================================================
            logger.info("Starting Phase 2: Content Generation")

            generation_instructions = p1_result["plan"]["generation_instructions"]
            skill_md_template = _load_skill_md_template()
            if skill_md_template:
                generation_instructions = (
                    f"{generation_instructions}\n\n"
                    "Follow this SKILL.md template structure (mustache placeholders indicate intent; "
                    "render to normal markdown with valid YAML frontmatter):\n\n"
                    f"{skill_md_template}"
                )

            # Execute Phase 2 generation
            p2_result = await self.phase2.aforward(
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                generation_instructions=generation_instructions,
                parent_skills_content="",  # TODO: Fetch parent content if needed
                dependency_summaries=str(p1_result["dependencies"]),
            )

            # HITL 2.1: Preview & Feedback
            if self.hitl_enabled and hitl_callback:
                preview = await self.preview_generator.aforward(
                    skill_content=p2_result["skill_content"],
                    metadata=str(p1_result["plan"]["skill_metadata"]),
                )

                # Show preview to user
                feedback = await hitl_callback(
                    "preview", {"content": preview["preview"], "highlights": preview["highlights"]}
                )

                if isinstance(feedback, dict) and feedback.get("action") == "cancel":
                    return SkillCreationResult(status="cancelled")

                if isinstance(feedback, dict) and feedback.get("action") == "refine":
                    # Analyze feedback and re-run Phase 2 refinement
                    analysis = await self.feedback_analyzer.aforward(
                        user_feedback=feedback.get("feedback", ""),
                        current_content=p2_result["skill_content"],
                    )

                    p2_result = await self.phase2.aforward(
                        skill_metadata=p1_result["plan"]["skill_metadata"],
                        content_plan=p1_result["plan"]["content_plan"],
                        generation_instructions=generation_instructions,
                        parent_skills_content="",
                        dependency_summaries=str(p1_result["dependencies"]),
                        user_feedback=feedback.get("feedback", ""),
                        change_requests=str(analysis["change_requests"]),
                    )

            # ============================================================
            # PHASE 3: VALIDATION & REFINEMENT
            # ============================================================
            logger.info("Starting Phase 3: Validation & Refinement")

            # Execute Phase 3
            p3_result = await self.phase3.aforward(
                skill_content=p2_result["skill_content"],
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                validation_rules="Standard agentskills.io compliance",
                target_level=p1_result["requirements"]["target_level"],
            )

            # HITL 3.1: Final Validation Review
            if self.hitl_enabled and hitl_callback:
                report = await self.validation_formatter.aforward(
                    validation_report=str(p3_result["validation_report"]),
                    skill_content=p3_result["refined_content"],
                )

                final_decision = await hitl_callback(
                    "validate",
                    {
                        "report": report["formatted_report"],
                        "passed": p3_result["validation_report"].passed,
                    },
                )

                if isinstance(final_decision, dict) and final_decision.get("action") == "cancel":
                    return SkillCreationResult(status="cancelled")

                if isinstance(final_decision, dict) and final_decision.get("action") == "refine":
                    # Manual refinement request
                    p3_result = await self.phase3.aforward(
                        skill_content=p3_result["refined_content"],
                        skill_metadata=p1_result["plan"]["skill_metadata"],
                        content_plan=p1_result["plan"]["content_plan"],
                        validation_rules="Standard agentskills.io compliance",
                        user_feedback=final_decision.get("feedback", ""),
                        target_level=p1_result["requirements"]["target_level"],
                    )

            return SkillCreationResult(
                status="completed",
                skill_content=p3_result["refined_content"],
                metadata=p1_result["plan"]["skill_metadata"],
                validation_report=p3_result["validation_report"],
                quality_assessment=p3_result["quality_assessment"],
            )

        except Exception as e:
            logger.error(f"Error in SkillCreationProgram: {e}", exc_info=True)
            return SkillCreationResult(status="failed", error=str(e))

    def forward(self, *args, **kwargs) -> SkillCreationResult:
        """Sync wrapper."""
        return run_async(lambda: self.aforward(*args, **kwargs))
