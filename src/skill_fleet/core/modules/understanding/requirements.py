"""
Requirements gathering module.

Uses GatherRequirements signature to extract structured requirements
from user task descriptions.
"""

import re
import time
from typing import Any

import dspy

from skill_fleet.common.llm_fallback import llm_fallback_enabled, with_llm_fallback
from skill_fleet.common.utils import timed_execution
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding.requirements import GatherRequirements

# Default values for missing fields
DEFAULT_DOMAIN = "technical"
DEFAULT_CATEGORY = "general"
DEFAULT_TARGET_LEVEL = "intermediate"
DEFAULT_TOPICS = ["general"]

# Required fields for validation
REQUIRED_FIELDS = ["domain", "category", "target_level", "topics"]


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

    def _ensure_list(self, value: Any) -> list:
        """Ensure value is a list."""
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [value]

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        """Normalize DSPy result into a stable dict output."""
        if result is None:
            return self._create_fallback_output("")

        return {
            "domain": getattr(result, "domain", DEFAULT_DOMAIN),
            "category": getattr(result, "category", DEFAULT_CATEGORY),
            "target_level": getattr(result, "target_level", DEFAULT_TARGET_LEVEL),
            "topics": self._ensure_list(getattr(result, "topics", DEFAULT_TOPICS)),
            "constraints": self._ensure_list(getattr(result, "constraints", [])),
            "ambiguities": self._ensure_list(getattr(result, "ambiguities", [])),
            "description": getattr(result, "description", ""),
            "suggested_skill_name": getattr(result, "suggested_skill_name", ""),
            "trigger_phrases": self._ensure_list(getattr(result, "trigger_phrases", [])),
            "negative_triggers": self._ensure_list(getattr(result, "negative_triggers", [])),
            "skill_category": getattr(result, "skill_category", "other"),
            "requires_mcp": getattr(result, "requires_mcp", False),
            "suggested_mcp_server": getattr(result, "suggested_mcp_server", ""),
        }

    def _create_fallback_output(self, clean_task: str) -> dict[str, Any]:
        """Create fallback output when DSPy fails or returns None."""
        task_lower = clean_task.lower()
        words = [w for w in re.findall(r"[a-z0-9]+", task_lower) if len(w) >= 3]
        topics = list(dict.fromkeys(words[:5])) or DEFAULT_TOPICS
        suggested_skill_name = "-".join(topics[:4])[:60].strip("-") or "unnamed-skill"
        trigger_phrases = [clean_task[:50]] if clean_task else ["use this skill"]
        description = (
            f"Use when user asks about: {', '.join(topics[:3])}."
            if topics
            else "Use when user asks about this topic."
        )

        return {
            "domain": DEFAULT_DOMAIN,
            "category": DEFAULT_CATEGORY,
            "target_level": DEFAULT_TARGET_LEVEL,
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

    def _validate_and_fill_defaults(self, output: dict[str, Any]) -> dict[str, Any]:
        """Validate output and fill in any missing required fields with defaults."""
        if not self._validate_result(output, REQUIRED_FIELDS):
            self.logger.warning("Result missing required fields, using defaults")
            output.setdefault("domain", DEFAULT_DOMAIN)
            output.setdefault("category", DEFAULT_CATEGORY)
            output.setdefault("target_level", DEFAULT_TARGET_LEVEL)
            output.setdefault("topics", DEFAULT_TOPICS.copy())
        return output

    def _add_reasoning_if_present(self, output: dict[str, Any], result: Any) -> dict[str, Any]:
        """Add reasoning from result if present."""
        if result is not None and hasattr(result, "reasoning"):
            output.setdefault("reasoning", str(result.reasoning))
        return output

    @timed_execution()
    @with_llm_fallback(default_return=None)
    async def aforward(
        self, task_description: str, user_context: dict | None = None
    ) -> dspy.Prediction:
        """Async requirements gathering using DSPy `acall`."""
        clean_task = self._sanitize_input(task_description)
        clean_context = self._sanitize_input(str(user_context or {}))

        result = await self.gather.acall(task_description=clean_task, user_context=clean_context)

        # Normalize result
        if result is None:
            output = self._create_fallback_output(clean_task)
        else:
            output = self._normalize_result(result)
            output = self._add_reasoning_if_present(output, result)

        # Validate and fill defaults
        output = self._validate_and_fill_defaults(output)

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

        # Normalize result
        if result is None:
            output = self._create_fallback_output(clean_task)
        else:
            output = self._normalize_result(result)
            output = self._add_reasoning_if_present(output, result)

        # Validate and fill defaults
        output = self._validate_and_fill_defaults(output)

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"task_description": clean_task[:100]},
            outputs={k: v for k, v in output.items() if k != "ambiguities"},
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)
