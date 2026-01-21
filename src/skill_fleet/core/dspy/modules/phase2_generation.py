"""DSPy modules for Phase 2: Content Generation.

v2 Golden Standard (Jan 2026):
- Supports 3 skill styles: navigation_hub, comprehensive, minimal
- Progressive disclosure via subdirectory files (references/, guides/, etc.)
- Gold examples from .skills/ directory
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import dspy

from ....common.async_utils import run_async
from ....common.paths import find_repo_root
from ....common.serialization import (
    merge_subdirectory_files as common_merge_subdirectory_files,
)
from ....common.serialization import (
    serialize_pydantic_objects as common_serialize_pydantic_objects,
)
from ..signatures.phase2_generation import (
    GenerateSkillContent,
    IncorporateFeedback,
    SkillStyle,
)

logger = logging.getLogger(__name__)

# Default skill style when not specified
DEFAULT_SKILL_STYLE: SkillStyle = "comprehensive"


def _load_gold_standard_examples(max_examples: int = 2) -> str:
    """Load gold standard skill examples for few-shot learning.

    v2 Golden Standard: Loads from .skills/ directory which contains
    proven high-quality skills (dspy-basics, vibe-coding, neon-drizzle).

    Args:
        max_examples: Maximum number of examples to include

    Returns:
        Formatted string with example excerpts
    """
    repo_root = find_repo_root(Path.cwd()) or find_repo_root(Path(__file__).resolve()) or Path.cwd()

    # v2 Golden Standard: Primary gold skills from .skills/
    gold_skill_paths = [
        ".skills/dspy-basics/SKILL.md",  # Navigation hub example
        ".skills/vibe-coding/SKILL.md",  # Comprehensive example
        ".skills/neon-db/neon-drizzle/SKILL.md",  # Navigation hub with guides/
        # Fallback to legacy paths if .skills/ doesn't exist
        "skills/python/fastapi-production/SKILL.md",
        "skills/python/decorators/SKILL.md",
    ]

    examples = []
    for skill_path in gold_skill_paths:
        if len(examples) >= max_examples:
            break
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

    # Use consolidated serialization utility
    result = common_serialize_pydantic_objects(
        items if isinstance(items, list) else [items], output_format="dict"
    )

    # Ensure result is a list and cast to expected type
    if not isinstance(result, list):
        result = [result] if result else []

    # Type assertion: result is list[dict[str, Any]]
    assert all(isinstance(item, dict) for item in result), "All items must be dicts"
    return result  # type: ignore[return-value]


def _normalize_dict_output(value: Any, field_name: str = "") -> dict[str, str]:
    """Normalize DSPy output to dict[str, str] format.

    DSPy may return strings, empty values, or dicts. This ensures we get a dict.

    Args:
        value: Raw DSPy output value
        field_name: Name of field for debugging

    Returns:
        Normalized dict[str, str]
    """
    if not value:
        return {}
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    if isinstance(value, str):
        # Try to parse as JSON if it's a string
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            logger.debug(f"Could not parse {field_name} as JSON: {value[:100]}...")
    return {}


def _merge_subdirectory_files(
    reference_files: dict[str, str],
    guide_files: dict[str, str],
    template_files: dict[str, str],
    script_files: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Merge individual subdirectory file dicts into consolidated format.

    Args:
        reference_files: Files for references/ directory
        guide_files: Files for guides/ directory
        template_files: Files for templates/ directory
        script_files: Files for scripts/ directory

    Returns:
        Consolidated dict: {'references': {...}, 'guides': {...}, ...}
    """
    return common_merge_subdirectory_files(
        {"references": reference_files} if reference_files else {},
        {"guides": guide_files} if guide_files else {},
        {"templates": template_files} if template_files else {},
        {"scripts": script_files} if script_files else {},
    )


class ContentGeneratorModule(dspy.Module):
    """Generate initial skill content from the Phase 1 plan.

    v2 Golden Standard: Now supports skill_style input and subdirectory file outputs.
    """

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
        skill_style: SkillStyle | None = None,
    ) -> dict[str, Any]:
        """Generate skill content based on metadata and planning.

        Args:
            skill_metadata: Skill metadata including name, description, etc.
            content_plan: Structured plan for the skill content
            generation_instructions: Specific instructions for content generation
            parent_skills_content: Content from parent skills in taxonomy
            dependency_summaries: Summaries of skill dependencies
            skill_style: v2 Golden Standard - skill style (navigation_hub, comprehensive, minimal)

        Returns:
            dict: Generated content including skill_content, usage_examples,
                  best_practices, test_cases, estimated_reading_time, subdirectory_files, and rationale
        """
        enhanced_instructions = self._get_enhanced_instructions(generation_instructions)
        effective_style = skill_style or DEFAULT_SKILL_STYLE

        result = self.generate(
            skill_metadata=skill_metadata,
            skill_style=effective_style,
            content_plan=content_plan,
            generation_instructions=enhanced_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )

        # Normalize subdirectory file outputs
        reference_files = _normalize_dict_output(
            getattr(result, "reference_files", {}), "reference_files"
        )
        guide_files = _normalize_dict_output(getattr(result, "guide_files", {}), "guide_files")
        template_files = _normalize_dict_output(
            getattr(result, "template_files", {}), "template_files"
        )
        script_files = _normalize_dict_output(getattr(result, "script_files", {}), "script_files")

        return {
            "skill_content": result.skill_content,
            "usage_examples": _serialize_pydantic_list(result.usage_examples),
            "best_practices": _serialize_pydantic_list(result.best_practices),
            "test_cases": _serialize_pydantic_list(result.test_cases),
            "estimated_reading_time": result.estimated_reading_time,
            "skill_style": effective_style,
            "subdirectory_files": _merge_subdirectory_files(
                reference_files, guide_files, template_files, script_files
            ),
            "rationale": getattr(result, "rationale", ""),
        }

    async def aforward(
        self,
        skill_metadata: Any,
        content_plan: str,
        generation_instructions: str,
        parent_skills_content: str,
        dependency_summaries: str,
        skill_style: SkillStyle | None = None,
    ) -> dict[str, Any]:
        """Async wrapper for content generation (preferred)."""
        enhanced_instructions = self._get_enhanced_instructions(generation_instructions)
        effective_style = skill_style or DEFAULT_SKILL_STYLE

        result = await self.generate.acall(
            skill_metadata=skill_metadata,
            skill_style=effective_style,
            content_plan=content_plan,
            generation_instructions=enhanced_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
        )

        # Normalize subdirectory file outputs
        reference_files = _normalize_dict_output(
            getattr(result, "reference_files", {}), "reference_files"
        )
        guide_files = _normalize_dict_output(getattr(result, "guide_files", {}), "guide_files")
        template_files = _normalize_dict_output(
            getattr(result, "template_files", {}), "template_files"
        )
        script_files = _normalize_dict_output(getattr(result, "script_files", {}), "script_files")

        return {
            "skill_content": result.skill_content,
            "usage_examples": _serialize_pydantic_list(result.usage_examples),
            "best_practices": _serialize_pydantic_list(result.best_practices),
            "test_cases": _serialize_pydantic_list(result.test_cases),
            "estimated_reading_time": result.estimated_reading_time,
            "skill_style": effective_style,
            "subdirectory_files": _merge_subdirectory_files(
                reference_files, guide_files, template_files, script_files
            ),
            "rationale": getattr(result, "rationale", ""),
        }


class FeedbackIncorporatorModule(dspy.Module):
    """Apply user feedback and change requests to draft content.

    v2 Golden Standard: Now handles subdirectory files (references, guides, templates, scripts).
    """

    def __init__(self):
        super().__init__()
        self.incorporate = dspy.ChainOfThought(IncorporateFeedback)

    def forward(
        self,
        current_content: str,
        user_feedback: str,
        change_requests: str,
        skill_metadata: Any,
        skill_style: SkillStyle | None = None,
        current_subdirectory_files: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Incorporate user feedback into existing skill content.

        Args:
            current_content: Current skill content to be refined
            user_feedback: User's feedback and comments
            change_requests: Specific change requests from user
            skill_metadata: Skill metadata for context
            skill_style: v2 Golden Standard - skill style
            current_subdirectory_files: Current subdirectory files (if any)

        Returns:
            dict: Refined content including refined_content, subdirectory_files, changes_made
        """
        effective_style = skill_style or DEFAULT_SKILL_STYLE
        subdir_json = json.dumps(current_subdirectory_files or {})

        result = self.incorporate(
            current_content=current_content,
            current_subdirectory_files=subdir_json,
            user_feedback=user_feedback,
            change_requests=change_requests,
            skill_metadata=skill_metadata,
            skill_style=effective_style,
        )

        # Normalize refined subdirectory file outputs
        refined_reference_files = _normalize_dict_output(
            getattr(result, "refined_reference_files", {}), "refined_reference_files"
        )
        refined_guide_files = _normalize_dict_output(
            getattr(result, "refined_guide_files", {}), "refined_guide_files"
        )
        refined_template_files = _normalize_dict_output(
            getattr(result, "refined_template_files", {}), "refined_template_files"
        )
        refined_script_files = _normalize_dict_output(
            getattr(result, "refined_script_files", {}), "refined_script_files"
        )

        return {
            "refined_content": result.refined_content,
            "subdirectory_files": _merge_subdirectory_files(
                refined_reference_files,
                refined_guide_files,
                refined_template_files,
                refined_script_files,
            ),
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
        skill_style: SkillStyle | None = None,
        current_subdirectory_files: dict[str, dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Async wrapper for feedback incorporation (preferred)."""
        effective_style = skill_style or DEFAULT_SKILL_STYLE
        subdir_json = json.dumps(current_subdirectory_files or {})

        result = await self.incorporate.acall(
            current_content=current_content,
            current_subdirectory_files=subdir_json,
            user_feedback=user_feedback,
            change_requests=change_requests,
            skill_metadata=skill_metadata,
            skill_style=effective_style,
        )

        # Normalize refined subdirectory file outputs
        refined_reference_files = _normalize_dict_output(
            getattr(result, "refined_reference_files", {}), "refined_reference_files"
        )
        refined_guide_files = _normalize_dict_output(
            getattr(result, "refined_guide_files", {}), "refined_guide_files"
        )
        refined_template_files = _normalize_dict_output(
            getattr(result, "refined_template_files", {}), "refined_template_files"
        )
        refined_script_files = _normalize_dict_output(
            getattr(result, "refined_script_files", {}), "refined_script_files"
        )

        return {
            "refined_content": result.refined_content,
            "subdirectory_files": _merge_subdirectory_files(
                refined_reference_files,
                refined_guide_files,
                refined_template_files,
                refined_script_files,
            ),
            "changes_made": result.changes_made,
            "unaddressed_feedback": result.unaddressed_feedback,
            "improvement_score": result.improvement_score,
            "rationale": getattr(result, "rationale", ""),
        }


class Phase2GenerationModule(dspy.Module):
    """Phase 2 orchestrator: generate content and optionally incorporate feedback.

    v2 Golden Standard: Supports skill styles and subdirectory file generation.
    """

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
        skill_style: SkillStyle | None = None,
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
            skill_style: v2 Golden Standard - skill style (navigation_hub, comprehensive, minimal)
            user_feedback: Optional user feedback for refinement
            change_requests: Optional specific change requests

        Returns:
            dict: Final generated content with all metadata and subdirectory_files
        """
        content_result = await self.generate_content.aforward(
            skill_metadata=skill_metadata,
            content_plan=content_plan,
            generation_instructions=generation_instructions,
            parent_skills_content=parent_skills_content,
            dependency_summaries=dependency_summaries,
            skill_style=skill_style,
        )

        if user_feedback or change_requests:
            refinement_result = await self.incorporate_feedback.aforward(
                current_content=content_result["skill_content"],
                user_feedback=user_feedback,
                change_requests=change_requests,
                skill_metadata=skill_metadata,
                skill_style=skill_style,
                current_subdirectory_files=content_result.get("subdirectory_files"),
            )
            content_result["skill_content"] = refinement_result["refined_content"]
            content_result["subdirectory_files"] = refinement_result["subdirectory_files"]
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
