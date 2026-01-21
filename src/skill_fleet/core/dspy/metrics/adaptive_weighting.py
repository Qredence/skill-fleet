"""
Adaptive Metric Weighting System for DSPy Skill Evaluation.

Adjusts metric weights based on skill style (navigation_hub, comprehensive, minimal).
Ensures evaluation prioritizes metrics relevant to each skill type.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

import dspy


class SkillStyle(StrEnum):
    """Skill creation styles with different priorities."""

    NAVIGATION_HUB = "navigation_hub"  # Prioritize clarity + coverage
    COMPREHENSIVE = "comprehensive"  # Balanced approach
    MINIMAL = "minimal"  # Prioritize semantic correctness


@dataclass
class MetricWeights:
    """Weights for each metric in evaluation."""

    skill_quality: float = 0.25
    semantic_f1: float = 0.25
    entity_f1: float = 0.20
    readability: float = 0.20
    coverage: float = 0.10

    def to_dict(self) -> dict[str, float]:
        """Convert to dict for use in scoring."""
        return {
            "skill_quality": self.skill_quality,
            "semantic_f1": self.semantic_f1,
            "entity_f1": self.entity_f1,
            "readability": self.readability,
            "coverage": self.coverage,
        }

    @classmethod
    def for_style(cls, style: SkillStyle | str) -> "MetricWeights":
        """Get weights for a specific skill style."""
        if isinstance(style, str):
            try:
                style = SkillStyle(style)
            except ValueError:
                style = SkillStyle.COMPREHENSIVE

        if style == SkillStyle.NAVIGATION_HUB:
            return cls(
                skill_quality=0.30,  # ↑ prioritize structure
                semantic_f1=0.15,
                entity_f1=0.05,  # ↓ de-emphasize
                readability=0.35,  # ↑ must be clear
                coverage=0.15,  # ↑ must have examples
            )
        elif style == SkillStyle.MINIMAL:
            return cls(
                skill_quality=0.20,
                semantic_f1=0.50,  # ↑↑ pure correctness
                entity_f1=0.15,
                readability=0.10,
                coverage=0.05,  # ↓ few examples ok
            )
        else:  # COMPREHENSIVE (default)
            return cls(
                skill_quality=0.25,
                semantic_f1=0.25,  # balanced
                entity_f1=0.20,
                readability=0.20,
                coverage=0.10,
            )


class DetectSkillStyle(dspy.Signature):
    """Detect the style of a skill from its content.

    Navigation hub: Clear, well-organized guide with multiple examples
    Comprehensive: Balanced coverage with patterns and examples
    Minimal: Concise, correct, with minimal overhead
    """

    skill_title: str = dspy.InputField()
    skill_content: str = dspy.InputField()
    skill_description: str = dspy.InputField()

    style: Literal["navigation_hub", "comprehensive", "minimal"] = dspy.OutputField(
        desc="Detected skill style"
    )
    confidence: float = dspy.OutputField(desc="Confidence in detection (0.0-1.0)")
    reasoning: str = dspy.OutputField(desc="Explanation of style detection")


class AdjustMetricWeights(dspy.Signature):
    """Adjust metric weights based on skill style.

    Navigation hub skills prioritize clarity and structure.
    Comprehensive skills use balanced metric weights.
    Minimal skills prioritize semantic correctness.
    """

    skill_style: Literal["navigation_hub", "comprehensive", "minimal"] = dspy.InputField()
    current_scores: dict = dspy.InputField(desc="Current scores for each metric")

    adjusted_weights: dict = dspy.OutputField(
        desc="Adjusted weights for [skill_quality, semantic_f1, entity_f1, readability, coverage]"
    )
    reasoning: str = dspy.OutputField(desc="Explanation of weight adjustments")
    expected_improvement: str = dspy.OutputField(desc="Expected improvement from adjustment")


class SkillStyleDetector(dspy.Module):
    """Detect skill style using chain-of-thought reasoning."""

    def __init__(self):
        super().__init__()
        self.detect_style = dspy.ChainOfThought(DetectSkillStyle)

    def forward(self, skill_title: str, skill_content: str, skill_description: str):
        """Detect style."""
        return self.detect_style(
            skill_title=skill_title,
            skill_content=skill_content,
            skill_description=skill_description,
        )


class WeightAdjuster(dspy.Module):
    """Adjust metric weights using reasoning."""

    def __init__(self):
        super().__init__()
        self.adjust_weights = dspy.ChainOfThought(AdjustMetricWeights)

    def forward(self, skill_style: str, current_scores: dict):
        """Adjust weights."""
        return self.adjust_weights(
            skill_style=skill_style,
            current_scores=current_scores,
        )


class AdaptiveMetricWeighting:
    """Manages adaptive weighting of evaluation metrics based on skill style.

    Usage:
        weighting = AdaptiveMetricWeighting()
        style = weighting.detect_style(skill_title, skill_content, skill_description)
        adjusted_weights = weighting.get_weights(style)
        adjusted_scores = weighting.apply_weights(original_scores, adjusted_weights)
    """

    def __init__(self):
        """Initialize detector and adjuster."""
        self.detector = SkillStyleDetector()
        self.adjuster = WeightAdjuster()

    def detect_style(
        self, skill_title: str, skill_content: str, skill_description: str
    ) -> tuple[SkillStyle, float, str]:
        """Detect skill style from content.

        Args:
            skill_title: Skill title
            skill_content: Full skill markdown content
            skill_description: Brief skill description

        Returns:
            (style, confidence, reasoning)
        """
        try:
            result = self.detector(
                skill_title=skill_title,
                skill_content=skill_content[:2000],  # Limit to 2000 chars
                skill_description=skill_description,
            )

            style = SkillStyle(result.style)
            confidence = min(1.0, max(0.0, float(result.confidence)))

            return style, confidence, result.reasoning
        except Exception as e:
            # Fall back to comprehensive if detection fails
            return SkillStyle.COMPREHENSIVE, 0.5, str(e)

    def get_weights(self, style: SkillStyle | str) -> MetricWeights:
        """Get metric weights for a skill style.

        Args:
            style: SkillStyle enum or string

        Returns:
            MetricWeights object
        """
        return MetricWeights.for_style(style)

    def apply_weights(
        self,
        scores: dict[str, float],
        weights: MetricWeights | dict[str, float] | None = None,
        style: SkillStyle | str | None = None,
    ) -> float:
        """Apply weights to scores to get composite score.

        Args:
            scores: Dict of metric_name -> score
            weights: MetricWeights object or dict. If None, uses style.
            style: SkillStyle to determine weights. Ignored if weights provided.

        Returns:
            Weighted composite score (0.0-1.0)
        """
        if weights is None:
            if style is None:
                style = SkillStyle.COMPREHENSIVE
            weights = self.get_weights(style)

        if isinstance(weights, MetricWeights):
            weights_dict = weights.to_dict()
        else:
            weights_dict = weights

        # Normalize weights
        weight_sum = sum(weights_dict.values())
        if weight_sum > 0:
            weights_dict = {k: v / weight_sum for k, v in weights_dict.items()}

        # Apply weights
        composite = 0.0
        for metric_name, weight in weights_dict.items():
            if metric_name in scores:
                score = scores.get(metric_name, 0.0)
                composite += weight * score

        return min(1.0, max(0.0, composite))

    def recommend_weights(
        self, skill_style: str, current_scores: dict[str, float]
    ) -> tuple[dict[str, float], str, str]:
        """Recommend weights using LLM reasoning.

        Args:
            skill_style: One of "navigation_hub", "comprehensive", "minimal"
            current_scores: Current metric scores

        Returns:
            (weights_dict, reasoning, expected_improvement)
        """
        try:
            result = self.adjuster(skill_style=skill_style, current_scores=current_scores)

            # Parse weights
            weights = result.adjusted_weights
            if isinstance(weights, str):
                # Try to parse string representation
                import json

                weights = json.loads(weights)

            return weights, result.reasoning, result.expected_improvement
        except Exception:
            # Fall back to default weights for style
            style = SkillStyle(skill_style)
            weights = MetricWeights.for_style(style).to_dict()
            return weights, f"Fallback to {style.value}", "Standard weights"


def compute_adaptive_score(
    scores: dict[str, float], style: SkillStyle | str = SkillStyle.COMPREHENSIVE
) -> dict:
    """Compute adaptive score based on skill style.

    Args:
        scores: Dict of metric_name -> score
        style: SkillStyle enum or string

    Returns:
        Dict with:
        - "composite": weighted composite score
        - "weights": weights used
        - "details": per-metric weighted scores
    """
    weighting = AdaptiveMetricWeighting()

    weights = weighting.get_weights(style)
    weights_dict = weights.to_dict()

    # Compute weighted scores
    details = {}
    for metric_name, weight in weights_dict.items():
        score = scores.get(metric_name, 0.0)
        details[metric_name] = {"score": score, "weight": weight, "contribution": score * weight}

    composite = weighting.apply_weights(scores, weights)

    return {
        "composite": composite,
        "style": style if isinstance(style, str) else style.value,
        "weights": weights_dict,
        "details": details,
    }
