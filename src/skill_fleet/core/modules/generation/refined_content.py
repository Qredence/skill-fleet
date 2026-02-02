"""
Refined content generation module using dspy.Refine.

Uses iterative refinement to improve skill content quality through
multiple passes with feedback-driven improvements.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import dspy

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.generation.templates import (
    SkillTemplate,
    get_template_for_category,
    validate_against_template,
)
from skill_fleet.core.signatures.generation.content import GenerateSkillContent

logger = logging.getLogger(__name__)


class SkillQualityReward:
    """
    Reward function for assessing skill content quality.

    Evaluates skill content across multiple dimensions:
    - Completeness (required sections present)
    - Clarity (readability metrics)
    - Structure (YAML frontmatter, markdown)
    - Examples (code blocks, practicality)
    - Conciseness (appropriate length)

    Returns a score between 0.0 and 1.0.

    """

    # Optimal word count range for skills
    MIN_WORDS = 500
    OPTIMAL_WORDS = 2500
    MAX_WORDS = 5000

    # Required sections for a complete skill
    REQUIRED_SECTIONS = [
        "instructions",
        "examples",
        "when to use",
    ]

    def __init__(self):
        """Initialize the reward function."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, skill_content: str, plan: dict[str, Any] | None = None) -> float:
        """
        Calculate quality score for skill content.

        Args:
            skill_content: The SKILL.md content to evaluate
            plan: Optional original plan for comparison

        Returns:
            Quality score between 0.0 and 1.0

        """
        scores = {
            "completeness": self._score_completeness(skill_content),
            "structure": self._score_structure(skill_content),
            "clarity": self._score_clarity(skill_content),
            "examples": self._score_examples(skill_content),
            "conciseness": self._score_conciseness(skill_content),
        }

        # Weighted average
        weights = {
            "completeness": 0.25,
            "structure": 0.20,
            "clarity": 0.20,
            "examples": 0.20,
            "conciseness": 0.15,
        }

        total_score = sum(scores[k] * weights[k] for k in scores)

        self.logger.debug(f"Quality scores: {scores}, Total: {total_score:.3f}")

        return round(total_score, 3)

    def _score_completeness(self, content: str) -> float:
        """Score content completeness based on required sections."""
        content_lower = content.lower()

        # Check for required sections
        sections_found = sum(1 for section in self.REQUIRED_SECTIONS if section in content_lower)

        # Check for YAML frontmatter
        has_frontmatter = content.strip().startswith("---")
        has_name = "name:" in content_lower[:500]  # In frontmatter
        has_description = "description:" in content_lower[:500]

        section_score = sections_found / len(self.REQUIRED_SECTIONS)
        frontmatter_score = (
            (1.0 if has_frontmatter else 0.0)
            + (0.5 if has_name else 0.0)
            + (0.5 if has_description else 0.0)
        ) / 2.0

        return (section_score + frontmatter_score) / 2.0

    def _score_structure(self, content: str) -> float:
        """Score content structure and formatting."""
        score = 0.0

        # Check markdown headers
        headers = re.findall(r"^#{1,6}\s+.+$", content, re.MULTILINE)
        if len(headers) >= 3:
            score += 0.3
        if len(headers) >= 5:
            score += 0.2

        # Check for proper heading hierarchy
        header_levels = [len(h.split()[0]) for h in headers]
        # Prefer starting with h1 or h2
        if header_levels and header_levels[0] <= 2:
            score += 0.2

        # Check for lists (bullet points, numbered)
        has_lists = bool(re.search(r"^[\s]*[-*\d]\s+", content, re.MULTILINE))
        if has_lists:
            score += 0.3

        return min(score, 1.0)

    def _score_clarity(self, content: str) -> float:
        """Score content clarity and readability."""
        # Remove code blocks for analysis
        text_only = re.sub(r"```[\s\S]*?```", "", content)
        text_only = re.sub(r"`[^`]+`", "", text_only)

        sentences = re.split(r"[.!?]+", text_only)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return 0.0

        # Average sentence length (shorter is generally clearer)
        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Score based on sentence length
        if avg_length <= 15:
            length_score = 1.0
        elif avg_length <= 20:
            length_score = 0.8
        elif avg_length <= 25:
            length_score = 0.6
        else:
            length_score = 0.4

        # Check for passive voice indicators (simplified)
        passive_indicators = ["is done", "was created", "were added", "is used"]
        passive_count = sum(text_only.lower().count(p) for p in passive_indicators)
        passive_score = max(0.0, 1.0 - (passive_count / max(len(sentences), 1)))

        return (length_score + passive_score) / 2.0

    def _score_examples(self, content: str) -> float:
        """Score code examples and practicality."""
        score = 0.0

        # Count code blocks
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        if code_blocks:
            score += 0.3
        if len(code_blocks) >= 2:
            score += 0.2
        if len(code_blocks) >= 3:
            score += 0.2

        # Check for inline code
        inline_code = re.findall(r"`[^`]+`", content)
        if len(inline_code) >= 3:
            score += 0.15

        # Check for example descriptions
        has_example_text = "example" in content.lower()
        if has_example_text:
            score += 0.15

        return min(score, 1.0)

    def _score_conciseness(self, content: str) -> float:
        """Score content length and conciseness."""
        word_count = len(content.split())

        if word_count < self.MIN_WORDS:
            # Too short
            return word_count / self.MIN_WORDS * 0.5
        elif word_count <= self.OPTIMAL_WORDS:
            # Optimal range
            return 1.0
        elif word_count <= self.MAX_WORDS:
            # Acceptable but getting long
            return (
                1.0
                - (word_count - self.OPTIMAL_WORDS) / (self.MAX_WORDS - self.OPTIMAL_WORDS) * 0.3
            )
        else:
            # Too long
            return max(0.4, 0.7 - (word_count - self.MAX_WORDS) / self.MAX_WORDS)


class RefinedContentModule(BaseModule):
    """
    Generate refined skill content using iterative improvement.

    Uses dspy.Refine pattern with a quality reward function to iteratively
    improve generated content. The module generates initial content, evaluates
    it, and refines based on feedback until quality threshold is met or
    max iterations reached.

    Example:
        >>> module = RefinedContentModule()
        >>> result = await module.aforward(
        ...     plan={"skill_name": "react-hooks", ...},
        ...     understanding={"requirements": {...}},
        ...     target_quality=0.85,
        ...     max_iterations=3
        ... )
        >>> print(result.skill_content)
        >>> print(result.quality_score)  # 0.87
        >>> print(result.iterations)  # 2

    """

    def __init__(self):
        """Initialize the refined content module."""
        super().__init__()
        self.generator = dspy.ChainOfThought(GenerateSkillContent)
        self.reward_fn = SkillQualityReward()

    async def aforward(  # type: ignore[override]
        self,
        plan: dict[str, Any],
        understanding: dict[str, Any],
        skill_style: str = "comprehensive",
        target_quality: float = 0.80,
        max_iterations: int = 3,
    ) -> dspy.Prediction:
        """
        Generate refined skill content with iterative improvement.

        Args:
            plan: Skill plan with outline and guidance
            understanding: Understanding from Phase 1
            skill_style: Content style preference
            target_quality: Target quality score (0.0-1.0)
            max_iterations: Maximum refinement iterations

        Returns:
            dspy.Prediction with:
            - skill_content: Final refined content
            - quality_score: Final quality score
            - iterations: Number of iterations performed
            - improvements: List of improvements made
            - initial_quality: Initial quality score

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

        # Track improvements
        improvements: list[dict[str, Any]] = []

        # Generate initial content
        result = await self.generator.acall(
            plan=str(enhanced_plan),
            understanding=str(understanding),
            skill_style=skill_style,
        )

        current_content = result.skill_content

        # Evaluate initial quality
        current_quality = self.reward_fn(current_content, plan)
        initial_quality = current_quality

        self.logger.info(f"Initial content quality: {current_quality:.3f}")

        # Iterative refinement
        iteration = 0
        for iteration in range(1, max_iterations + 1):
            if current_quality >= target_quality:
                self.logger.info(
                    f"Quality target met ({current_quality:.3f} >= {target_quality}), stopping"
                )
                break

            # Generate refinement feedback
            feedback = self._generate_refinement_feedback(
                current_content, current_quality, plan, template
            )

            self.logger.info(f"Iteration {iteration}: Quality {current_quality:.3f}, refining...")

            # Refine content using feedback
            refined_result = await self._refine_content(
                current_content=current_content,
                feedback=feedback,
                plan=enhanced_plan,
                understanding=understanding,
            )

            # Evaluate refined content
            new_content = refined_result.get("skill_content", current_content)
            new_quality = self.reward_fn(new_content, plan)

            # Track improvement
            improvement = {
                "iteration": iteration,
                "previous_quality": current_quality,
                "new_quality": new_quality,
                "feedback": feedback,
            }
            improvements.append(improvement)

            if new_quality > current_quality:
                current_content = new_content
                current_quality = new_quality
                self.logger.info(f"Iteration {iteration}: Improved to {current_quality:.3f}")
            else:
                self.logger.info(
                    f"Iteration {iteration}: No improvement ({new_quality:.3f}), keeping previous"
                )
                # Stop if no improvement
                break

        # Validate against template
        template_validation = validate_against_template(current_content, template)

        output = {
            "skill_content": current_content,
            "quality_score": current_quality,
            "initial_quality": initial_quality,
            "iterations": iteration,
            "improvements": improvements,
            "target_quality": target_quality,
            "target_met": current_quality >= target_quality,
            "category": skill_category,
            "template_compliance": template_validation,
            "sections_generated": self._extract_sections(current_content),
            "code_examples_count": len(re.findall(r"```[\s\S]*?```", current_content)),
            "estimated_reading_time": max(1, len(current_content.split()) // 200),
        }

        # Log execution
        duration_ms = (time.time() - start_time) * 1000
        self._log_execution(
            inputs={
                "plan": str(plan)[:50],
                "style": skill_style,
                "target_quality": target_quality,
            },
            outputs={
                "final_quality": current_quality,
                "iterations": iteration,
                "target_met": output["target_met"],
            },
            duration_ms=duration_ms,
        )

        return self._to_prediction(**output)

    def _generate_refinement_feedback(
        self,
        content: str,
        quality: float,
        plan: dict[str, Any],
        template: SkillTemplate,
    ) -> str:
        """Generate specific feedback for content refinement."""
        feedback_points = []

        # Check completeness
        content_lower = content.lower()
        missing_sections = [
            section
            for section in ["instructions", "examples", "when to use"]
            if section not in content_lower
        ]
        if missing_sections:
            feedback_points.append(f"Add missing sections: {', '.join(missing_sections)}")

        # Check structure
        if not content.strip().startswith("---"):
            feedback_points.append("Add YAML frontmatter with name and description")

        # Check examples
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        if len(code_blocks) < 2:
            feedback_points.append("Add more practical code examples")

        # Check template compliance
        template_validation = validate_against_template(content, template)
        missing_template = template_validation.get("missing_sections", [])
        if missing_template:
            feedback_points.append(f"Include template sections: {', '.join(missing_template[:3])}")

        # General quality feedback
        if quality < 0.5:
            feedback_points.append("Significantly expand content with more detail and examples")
        elif quality < 0.7:
            feedback_points.append("Improve content with clearer explanations and better structure")
        elif quality < 0.85:
            feedback_points.append("Polish content: improve examples, clarify instructions")

        return (
            "; ".join(feedback_points) if feedback_points else "Polish and improve overall quality"
        )

    async def _refine_content(
        self,
        current_content: str,
        feedback: str,
        plan: dict[str, Any],
        understanding: dict[str, Any],
    ) -> dict[str, Any]:
        """Refine content based on feedback."""

        # Create a refinement signature inline
        class RefineSkillContent(dspy.Signature):
            """Refine skill content based on feedback."""

            current_content: str = dspy.InputField(desc="Current SKILL.md content")
            feedback: str = dspy.InputField(desc="Specific feedback for improvement")
            plan: str = dspy.InputField(desc="Original skill plan")
            understanding: str = dspy.InputField(desc="User requirements understanding")

            skill_content: str = dspy.OutputField(desc="Refined SKILL.md content")
            changes_made: list[str] = dspy.OutputField(desc="List of changes made")

        try:
            refine_predictor = dspy.ChainOfThought(RefineSkillContent)
            result = await refine_predictor.acall(
                current_content=current_content,
                feedback=feedback,
                plan=str(plan),
                understanding=str(understanding),
            )
            return {
                "skill_content": result.skill_content,
                "changes_made": result.changes_made if hasattr(result, "changes_made") else [],
            }
        except Exception as e:
            self.logger.warning(f"Refinement failed: {e}, returning original")
            return {"skill_content": current_content, "changes_made": []}

    def _extract_sections(self, content: str) -> list[str]:
        """Extract section headers from content."""
        headers = re.findall(r"^#{2,3}\s+(.+)$", content, re.MULTILINE)
        return headers

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Sync version - delegates to async."""
        from dspy.utils.syncify import run_async

        return run_async(self.aforward(**kwargs))


def generate_refined_skill_content(
    plan: dict[str, Any],
    understanding: dict[str, Any],
    skill_style: str = "comprehensive",
    target_quality: float = 0.80,
    max_iterations: int = 3,
) -> dspy.Prediction:
    """
    Convenience function for refined skill content generation.

    Args:
        plan: Skill plan with outline and guidance
        understanding: Understanding from Phase 1
        skill_style: Content style preference
        target_quality: Target quality score (0.0-1.0)
        max_iterations: Maximum refinement iterations

    Returns:
        dspy.Prediction with refined content and quality metrics

    Example:
        >>> result = generate_refined_skill_content(
        ...     plan={"skill_name": "react-hooks", ...},
        ...     understanding={"requirements": {...}},
        ...     target_quality=0.85
        ... )
        >>> print(result.quality_score)
        0.87

    """
    module = RefinedContentModule()
    return module.forward(
        plan=plan,
        understanding=understanding,
        skill_style=skill_style,
        target_quality=target_quality,
        max_iterations=max_iterations,
    )
