"""DSPy modules for Phase 2: Content Generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import dspy

from ....common.async_utils import run_async
from ....common.paths import find_repo_root
from ..signatures.phase2_generation import (
    GenerateSkillContent,
    IncorporateFeedback,
)

logger = logging.getLogger(__name__)


def _load_gold_standard_examples(max_examples: int = 2) -> str:
    """Load gold standard skill examples for few-shot learning.

    Loads excerpts from excellent skills to guide content generation.

    Args:
        max_examples: Maximum number of examples to include

    Returns:
        Formatted string with example excerpts
    """
    repo_root = find_repo_root(Path.cwd()) or find_repo_root(Path(__file__).resolve()) or Path.cwd()

    # Known excellent skill paths
    gold_skill_paths = [
        "skills/python/fastapi-production/SKILL.md",
        "skills/python/decorators/SKILL.md",
        "skills/python/async/SKILL.md",
    ]

    examples = []
    for skill_path in gold_skill_paths[:max_examples]:
        full_path = repo_root / skill_path
        if full_path.exists():
            try:
                content = full_path.read_text(encoding="utf-8")
                # Extract key sections for the example (first 150 lines max)
                lines = content.split("\n")[:150]
                excerpt = "\n".join(lines)
                skill_name = skill_path.split("/")[-2]
                examples.append(f"### Example: {skill_name}\n```markdown\n{excerpt}\n```")
            except Exception as e:
                logger.debug(f"Failed to load gold standard {skill_path}: {e}")

    if not examples:
        return ""

    return (
        "\n\n## Gold Standard Examples\n"
        "Study these excellent skill examples for structure and quality:\n\n"
        + "\n\n".join(examples)
    )


def _serialize_pydantic_list(items: Any) -> list[dict[str, Any]]:
    """Serialize a list of Pydantic models to list of dicts.

    DSPy signatures with typed list outputs (e.g., list[UsageExample]) return
    Pydantic model instances. These need to be serialized to dicts for
    downstream processing in TaxonomyManager._write_extra_files().

    Args:
        items: List of Pydantic models, list of dicts, or other values

    Returns:
        List of dicts suitable for file writing
    """
    if not items:
        return []

    if not isinstance(items, list):
        # Handle single item or unexpected type
        if hasattr(items, "model_dump"):
            return [items.model_dump()]
        return [items] if items else []

    result = []
    for item in items:
        if hasattr(item, "model_dump"):
            # Pydantic model - serialize to dict
            result.append(item.model_dump())
        elif isinstance(item, dict):
            # Already a dict
            result.append(item)
        else:
            # String or other type - wrap in dict with content key
            result.append({"content": str(item)})

    return result


class ContentGeneratorModule(dspy.Module):
    """Generate initial skill content from the Phase 1 plan."""

    def __init__(self, quality_assured: bool = True, use_gold_examples: bool = True):
        super().__init__()
        # For simplicity, using ChainOfThought. BestOfN requires a reward function.
        self.quality_assured = quality_assured
        self.use_gold_examples = use_gold_examples
        self.generate = dspy.ChainOfThought(GenerateSkillContent)
        self._gold_examples_cache: str | None = None

    def _get_enhanced_instructions(self, generation_instructions: str) -> str:
        """Enhance generation instructions with gold standard examples.

        Args:
            generation_instructions: Original generation instructions

        Returns:
            Enhanced instructions with gold standard examples appended
        """
        if not self.use_gold_examples:
            return generation_instructions

        # Cache gold examples to avoid repeated file reads
        if self._gold_examples_cache is None:
            self._gold_examples_cache = _load_gold_standard_examples(max_examples=1)

        if self._gold_examples_cache:
            return f"{generation_instructions}\n\n{self._gold_examples_cache}"
        return generation_instructions

    def forward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
    ) -> dict[str, Any]:
        """Generate skill content based on metadata and planning.

        Args:
            skill_metadata: Skill metadata including name, description, etc.
            content_plan: Structured plan for the skill content
            generation_instructions: Specific instructions for content generation
            parent_skills_content: Content from parent skills in taxonomy
            dependency_summaries: Summaries of skill dependencies

        Returns:
            dict: Generated content including skill_content, usage_examples,
                  best_practices, test_cases, estimated_reading_time, and rationale
        """
        enhanced_instructions = self._get_enhanced_instructions(generation_instructions)
        result = self.generate(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=enhanced_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )
        return {
            "skill_content": result.skill_content,
            "usage_examples": _serialize_pydantic_list(result.usage_examples),
            "best_practices": _serialize_pydantic_list(result.best_practices),
            "test_cases": _serialize_pydantic_list(result.test_cases),
            "estimated_reading_time": result.estimated_reading_time,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
    ) -> dict[str, Any]:
        """Async wrapper for content generation (preferred)."""
        enhanced_instructions = self._get_enhanced_instructions(generation_instructions)
        result = await self.generate.acall(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=enhanced_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )
        return {
            "skill_content": result.skill_content,
            "usage_examples": _serialize_pydantic_list(result.usage_examples),
            "best_practices": _serialize_pydantic_list(result.best_practices),
            "test_cases": _serialize_pydantic_list(result.test_cases),
            "estimated_reading_time": result.estimated_reading_time,
            "rationale": getattr(result, "rationale", ""),
        }


class FeedbackIncorporatorModule(dspy.Module):
    """Apply user feedback and change requests to draft content."""

    def __init__(self):
        super().__init__()
        self.incorporate = dspy.ChainOfThought(IncorporateFeedback)

    def forward(
        self,
        current_content: str,
        user_feedback: str,
        change_requests: str,
        skill_metadata: Any,
    ) -> dict[str, Any]:
        """Incorporate user feedback into existing skill content.

        Args:
            current_content: Current skill content to be refined
            user_feedback: User's feedback and comments
            change_requests: Specific change requests from user
            skill_metadata: Skill metadata for context

        Returns:
            dict: Refined content including refined_content, changes_made, and rationale
        """
        result = self.incorporate(
            current_content=current_content,
            user_feedback=user_feedback,
            change_requests=change_requests,
            skill_metadata=skill_metadata,
        )
        return {
            "refined_content": result.refined_content,
            "changes_made": result.changes_made,
            "unaddressed_feedback": result.unaddressed_feedback,
            "improvement_score": result.improvement_score,
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(
        self,
        current_content: str,
        user_feedback: str,
        change_requests: str,
        skill_metadata: Any,
    ) -> dict[str, Any]:
        """Async wrapper for feedback incorporation (preferred)."""
        result = await self.incorporate.acall(
            current_content=current_content,
            user_feedback=user_feedback,
            change_requests=change_requests,
            skill_metadata=skill_metadata,
        )
        return {
            "refined_content": result.refined_content,
            "changes_made": result.changes_made,
            "unaddressed_feedback": result.unaddressed_feedback,
            "improvement_score": result.improvement_score,
            "rationale": getattr(result, "rationale", ""),
        }


class Phase2GenerationModule(dspy.Module):
    """Phase 2 orchestrator: generate content and optionally incorporate feedback."""

    def __init__(self, quality_assured: bool = True):
        super().__init__()
        self.generate_content = ContentGeneratorModule(quality_assured=quality_assured)
        self.incorporate_feedback = FeedbackIncorporatorModule()

    async def aforward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
        user_feedback: str = "",
        change_requests: str = "",
    ) -> dict[str, Any]:
        """Async orchestration of Phase 2 content generation and feedback incorporation.

        Args:
            skill_metadata: Skill metadata including name, description, etc.
            content_plan: Structured plan for the skill content
            generation_instructions: Specific instructions for content generation
            parent_skills_content: Content from parent skills in taxonomy
            dependency_summaries: Summaries of skill dependencies
            user_feedback: Optional user feedback for refinement
            change_requests: Optional specific change requests

        Returns:
            dict: Final generated content with all metadata
        """
        content_result = await self.generate_content.aforward(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=generation_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )
        if user_feedback or change_requests:
            refinement_result = await self.incorporate_feedback.aforward(
                current_content=content_result["skill_content"],
                user_feedback=user_feedback,
                change_requests=change_requests,
                skill_metadata=skill_metadata,
            )
            content_result["skill_content"] = refinement_result["refined_content"]
            content_result["changes_made"] = refinement_result["changes_made"]
            content_result["improvement_score"] = refinement_result["improvement_score"]
        return content_result

    def forward(self, *args, **kwargs) -> dict[str, Any]:
        """Sync version of Phase 2 content generation orchestration.

        Args:
            *args: Positional arguments passed to aforward method
            **kwargs: Keyword arguments passed to aforward method

        Returns:
            dict: Final generated content with all metadata
        """
        return run_async(lambda: self.aforward(*args, **kwargs))
