"""
Skill content generation module.

Uses GenerateSkillContent signature to create complete SKILL.md
with YAML frontmatter and structured content.

Now supports category-specific templates for document creation,
workflow automation, MCP enhancement, and analysis skills.

Supports token-level streaming via dspy.streamify for real-time output.
"""

import time
from typing import TYPE_CHECKING, Any

import dspy
from dspy.streaming import StreamListener, streamify

from skill_fleet.core.modules.base import BaseModule

if TYPE_CHECKING:
    from collections.abc import Callable
from skill_fleet.core.modules.generation.templates import (
    get_template_for_category,
    validate_against_template,
)
from skill_fleet.core.signatures.generation.content import GenerateSkillContent

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


class GenerateSkillContentModule(BaseModule):
    """
    Generate complete skill content (SKILL.md).

    Uses GenerateSkillContent signature to create:
    - YAML frontmatter with metadata
    - Structured markdown content
    - Code examples
    - Based on plan and understanding

    Now supports category-specific templates to ensure generated skills
    follow best practices for their intended use case.

    Example:
        module = GenerateSkillContentModule()
        result = await module.aforward(
            plan={"skill_name": "react-hooks", "content_outline": [...]},
            understanding={"requirements": {...}, "intent": {...}},
            skill_style="comprehensive"
        )

    """

    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(GenerateSkillContent)
        # Create streamified version with skill_content listener
        self._stream_listeners = [
            StreamListener(signature_field_name="skill_content"),
        ]
        self._streaming_generate: Callable[..., Any] = streamify(
            program=self.generate,
            stream_listeners=self._stream_listeners,
        )

    async def aforward(  # type: ignore[override]
        self, plan: dict, understanding: dict, skill_style: str = "comprehensive"
    ) -> dspy.Prediction:
        """
        Generate skill content asynchronously.

        Args:
            plan: Skill plan with outline and guidance
            understanding: Understanding from Phase 1
            skill_style: Content style preference

        Returns:
            dspy.Prediction with generated content and template compliance

        """
        start_time = time.time()

        # Get category-specific template
        skill_category = understanding.get("skill_category", "other")
        template = get_template_for_category(skill_category)

        # Enhance plan with template information
        enhanced_plan = {
            **plan,
            "skill_category": skill_category,
            "required_sections": template["sections"],
            "required_elements": template["required_elements"],
            "example_skills": template["example_skills"],
        }

        # Execute signature with enhanced plan
        result = await self.generate.acall(
            plan=str(enhanced_plan),
            understanding=str(understanding),
            skill_style=skill_style,
        )

        # Transform output
        skill_content = result.skill_content

        # Validate against template
        template_validation = validate_against_template(skill_content, template)

        output = {
            "skill_content": skill_content,
            "sections_generated": result.sections_generated
            if isinstance(result.sections_generated, list)
            else [],
            "code_examples_count": int(result.code_examples_count)
            if hasattr(result, "code_examples_count")
            else 0,
            "estimated_reading_time": int(result.estimated_reading_time)
            if hasattr(result, "estimated_reading_time")
            else 10,
            # NEW: Template compliance data
            "category": skill_category,
            "template_compliance": template_validation,
            "missing_sections": template_validation.get("missing_sections", []),
        }

        # Validate
        required = ["skill_content"]
        if not self._validate_result(output, required):
            self.logger.error("Failed to generate skill content")
            output["skill_content"] = "# Error\n\nFailed to generate content."

        # Log
        sections_list = output.get("sections_generated", [])
        if not isinstance(sections_list, list):
            sections_list = []
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={"plan": str(plan)[:50], "style": skill_style, "category": skill_category},
            outputs={
                "sections": len(sections_list),
                "examples": output["code_examples_count"],
                "template_compliance": template_validation.get("compliance_score", 0.0),
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def forward(self, **kwargs) -> dspy.Prediction:
        """Sync version - delegates to async."""
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))

    async def aforward_streaming(
        self,
        plan: dict,
        understanding: dict,
        skill_style: str = "comprehensive",
    ) -> "AsyncIterator[dict[str, Any]]":
        """
        Generate skill content with token-level streaming.

        Yields chunks of content as they are generated by the LLM,
        enabling real-time display in CLI/UI.

        Args:
            plan: Skill plan with outline and guidance
            understanding: Understanding from Phase 1
            skill_style: Content style preference

        Yields:
            Dict with streaming events:
            - {"type": "token", "field": "skill_content", "content": "..."}
            - {"type": "prediction", "data": {...}} for final result

        Example:
            async for event in module.aforward_streaming(plan, understanding):
                if event["type"] == "token":
                    print(event["content"], end="", flush=True)
                elif event["type"] == "prediction":
                    final_result = event["data"]

        """
        start_time = time.time()

        # Get category-specific template
        skill_category = understanding.get("skill_category", "other")
        template = get_template_for_category(skill_category)

        # Enhance plan with template information
        enhanced_plan = {
            **plan,
            "skill_category": skill_category,
            "required_sections": template["sections"],
            "required_elements": template["required_elements"],
            "example_skills": template["example_skills"],
        }

        # Execute with streaming
        output = self._streaming_generate(
            plan=str(enhanced_plan),
            understanding=str(understanding),
            skill_style=skill_style,
            include_final_prediction_in_output_stream=True,
        )

        final_prediction = None

        async for value in output:
            if isinstance(value, dspy.Prediction):
                final_prediction = value
                # Process final prediction same as aforward
                skill_content = value.skill_content
                template_validation = validate_against_template(skill_content, template)

                result_data = {
                    "skill_content": skill_content,
                    "sections_generated": value.sections_generated
                    if isinstance(value.sections_generated, list)
                    else [],
                    "code_examples_count": int(value.code_examples_count)
                    if hasattr(value, "code_examples_count")
                    else 0,
                    "estimated_reading_time": int(value.estimated_reading_time)
                    if hasattr(value, "estimated_reading_time")
                    else 10,
                    "category": skill_category,
                    "template_compliance": template_validation,
                    "missing_sections": template_validation.get("missing_sections", []),
                }

                yield {"type": "prediction", "data": result_data}
            elif hasattr(value, "field_name") and hasattr(value, "chunk"):
                # StreamResponse from dspy.streaming
                yield {
                    "type": "token",
                    "field": value.field_name,
                    "content": value.chunk,
                }
            else:
                # Fallback for other message types
                yield {"type": "message", "content": str(value)}

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        if final_prediction:
            sections_list = getattr(final_prediction, "sections_generated", [])
            if not isinstance(sections_list, list):
                sections_list = []
            self._log_execution(
                inputs={"plan": str(plan)[:50], "style": skill_style, "category": skill_category},
                outputs={
                    "sections": len(sections_list),
                    "streaming": True,
                },
                duration_ms=duration_ms,
            )
