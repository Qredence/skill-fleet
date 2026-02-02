"""
Dependencies analysis module.

Uses AnalyzeDependencies signature to identify prerequisites,
complementary skills, and potential conflicts.
"""

import time
from typing import Any

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled, with_llm_fallback
from skill_fleet.common.utils import timed_execution
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.dependencies import AnalyzeDependencies


class AnalyzeDependenciesModule(BaseModule):
    """
    Analyze skill dependencies.

    Uses AnalyzeDependencies signature to identify:
    - Prerequisite skills (hard requirements)
    - Complementary skills (enhancements)
    - Conflicting skills (incompatible)
    - Missing prerequisites (need to create)

    Example:
        module = AnalyzeDependenciesModule()
        result = module.forward(
            task_description="Build a React component library",
            intent_analysis={"purpose": "...", "skill_type": "how_to"},
            taxonomy_path="technical/frontend/react-components",
            existing_skills=["technical/frontend/react-basics", "technical/javascript"]
        )
        # Returns: {
        #   "prerequisite_skills": ["technical/frontend/react-basics: ..."],
        #   "complementary_skills": ["technical/testing: ..."],
        #   "conflicting_skills": [],
        #   "missing_prerequisites": [],
        #   "dependency_rationale": "..."
        # }

    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeDependencies)

    @timed_execution()
    @with_llm_fallback(default_return=None)
    async def aforward(
        self,
        task_description: str,
        intent_analysis: dict | None = None,
        taxonomy_path: str = "",
        existing_skills: list[str] | None = None,
    ) -> dspy.Prediction:
        """Async dependency analysis using DSPy `acall`."""
        clean_task = self._sanitize_input(task_description)
        clean_intent = self._sanitize_input(str(intent_analysis or {}))
        clean_path = self._sanitize_input(taxonomy_path)
        clean_existing = existing_skills if existing_skills else []

        result = await self.analyze.acall(
            task_description=clean_task,
            intent_analysis=clean_intent,
            taxonomy_path=clean_path,
            existing_skills=clean_existing,
        )

        output = (
            {
                "prerequisite_skills": result.prerequisite_skills
                if isinstance(result.prerequisite_skills, list)
                else [],
                "complementary_skills": result.complementary_skills
                if isinstance(result.complementary_skills, list)
                else [],
                "conflicting_skills": result.conflicting_skills
                if isinstance(result.conflicting_skills, list)
                else [],
                "missing_prerequisites": result.missing_prerequisites
                if isinstance(result.missing_prerequisites, list)
                else [],
                "dependency_rationale": result.dependency_rationale,
            }
            if result is not None
            else {
                "prerequisite_skills": [],
                "complementary_skills": [],
                "conflicting_skills": [],
                "missing_prerequisites": [],
                "dependency_rationale": "Fallback dependencies due to analysis failure.",
                "fallback": True,
            }
        )
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))

        required = ["prerequisite_skills", "complementary_skills", "dependency_rationale"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("prerequisite_skills", [])
            output.setdefault("complementary_skills", [])
            output.setdefault("dependency_rationale", "No dependency analysis available")

        prerequisite_skills = output.get("prerequisite_skills", [])
        if not isinstance(prerequisite_skills, list):
            prerequisite_skills = []
        complementary_skills = output.get("complementary_skills", [])
        if not isinstance(complementary_skills, list):
            complementary_skills = []

        return self._to_prediction(**output)

    def forward(
        self,
        task_description: str | None = None,
        intent_analysis: dict | None = None,
        taxonomy_path: str = "",
        existing_skills: list[str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> dspy.Prediction:
        """
        Analyze dependencies for skill.

        Args:
            task_description: User's task description
            intent_analysis: Intent analysis from AnalyzeIntentModule
            taxonomy_path: Selected taxonomy path
            existing_skills: List of existing skill identifiers
            *args: Positional arguments for BaseModule compatibility.
            **kwargs: Additional keyword arguments for compatibility.

        Returns:
            dspy.Prediction with dependency analysis:
            - prerequisite_skills: Hard prerequisites
            - complementary_skills: Optional enhancements
            - conflicting_skills: Incompatible skills
            - missing_prerequisites: Skills that need creation
            - dependency_rationale: Explanation

        """
        # Support BaseModule.forward-style calls where task_description may be
        # passed positionally and this override must remain compatible.
        if task_description is None and args:
            # Use the first positional argument as the task description.
            task_description = str(args[0])

        if task_description is None:
            raise ValueError("task_description must be provided")
        start_time = time.time()

        # Sanitize inputs
        clean_task = self._sanitize_input(task_description)
        clean_intent = self._sanitize_input(str(intent_analysis or {}))
        clean_path = self._sanitize_input(taxonomy_path)
        clean_existing = existing_skills if existing_skills else []

        # Execute signature
        try:
            result = self.analyze(
                task_description=clean_task,
                intent_analysis=clean_intent,
                taxonomy_path=clean_path,
                existing_skills=clean_existing,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Dependency analysis failed: {e}. Using fallback dependencies.")
            result = None

        # Transform to structured output
        if result is None:
            output = {
                "prerequisite_skills": [],
                "complementary_skills": [],
                "conflicting_skills": [],
                "missing_prerequisites": [],
                "dependency_rationale": "Fallback dependencies due to analysis failure.",
            }
        else:
            output = {
                "prerequisite_skills": result.prerequisite_skills
                if isinstance(result.prerequisite_skills, list)
                else [],
                "complementary_skills": result.complementary_skills
                if isinstance(result.complementary_skills, list)
                else [],
                "conflicting_skills": result.conflicting_skills
                if isinstance(result.conflicting_skills, list)
                else [],
                "missing_prerequisites": result.missing_prerequisites
                if isinstance(result.missing_prerequisites, list)
                else [],
                "dependency_rationale": result.dependency_rationale,
            }
            if hasattr(result, "reasoning"):
                output.setdefault("reasoning", str(result.reasoning))

        # Validate
        required = ["prerequisite_skills", "complementary_skills", "dependency_rationale"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("prerequisite_skills", [])
            output.setdefault("complementary_skills", [])
            output.setdefault("dependency_rationale", "No dependency analysis available")

        prerequisite_skills = output.get("prerequisite_skills", [])
        if not isinstance(prerequisite_skills, list):
            prerequisite_skills = []
        complementary_skills = output.get("complementary_skills", [])
        if not isinstance(complementary_skills, list):
            complementary_skills = []

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "task_description": clean_task[:100],
                "taxonomy_path": clean_path,
            },
            outputs={
                "prerequisites_count": len(prerequisite_skills),
                "complementary_count": len(complementary_skills),
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)
