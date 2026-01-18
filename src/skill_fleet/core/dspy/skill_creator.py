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
from ...common.paths import default_config_root
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
from .signatures.hitl import GenerateHITLQuestions

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
    """Load the SKILL.md authoring template for generation guidance."""
    candidates: list[Path] = []

    # Allow a local override in the current working directory.
    candidates.append(Path.cwd() / "config" / "templates" / "SKILL_md_template.md")
    candidates.append(default_config_root() / "templates" / "SKILL_md_template.md")

    for path in candidates:
        if not path.exists():
            continue
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

    def __init__(
        self,
        quality_assured: bool = True,
        hitl_enabled: bool = True,
        load_optimized: bool = True,
    ):
        super().__init__()
        self.hitl_enabled = hitl_enabled
        self._optimized_loaded = False

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

        # Try to load optimized program if available
        if load_optimized:
            self._try_load_optimized()

    def _try_load_optimized(self) -> bool:
        """Try to load an optimized version of this program.

        Looks for optimized programs in config/optimized/ directory.
        Returns True if an optimized program was loaded.
        """
        optimized_roots = [
            Path.cwd() / "config" / "optimized",
            default_config_root() / "optimized",
        ]

        candidates: list[Path] = []
        for root in optimized_roots:
            if not root.exists():
                continue
            candidates.extend(sorted(root.glob("skill_creator*.json"), reverse=True))

        if not candidates:
            return False

        try:
            # Load the most recent optimized program
            program_file = candidates[0]
            self.load(str(program_file))
            self._optimized_loaded = True
            logger.info(f"Loaded optimized program from {program_file}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load optimized program: {e}")
            return False

    @property
    def is_optimized(self) -> bool:
        """Check if this program is using optimized weights."""
        return self._optimized_loaded

    async def aforward(
        self,
        task_description: str,
        user_context: dict[str, Any],
        taxonomy_structure: str,
        existing_skills: str,
        hitl_callback: Callable[[str, dict[str, Any]], Any] | None = None,
        progress_callback: Callable[[str, str], None] | None = None,
        **kwargs,
    ) -> SkillCreationResult:
        """Execute the 3-phase skill creation workflow with HITL.

        Args:
            task_description: Initial user task
            user_context: Context about the user
            taxonomy_structure: Current taxonomy tree
            existing_skills: List of existing skills
            hitl_callback: Async callback for human interaction
            progress_callback: Callback for progress updates (phase, message)

        Returns:
            SkillCreationResult with content and metadata
        """
        try:
            # ============================================================
            # PHASE 1: UNDERSTANDING & PLANNING
            # ============================================================
            logger.info("Starting Phase 1: Understanding & Planning")
            if progress_callback:
                progress_callback(
                    "understanding", "Starting Phase 1: Analyzing task requirements..."
                )

            # HITL 1.1: Clarification (if needed)
            user_clarifications = ""
            if self.hitl_enabled and hitl_callback:
                # Initial analysis for clarification
                if progress_callback:
                    progress_callback(
                        "understanding", "Gathering initial requirements from task description..."
                    )
                requirements = await self.phase1.gather_requirements.aforward(task_description)

                if requirements["ambiguities"]:
                    # Generate focused questions using class-based signature
                    hitl_module = dspy.ChainOfThought(GenerateHITLQuestions)
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
            if progress_callback:
                progress_callback(
                    "understanding",
                    "Analyzing intent, finding taxonomy path, and checking dependencies...",
                )
            p1_result = await self.phase1.aforward(
                task_description=task_description,
                user_context=str(user_context),
                taxonomy_structure=taxonomy_structure,
                existing_skills=existing_skills,
            )
            if progress_callback:
                progress_callback(
                    "understanding", "Phase 1 complete. Preparing confirmation summary..."
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

                # Confirm with user - include rationale/thinking for transparency
                confirmation = await hitl_callback(
                    "confirm",
                    {
                        "summary": summary["summary"],
                        "path": p1_result["taxonomy"]["recommended_path"],
                        "rationale": p1_result["plan"].get("rationale", "")
                        or p1_result["taxonomy"].get("path_rationale", ""),
                        "key_assumptions": summary.get("key_assumptions", []),
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
            if progress_callback:
                progress_callback("generation", "Starting Phase 2: Preparing content generation...")

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
            if progress_callback:
                progress_callback(
                    "generation", "Generating SKILL.md content, examples, and best practices..."
                )
            p2_result = await self.phase2.aforward(
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                generation_instructions=generation_instructions,
                parent_skills_content="",  # TODO: Fetch parent content if needed
                dependency_summaries=str(p1_result["dependencies"]),
            )
            if progress_callback:
                progress_callback("generation", "Content generated. Preparing preview...")

            # HITL 2.1: Preview & Feedback
            if self.hitl_enabled and hitl_callback:
                preview = await self.preview_generator.aforward(
                    skill_content=p2_result["skill_content"],
                    metadata=str(p1_result["plan"]["skill_metadata"]),
                )

                # Show preview to user - include rationale/thinking for transparency
                feedback = await hitl_callback(
                    "preview",
                    {
                        "content": preview["preview"],
                        "highlights": preview["highlights"],
                        "rationale": p2_result.get("rationale", ""),
                    },
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
            if progress_callback:
                progress_callback("validation", "Starting Phase 3: Validating skill content...")

            # Execute Phase 3
            if progress_callback:
                progress_callback(
                    "validation", "Checking agentskills.io compliance and content quality..."
                )
            p3_result = await self.phase3.aforward(
                skill_content=p2_result["skill_content"],
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                validation_rules="Standard agentskills.io compliance",
                target_level=p1_result["requirements"]["target_level"],
            )
            if progress_callback:
                progress_callback("validation", "Validation complete. Preparing final report...")

            # HITL 3.1: Final Validation Review
            if self.hitl_enabled and hitl_callback:
                max_rounds = 3
                rounds_used = 0
                while True:
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

                    if (
                        isinstance(final_decision, dict)
                        and final_decision.get("action") == "cancel"
                    ):
                        return SkillCreationResult(status="cancelled")

                    if (
                        isinstance(final_decision, dict)
                        and final_decision.get("action") == "refine"
                    ):
                        rounds_used += 1
                        if rounds_used >= max_rounds:
                            return SkillCreationResult(
                                status="failed",
                                error="Validation refinement exceeded maximum iterations",
                            )

                        # Manual refinement request
                        p3_result = await self.phase3.aforward(
                            skill_content=p3_result["refined_content"],
                            skill_metadata=p1_result["plan"]["skill_metadata"],
                            content_plan=p1_result["plan"]["content_plan"],
                            validation_rules="Standard agentskills.io compliance",
                            user_feedback=final_decision.get("feedback", ""),
                            target_level=p1_result["requirements"]["target_level"],
                        )
                        continue

                    # proceed (or unknown action)
                    break

            # Build extra_files from Phase 2 results for subdirectory content
            extra_files = {
                "usage_examples": p2_result.get("usage_examples", []),
                "best_practices": p2_result.get("best_practices", []),
                "integration_tests": p2_result.get("test_cases", []),
            }

            return SkillCreationResult(
                status="completed",
                skill_content=p3_result["refined_content"],
                metadata=p1_result["plan"]["skill_metadata"],
                validation_report=p3_result["validation_report"],
                quality_assessment=p3_result["quality_assessment"],
                extra_files=extra_files,
            )

        except Exception as e:
            logger.error(f"Error in SkillCreationProgram: {e}", exc_info=True)
            return SkillCreationResult(status="failed", error=str(e))

    def forward(self, *args, **kwargs) -> SkillCreationResult:
        """Sync wrapper."""
        return run_async(lambda: self.aforward(*args, **kwargs))
