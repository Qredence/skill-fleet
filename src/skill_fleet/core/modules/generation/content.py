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
from skill_fleet.core.signatures.generation.content import (
    GenerateSkillContent,
    SkillPlan,
    SkillUnderstanding,
)

if TYPE_CHECKING:
    from collections.abc import Callable
from skill_fleet.core.modules.generation.templates import (
    SkillTemplate,
    get_template_for_category,
    validate_against_template,
)

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

    def _create_skill_plan(self, plan: dict, understanding: dict) -> SkillPlan:
        """Create structured SkillPlan from raw dict inputs with template enhancement."""
        skill_category = understanding.get("skill_category", "other")
        template = get_template_for_category(skill_category)

        # Build content outline from plan
        content_outline = []
        outline_data = plan.get("content_outline", [])
        if isinstance(outline_data, list):
            for item in outline_data:
                if isinstance(item, dict):
                    content_outline.append(
                        {
                            "title": item.get("title", "Untitled"),
                            "description": item.get("description", ""),
                            "estimated_length": item.get("estimated_length", "medium"),
                        }
                    )

        return SkillPlan(
            skill_name=plan.get("skill_name", "unnamed-skill"),
            skill_description=plan.get("skill_description", ""),
            content_outline=content_outline,
            generation_guidance=plan.get("generation_guidance", ""),
            skill_category=skill_category,
            required_sections=template["sections"],
            required_elements=template["required_elements"],
            example_skills=template["example_skills"],
        )

    def _create_skill_understanding(self, understanding: dict) -> SkillUnderstanding:
        """Create structured SkillUnderstanding from raw dict input."""
        return SkillUnderstanding(
            domain=understanding.get("domain", "technical"),
            category=understanding.get("category", "general"),
            target_level=understanding.get("target_level", "intermediate"),
            topics=understanding.get("topics", []),
            constraints=understanding.get("constraints", []),
            requirements=understanding.get("requirements", {}),
            intent=understanding.get("intent", {}),
            taxonomy=understanding.get("taxonomy", {}),
            dependencies=understanding.get("dependencies", []),
        )

    def _process_generation_result(
        self, result: dspy.Prediction, skill_category: str, template: SkillTemplate
    ) -> dict[str, Any]:
        """Process and validate generation result."""
        skill_content = result.skill_content
        template_validation = validate_against_template(skill_content, template)

        sections_list = (
            result.sections_generated if isinstance(result.sections_generated, list) else []
        )

        return {
            "skill_content": skill_content,
            "sections_generated": sections_list,
            "code_examples_count": int(result.code_examples_count)
            if hasattr(result, "code_examples_count")
            else 0,
            "estimated_reading_time": int(result.estimated_reading_time)
            if hasattr(result, "estimated_reading_time")
            else 10,
            "category": skill_category,
            "template_compliance": template_validation,
            "missing_sections": template_validation.get("missing_sections", []),
        }

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

        # Create structured inputs following DSPy best practices
        skill_plan = self._create_skill_plan(plan, understanding)
        skill_understanding = self._create_skill_understanding(understanding)

        # Get template for validation
        template = get_template_for_category(skill_plan.skill_category)

        # Execute signature with structured Pydantic models (not stringified JSON)
        result = await self.generate.acall(
            plan=skill_plan,
            understanding=skill_understanding,
            skill_style=skill_style,
        )

        # Process and validate result
        output = self._process_generation_result(result, skill_plan.skill_category, template)

        # Validate
        required = ["skill_content"]
        if not self._validate_result(output, required):
            self.logger.error("Failed to generate skill content")
            output["skill_content"] = "# Error\n\nFailed to generate content."

        # Log
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "plan": str(plan)[:50],
                "style": skill_style,
                "category": skill_plan.skill_category,
            },
            outputs={
                "sections": len(output["sections_generated"]),
                "examples": output["code_examples_count"],
                "template_compliance": output["template_compliance"].get("compliance_score", 0.0),
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

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

        # Create structured inputs (same as aforward)
        skill_plan = self._create_skill_plan(plan, understanding)
        skill_understanding = self._create_skill_understanding(understanding)

        # Get template for validation
        template = get_template_for_category(skill_plan.skill_category)

        # Execute with streaming
        output = self._streaming_generate(
            plan=skill_plan,
            understanding=skill_understanding,
            skill_style=skill_style,
            include_final_prediction_in_output_stream=True,
        )

        final_prediction = None

        async for value in output:
            if isinstance(value, dspy.Prediction):
                final_prediction = value
                # Process final prediction using shared helper
                output_data = self._process_generation_result(
                    value, skill_plan.skill_category, template
                )
                yield {"type": "prediction", "data": output_data}
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
                inputs={
                    "plan": str(plan)[:50],
                    "style": skill_style,
                    "category": skill_plan.skill_category,
                },
                outputs={
                    "sections": len(sections_list),
                    "streaming": True,
                },
                duration_ms=duration_ms,
            )
