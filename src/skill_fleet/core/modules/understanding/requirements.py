"""
Requirements gathering module.

Uses GatherRequirements signature to extract structured requirements
from user task descriptions.
"""

import time
from typing import Any

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.requirements import GatherRequirements


class GatherRequirementsModule(BaseModule):
    """
    Gather requirements from task description.

    Uses GatherRequirements signature to extract:
    - Domain (technical, cognitive, domain_knowledge, tool, meta)
    - Topics to cover
    - Constraints and preferences
    - Ambiguities requiring clarification
    - Target expertise level

    Example:
        module = GatherRequirementsModule()
        result = module.forward(
            task_description="Build a React component library",
            user_context={"experience": "intermediate"}
        )
        # Returns: dspy.Prediction with:
        #   domain="technical",
        #   category="frontend",
        #   target_level="intermediate",
        #   topics=["react", "components", "typescript"],
        #   constraints=["TypeScript", "production ready"],
        #   ambiguities=["Unclear if SSR is needed"]

    """

    def __init__(self):
        super().__init__()
        self.gather = dspy.ChainOfThought(GatherRequirements)

    async def aforward(
        self, task_description: str, user_context: dict | None = None
    ) -> dspy.Prediction:  # type: ignore[override]
        """Async requirements gathering using DSPy `acall`."""
        start_time = time.time()

        clean_task = self._sanitize_input(task_description)
        clean_context = self._sanitize_input(str(user_context or {}))

        try:
            result = await self.gather.acall(
                task_description=clean_task, user_context=clean_context
            )
        except Exception as e:
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Requirements gathering failed: {e}. Using heuristic fallback.")
            result = None

        output = self._result_to_output(result, clean_task)
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))

        required = ["domain", "category", "target_level", "topics"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("domain", "technical")
            output.setdefault("category", "general")
            output.setdefault("target_level", "intermediate")
            output.setdefault("topics", ["general"])

        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task_description": clean_task[:100]},
            outputs={k: v for k, v in output.items() if k != "ambiguities"},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def forward(self, task_description: str, user_context: dict | None = None) -> dspy.Prediction:  # type: ignore[override]
        """
        Gather requirements from task description.

        Args:
            task_description: User's task description
            user_context: Optional user context (preferences, history, etc.)

        Returns:
            dspy.Prediction with structured requirements:
            - domain: Primary domain
            - category: Specific category
            - target_level: Target expertise level
            - topics: List of topics to cover
            - constraints: Technical constraints
            - ambiguities: Unclear aspects requiring HITL

        """
        start_time = time.time()

        # Sanitize inputs
        clean_task = self._sanitize_input(task_description)
        clean_context = self._sanitize_input(str(user_context or {}))

        # Execute signature
        try:
            result = self.gather(
                task_description=clean_task,
                user_context=clean_context,
            )
        except Exception as e:
            # If the LM is not configured (or signature output parsing fails), fall back to a
            # lightweight heuristic extraction so workflows and tests can proceed.
            if not llm_fallback_enabled():
                raise
            self.logger.warning(f"Requirements gathering failed: {e}. Using heuristic fallback.")
            result = None

        output = self._result_to_output(result, clean_task)
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))

        # Validate
        required = ["domain", "category", "target_level", "topics"]
        if not self._validate_result(output, required):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("domain", "technical")
            output.setdefault("category", "general")
            output.setdefault("target_level", "intermediate")
            output.setdefault("topics", ["general"])

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task_description": clean_task[:100]},
            outputs={k: v for k, v in output.items() if k != "ambiguities"},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _result_to_output(self, result: Any, clean_task: str) -> dict[str, Any]:
        """Normalize DSPy result into a stable dict output (with optional fallback)."""
        if result is None:
            import re

            task_lower = clean_task.lower()
            words = [w for w in re.findall(r"[a-z0-9]+", task_lower) if len(w) >= 3]
            topics = list(dict.fromkeys(words[:5])) or ["general"]
            suggested_skill_name = "-".join(topics[:4])[:60].strip("-") or "unnamed-skill"
            trigger_phrases = [clean_task[:50]] if clean_task else ["use this skill"]
            description = (
                f"Use when user asks about: {', '.join(topics[:3])}."
                if topics
                else "Use when user asks about this topic."
            )
            return {
                "domain": "technical",
                "category": "general",
                "target_level": "intermediate",
                "topics": topics,
                "constraints": [],
                "ambiguities": [],
                "description": description,
                "suggested_skill_name": suggested_skill_name,
                "trigger_phrases": trigger_phrases,
                "negative_triggers": [],
                "skill_category": "other",
                "requires_mcp": False,
                "suggested_mcp_server": "",
                "fallback": True,
            }

        return {
            "domain": result.domain,
            "category": result.category,
            "target_level": result.target_level,
            "topics": result.topics if isinstance(result.topics, list) else [result.topics],
            "constraints": result.constraints if isinstance(result.constraints, list) else [],
            "ambiguities": result.ambiguities if isinstance(result.ambiguities, list) else [],
            "description": result.description,
            "suggested_skill_name": result.suggested_skill_name,
            "trigger_phrases": result.trigger_phrases
            if isinstance(result.trigger_phrases, list)
            else [result.trigger_phrases],
            "negative_triggers": result.negative_triggers
            if isinstance(result.negative_triggers, list)
            else [result.negative_triggers],
            "skill_category": result.skill_category,
            "requires_mcp": result.requires_mcp,
            "suggested_mcp_server": result.suggested_mcp_server,
        }
