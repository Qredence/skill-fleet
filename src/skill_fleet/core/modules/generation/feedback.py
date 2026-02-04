"""
User feedback incorporation module.

Uses the IncorporateFeedback DSPy signature to apply targeted edits to an
already-generated SKILL.md while preserving structure and agentskills.io
frontmatter.
"""

from __future__ import annotations

import dspy

from skill_fleet.common.llm_fallback import with_llm_fallback
from skill_fleet.common.utils import timed_execution
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.generation.content import IncorporateFeedback


class IncorporateFeedbackModule(BaseModule):
    """Apply user feedback to existing SKILL.md content."""

    def __init__(self) -> None:
        super().__init__()
        self.revise = dspy.ChainOfThought(IncorporateFeedback)

    @staticmethod
    def _to_change_requests(feedback: str) -> list[str]:
        lines = [ln.strip() for ln in feedback.splitlines() if ln.strip()]
        if not lines:
            return []
        # Treat bullet lists as individual requests; otherwise use whole feedback.
        bullets = [ln.lstrip("-* ").strip() for ln in lines if ln[:2] in {"- ", "* "}]
        if bullets:
            return [b for b in bullets if b]
        return [feedback.strip()]

    @timed_execution()
    @with_llm_fallback(default_return=None)
    async def aforward(self, current_content: str, feedback: str) -> dspy.Prediction:
        """Return revised content by applying user feedback to an existing SKILL.md."""
        change_requests = self._to_change_requests(feedback)
        result = await self.revise.acall(
            current_content=current_content,
            feedback=feedback,
            change_requests=change_requests,
        )

        if result is None:
            # Best-effort no-op fallback.
            return self._to_prediction(
                revised_content=current_content,
                changes_made=[],
                changes_rejected=["LLM unavailable; could not apply feedback."],
            )

        return result
