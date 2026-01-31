"""
Skill content generation module.

Uses GenerateSkillContent signature to create complete SKILL.md
with YAML frontmatter and structured content.

Now supports category-specific templates for document creation,
workflow automation, MCP enhancement, and analysis skills.
"""

import time
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.generation.templates import (
    get_template_for_category,
    validate_against_template,
)
from skill_fleet.core.signatures.generation.content import GenerateSkillContent


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

    async def aforward(  # type: ignore[override]
        self, plan: dict, understanding: dict, skill_style: str = "comprehensive"
    ) -> dict[str, Any]:
        """
        Generate skill content asynchronously.

        Args:
            plan: Skill plan with outline and guidance
            understanding: Understanding from Phase 1
            skill_style: Content style preference

        Returns:
            Dictionary with generated content and template compliance

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

        return output

    def forward(self, **kwargs) -> dict[str, Any]:
        """Sync version - delegates to async."""
        import asyncio

        return asyncio.run(self.aforward(**kwargs))
