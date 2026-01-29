"""
Intent analysis module.

Uses AnalyzeIntent signature to determine skill purpose,
target audience, and success criteria.
"""

import time
from typing import Any

import dspy

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
        # Returns: {
        #   "purpose": "Help developers build consistent UIs",
        #   "problem_statement": "Managing UI consistency across apps",
        #   "target_audience": "Frontend developers",
        #   "value_proposition": "Pre-built, tested components",
        #   "skill_type": "how_to",
        #   "scope": "Component creation and management",
        #   "success_criteria": ["User can create components", ...]
        # }

    """

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeIntent)

    def forward(  # type: ignore[override]
        self, task_description: str, requirements: dict | None = None
    ) -> dict[str, Any]:
        """
        Analyze intent from task description.

        Args:
            task_description: User's task description
            requirements: Optional requirements from GatherRequirementsModule

        Returns:
            Dictionary with intent analysis:
            - purpose: Why this skill exists
            - problem_statement: Specific problem addressed
            - target_audience: Who needs this skill
            - value_proposition: Unique value provided
            - skill_type: Type of skill (how_to, reference, etc.)
            - scope: What's included/excluded
            - success_criteria: Measurable success criteria

        """
        start_time = time.time()

        # Sanitize inputs
        clean_task = self._sanitize_input(task_description)
        clean_requirements = self._sanitize_input(str(requirements or {}))

        # Execute signature
        result = self.analyze(
            task_description=clean_task,
            requirements=clean_requirements,
        )

        # Transform to structured output
        output = {
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

        # Validate
        required = ["purpose", "problem_statement", "target_audience", "skill_type"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("purpose", "Learn " + clean_task[:50])
            output.setdefault("problem_statement", "Need to " + clean_task[:50])
            output.setdefault("target_audience", "Developers")
            output.setdefault("skill_type", "how_to")

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task_description": clean_task[:100]},
            outputs={"skill_type": output["skill_type"], "purpose": output["purpose"][:50]},
            duration_ms=duration_ms,
        )

        return output
