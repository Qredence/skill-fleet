"""
Intent analysis module.

Uses AnalyzeIntent signature to determine skill purpose,
target audience, and success criteria.
"""

import time
from typing import Any

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.intent import AnalyzeIntent


class AnalyzeIntentModule(BaseModule):
    """
    Analyze user intent from task description.

    Uses AnalyzeIntent signature to extract:
    - Purpose and problem statement
    - Target audience
    - Value proposition
    - Skill type and scope
    - Success criteria

    Example:
        module = AnalyzeIntentModule()
        result = module.forward(
            task_description="Build a React component library",
            requirements={"domain": "technical", "topics": ["react", "components"]}
        )
        # Returns: dspy.Prediction with:
        #   purpose="Help developers build consistent UIs",
        #   problem_statement="Managing UI consistency across apps",
        #   target_audience="Frontend developers",
        #   value_proposition="Pre-built, tested components",
        #   skill_type="how_to",
        #   scope="Component creation and management",
        #   success_criteria=["User can create components", ...]

    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeIntent)

    async def aforward(
        self, task_description: str, requirements: dict | None = None
    ) -> dspy.Prediction:  # type: ignore[override]
        """Async intent analysis using DSPy `acall`."""
        start_time = time.time()

        clean_task = self._sanitize_input(task_description)
        clean_requirements = self._sanitize_input(str(requirements or {}))

        try:
            result = await self.analyze.acall(
                task_description=clean_task,
                requirements=clean_requirements,
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Intent analysis failed: {e}. Using heuristic fallback.")
            result = None

        output = (
            {
                "purpose": result.purpose,
                "problem_statement": result.problem_statement,
                "target_audience": result.target_audience,
                "value_proposition": result.value_proposition,
                "skill_type": result.skill_type,
                "scope": result.scope,
                "success_criteria": result.success_criteria
                if isinstance(result.success_criteria, list)
                else [],
            }
            if result is not None
            else {
                "purpose": f"Help with: {clean_task[:80]}",
                "problem_statement": f"User needs guidance on: {clean_task[:80]}",
                "target_audience": "Developers",
                "value_proposition": "Provides a clear, actionable workflow.",
                "skill_type": "how_to",
                "scope": "Focuses on practical steps and best practices.",
                "success_criteria": ["User can complete the task"],
                "fallback": True,
            }
        )
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))

        required = ["purpose", "problem_statement", "target_audience", "skill_type"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("purpose", "Learn " + clean_task[:50])
            output.setdefault("problem_statement", "Need to " + clean_task[:50])
            output.setdefault("target_audience", "Developers")
            output.setdefault("skill_type", "how_to")

        purpose = str(output.get("purpose", ""))
        skill_type = str(output.get("skill_type", ""))

        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task_description": clean_task[:100]},
            outputs={"skill_type": skill_type, "purpose": purpose[:50]},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def forward(self, *args: Any, **kwargs: Any) -> dspy.Prediction:
        """Sync wrapper that delegates to aforward()."""
        from dspy.utils.syncify import run_async

        if "task_description" in kwargs:
            task_description = kwargs["task_description"]
        elif args:
            task_description = args[0]
        else:
            raise TypeError("forward() missing required argument: 'task_description'")

        requirements = kwargs.get("requirements", args[1] if len(args) > 1 else None)
        return run_async(
            self.aforward(task_description=task_description, requirements=requirements)
        )
