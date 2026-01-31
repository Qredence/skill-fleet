"""
Phase 1: Understanding Workflow.

Orchestrates understanding modules to gather requirements,
analyze intent, find taxonomy path, identify dependencies,
and synthesize a complete plan. Uses async operations for better performance.
Can suspend for HITL clarification if ambiguities are detected.
"""

import asyncio
import logging
from typing import Any

from skill_fleet.core.modules.hitl.questions import GenerateClarifyingQuestionsModule
from skill_fleet.core.modules.understanding.dependencies import AnalyzeDependenciesModule
from skill_fleet.core.modules.understanding.intent import AnalyzeIntentModule
from skill_fleet.core.modules.understanding.plan import SynthesizePlanModule
from skill_fleet.core.modules.understanding.requirements import GatherRequirementsModule
from skill_fleet.core.modules.understanding.taxonomy import FindTaxonomyPathModule
from skill_fleet.core.modules.validation.structure import ValidateStructureModule

logger = logging.getLogger(__name__)


class UnderstandingWorkflow:
    """
    Phase 1: Understanding & Planning Workflow.

    Orchestrates understanding modules asynchronously:
    1. Gather requirements (always first - may trigger HITL)
    2. Analyze intent, find taxonomy path, analyze dependencies (parallel)
    3. Synthesize complete plan using ReAct

    Can suspend for HITL clarification if ambiguities found.

    Example:
        workflow = UnderstandingWorkflow()
        result = await workflow.execute(
            task_description="Build a React component library",
            user_context={"experience": "intermediate"}
        )
        # Returns complete understanding + plan or HITL checkpoint

    """

    def __init__(self):
        self.requirements = GatherRequirementsModule()
        self.intent = AnalyzeIntentModule()
        self.taxonomy = FindTaxonomyPathModule()
        self.dependencies = AnalyzeDependenciesModule()
        self.plan = SynthesizePlanModule()
        self.hitl_questions = GenerateClarifyingQuestionsModule()
        self.structure_validator = ValidateStructureModule()

    async def execute(
        self,
        task_description: str,
        user_context: dict | None = None,
        taxonomy_structure: dict | None = None,
        existing_skills: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute understanding workflow asynchronously.

        Args:
            task_description: User's task description
            user_context: Optional user context (preferences, history)
            taxonomy_structure: Current taxonomy structure
            existing_skills: List of existing skill paths

        Returns:
            Dictionary with either:
            - Complete understanding + synthesized plan
            - HITL checkpoint (if ambiguities detected)

        """
        logger.info(f"Starting understanding workflow for: {task_description[:50]}...")

        # Step 1: Gather requirements (blocking - must complete first)
        logger.debug("Step 1: Gathering requirements")
        requirements = await self.requirements.aforward(
            task_description=task_description, user_context=user_context or {}
        )

        # Step 1b: Validate structure early to catch common errors
        logger.debug("Step 1b: Validating skill structure")
        structure_validation = self.structure_validator(
            skill_name=requirements.get("suggested_skill_name", ""),
            description=requirements.get("description", ""),
            skill_content="",
        )

        if not structure_validation["overall_valid"]:
            logger.info("Structure validation failed, suspending for fixes")
            return await self._suspend_for_structure_fix(
                task_description=task_description,
                requirements=requirements,
                user_context=user_context or {},
                validation=structure_validation,
            )

        # Check if clarification needed
        if self._needs_clarification(requirements):
            logger.info(f"Ambiguities detected: {len(requirements.get('ambiguities', []))} items")
            return await self._suspend_for_clarification(
                task_description=task_description,
                requirements=requirements,
                user_context=user_context or {},
            )

        # Step 2-4: Run in parallel for better performance
        logger.debug("Steps 2-4: Analyzing intent, taxonomy, and dependencies (parallel)")
        intent_task = self.intent.aforward(
            task_description=task_description, requirements=requirements
        )
        taxonomy_task = self.taxonomy.aforward(
            task_description=task_description,
            requirements=requirements,
            taxonomy_structure=taxonomy_structure or {},
            existing_skills=existing_skills or [],
        )
        dependencies_task = self.dependencies.aforward(
            task_description=task_description,
            intent_analysis={},  # Will be updated after intent completes
            taxonomy_path="",  # Will be updated after taxonomy completes
            existing_skills=existing_skills or [],
        )

        # Wait for all parallel tasks
        intent, taxonomy, dependencies = await asyncio.gather(
            intent_task, taxonomy_task, dependencies_task
        )

        # Update dependencies with intent and taxonomy info
        dependencies = await self.dependencies.aforward(
            task_description=task_description,
            intent_analysis=intent,
            taxonomy_path=taxonomy.get("recommended_path", ""),
            existing_skills=existing_skills or [],
        )

        # Step 5: Synthesize plan using ReAct
        logger.debug("Step 5: Synthesizing plan with ReAct")
        plan = await self.plan.aforward(
            requirements=requirements,
            intent_analysis=intent,
            taxonomy_analysis=taxonomy,
            dependency_analysis=dependencies,
        )

        logger.info("Understanding workflow completed successfully")

        return {
            "status": "completed",
            "requirements": requirements,
            "intent": intent,
            "taxonomy": taxonomy,
            "dependencies": dependencies,
            "plan": plan,
        }

    def _needs_clarification(self, requirements: dict) -> bool:
        """
        Determine if HITL clarification is needed.

        Args:
            requirements: Requirements dictionary

        Returns:
            True if ambiguities exist and are significant

        """
        ambiguities = requirements.get("ambiguities", [])

        # No ambiguities = no clarification needed
        if not ambiguities:
            return False

        # Filter out minor ambiguities (less than 10 chars)
        significant_ambiguities = [a for a in ambiguities if len(str(a)) > 10]

        # Need clarification if we have significant ambiguities
        if len(significant_ambiguities) > 0:
            logger.debug(f"Significant ambiguities: {significant_ambiguities}")
            return True

        return False

    async def _suspend_for_clarification(
        self,
        task_description: str,
        requirements: dict,
        user_context: dict,
    ) -> dict[str, Any]:
        """
        Suspend workflow for HITL clarification with relevant questions.

        Args:
            task_description: Original task description
            requirements: Requirements with ambiguities
            user_context: User context

        Returns:
            HITL checkpoint with targeted questions

        """
        logger.info("Suspending for HITL clarification")

        # Get ambiguities
        ambiguities = requirements.get("ambiguities", [])

        # Generate targeted questions based on ambiguities
        questions_result = await self.hitl_questions.aforward(
            task_description=task_description,
            ambiguities=ambiguities,
            initial_analysis=str(requirements),
        )

        # Create follow-up context with suggestions
        follow_up_context = self._create_follow_up_context(requirements, questions_result)

        return {
            "status": "pending_user_input",
            "hitl_type": "clarify",
            "hitl_data": {
                "questions": questions_result.get("questions", []),
                "priority": questions_result.get("priority", "important"),
                "rationale": questions_result.get("rationale", ""),
                "follow_up_context": follow_up_context,
            },
            "context": {
                "requirements": requirements,
                "user_context": user_context,
                "partial_understanding": {
                    "domain": requirements.get("domain"),
                    "topics": requirements.get("topics"),
                    "target_level": requirements.get("target_level"),
                },
            },
        }

    def _create_follow_up_context(
        self, requirements: dict, questions_result: dict
    ) -> dict[str, Any]:
        """
        Create context for follow-up after HITL.

        Args:
            requirements: Current requirements
            questions_result: Questions generated

        Returns:
            Context dictionary for resuming workflow

        """
        return {
            "expected_improvements": [
                "Clearer topic definitions",
                "Specific technology choices",
                "Scope boundaries",
            ],
            "resume_strategy": "Re-run understanding with clarified requirements",
            "questions_asked": len(questions_result.get("questions", [])),
            "critical_gaps": requirements.get("ambiguities", [])[:3],  # Top 3 gaps
        }

    async def _suspend_for_structure_fix(
        self,
        task_description: str,
        requirements: dict,
        user_context: dict,
        validation: dict,
    ) -> dict[str, Any]:
        """
        Suspend workflow for structure fixes.

        Args:
            task_description: Original task description
            requirements: Current requirements
            user_context: User context
            validation: Structure validation results with errors

        Returns:
            HITL checkpoint with structure issues and suggested fixes

        """
        logger.info("Suspending for structure fix HITL")

        # Combine all errors
        all_issues = (
            validation.get("name_errors", [])
            + validation.get("description_errors", [])
            + validation.get("security_issues", [])
        )

        # Generate suggested fixes
        suggested_fixes = self._generate_structure_fixes(validation, requirements)

        return {
            "status": "pending_user_input",
            "hitl_type": "structure_fix",
            "hitl_data": {
                "issues": all_issues,
                "warnings": validation.get("description_warnings", []),
                "suggested_fixes": suggested_fixes,
                "current_values": {
                    "skill_name": requirements.get("suggested_skill_name", ""),
                    "description": requirements.get("description", ""),
                },
            },
            "context": {
                "requirements": requirements,
                "user_context": user_context,
                "validation": validation,
                "can_proceed": validation["overall_valid"],
            },
        }

    def _generate_structure_fixes(self, validation: dict, requirements: dict) -> list[dict]:
        """
        Generate suggested fixes for structure issues.

        Args:
            validation: Structure validation results
            requirements: Current requirements

        Returns:
            List of fix suggestions with before/after examples

        """
        fixes = []

        # Name fixes
        if not validation.get("name_valid"):
            current_name = requirements.get("suggested_skill_name", "")
            # Convert to kebab-case suggestion
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

        # Description fixes
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
