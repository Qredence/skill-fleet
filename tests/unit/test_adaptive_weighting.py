"""Unit tests for adaptive metric weighting system."""

from __future__ import annotations

from skill_fleet.core.dspy.metrics.adaptive_weighting import (
    AdaptiveMetricWeighting,
    MetricWeights,
    SkillStyle,
    compute_adaptive_score,
)


class TestMetricWeights:
    """Test MetricWeights dataclass."""

    def test_default_weights(self):
        """Test default weights are balanced."""
        weights = MetricWeights()
        assert weights.skill_quality == 0.25
        assert weights.semantic_f1 == 0.25
        assert weights.entity_f1 == 0.20
        assert weights.readability == 0.20
        assert weights.coverage == 0.10

    def test_to_dict(self):
        """Test conversion to dict."""
        weights = MetricWeights()
        d = weights.to_dict()
        assert d["skill_quality"] == 0.25
        assert len(d) == 5

    def test_for_style_navigation_hub(self):
        """Test navigation_hub style weights."""
        weights = MetricWeights.for_style(SkillStyle.NAVIGATION_HUB)
        assert weights.skill_quality == 0.30  # Higher
        assert weights.readability == 0.35  # Highest
        assert weights.entity_f1 == 0.05  # Lowest

    def test_for_style_minimal(self):
        """Test minimal style weights."""
        weights = MetricWeights.for_style(SkillStyle.MINIMAL)
        assert weights.semantic_f1 == 0.50  # Highest
        assert weights.skill_quality == 0.20  # Lower
        assert weights.coverage == 0.05  # Lowest

    def test_for_style_comprehensive(self):
        """Test comprehensive style weights (default)."""
        weights = MetricWeights.for_style(SkillStyle.COMPREHENSIVE)
        # All metrics balanced
        assert weights.skill_quality == 0.25
        assert weights.semantic_f1 == 0.25

    def test_for_style_string_input(self):
        """Test for_style works with string input."""
        weights = MetricWeights.for_style("navigation_hub")
        assert weights.readability == 0.35

    def test_for_style_invalid_string(self):
        """Test for_style falls back to comprehensive for invalid string."""
        weights = MetricWeights.for_style("invalid_style")
        assert weights.skill_quality == 0.25  # Default


class TestSkillStyleDetector:
    """Test skill style detection."""

    def test_detector_initialization(self):
        """Test detector initializes."""
        weighting = AdaptiveMetricWeighting()
        assert weighting.detector is not None
        assert weighting.adjuster is not None

    def test_detect_style_navigation_hub(self):
        """Test detecting navigation_hub style."""
        weighting = AdaptiveMetricWeighting()

        style, confidence, reasoning = weighting.detect_style(
            skill_title="Python Async Programming Guide",
            skill_content="Clear structure. Multiple examples. Well-organized.",
            skill_description="A comprehensive guide to async programming",
        )

        assert style in [SkillStyle.NAVIGATION_HUB, SkillStyle.COMPREHENSIVE]
        assert 0.0 <= confidence <= 1.0
        assert len(reasoning) > 0

    def test_detect_style_minimal(self):
        """Test detecting minimal style."""
        weighting = AdaptiveMetricWeighting()

        style, confidence, reasoning = weighting.detect_style(
            skill_title="Quick Start",
            skill_content="Short. Concise. Direct approach only.",
            skill_description="Fast intro",
        )

        assert style in [SkillStyle.MINIMAL, SkillStyle.COMPREHENSIVE]
        assert 0.0 <= confidence <= 1.0

    def test_detect_style_fallback(self):
        """Test detection falls back gracefully."""
        weighting = AdaptiveMetricWeighting()

        # Empty inputs should not crash
        style, confidence, reasoning = weighting.detect_style(
            skill_title="",
            skill_content="",
            skill_description="",
        )

        # Should return a valid style
        assert isinstance(style, SkillStyle)
        assert 0.0 <= confidence <= 1.0


class TestAdaptiveMetricWeighting:
    """Test AdaptiveMetricWeighting class."""

    def test_get_weights(self):
        """Test getting weights for a style."""
        weighting = AdaptiveMetricWeighting()

        weights = weighting.get_weights(SkillStyle.COMPREHENSIVE)
        assert weights.skill_quality == 0.25

    def test_apply_weights_empty_dict(self):
        """Test apply_weights with empty weights dict."""
        weighting = AdaptiveMetricWeighting()

        score = weighting.apply_weights({})
        assert score == 0.0

    def test_apply_weights_single_metric(self):
        """Test apply_weights with single metric."""
        weighting = AdaptiveMetricWeighting()

        scores = {"skill_quality": 0.8}
        weights = MetricWeights(
            skill_quality=1.0, semantic_f1=0.0, entity_f1=0.0, readability=0.0, coverage=0.0
        )

        score = weighting.apply_weights(scores, weights)
        assert abs(score - 0.8) < 0.01  # Close to 0.8

    def test_apply_weights_multiple_metrics(self):
        """Test apply_weights with multiple metrics."""
        weighting = AdaptiveMetricWeighting()

        scores = {
            "skill_quality": 0.8,
            "semantic_f1": 0.6,
            "entity_f1": 0.7,
        }

        score = weighting.apply_weights(scores)
        assert 0.0 <= score <= 1.0

    def test_apply_weights_with_style(self):
        """Test apply_weights using style parameter."""
        weighting = AdaptiveMetricWeighting()

        scores = {
            "skill_quality": 0.8,
            "semantic_f1": 0.6,
            "readability": 0.9,
        }

        score = weighting.apply_weights(scores, style=SkillStyle.NAVIGATION_HUB)
        assert 0.0 <= score <= 1.0

    def test_apply_weights_clamps_result(self):
        """Test apply_weights clamps result to [0, 1]."""
        weighting = AdaptiveMetricWeighting()

        # Weights that sum > 1
        weights = {
            "skill_quality": 2.0,
            "semantic_f1": 0.0,
            "entity_f1": 0.0,
            "readability": 0.0,
            "coverage": 0.0,
        }

        scores = {"skill_quality": 0.8}
        score = weighting.apply_weights(scores, weights)
        assert score <= 1.0  # Should be clamped

    def test_recommend_weights(self):
        """Test LLM-based weight recommendation."""
        weighting = AdaptiveMetricWeighting()

        weights, reasoning, improvement = weighting.recommend_weights(
            skill_style="navigation_hub",
            current_scores={"semantic_f1": 0.8, "readability": 0.6},
        )

        assert isinstance(weights, dict)
        assert len(reasoning) > 0
        assert len(improvement) > 0


class TestComputeAdaptiveScore:
    """Test compute_adaptive_score function."""

    def test_compute_adaptive_score_comprehensive(self):
        """Test computing adaptive score for comprehensive style."""
        scores = {
            "skill_quality": 0.8,
            "semantic_f1": 0.75,
            "entity_f1": 0.7,
            "readability": 0.85,
            "coverage": 0.9,
        }

        result = compute_adaptive_score(scores, SkillStyle.COMPREHENSIVE)

        assert "composite" in result
        assert "style" in result
        assert "weights" in result
        assert "details" in result
        assert 0.0 <= result["composite"] <= 1.0

    def test_compute_adaptive_score_navigation_hub(self):
        """Test computing adaptive score for navigation_hub."""
        scores = {
            "skill_quality": 0.8,
            "readability": 0.9,  # High readability weight
            "coverage": 0.85,
        }

        result = compute_adaptive_score(scores, SkillStyle.NAVIGATION_HUB)

        # Readability should have high contribution
        assert result["details"]["readability"]["weight"] > 0.3

    def test_compute_adaptive_score_minimal(self):
        """Test computing adaptive score for minimal."""
        scores = {
            "semantic_f1": 0.95,  # High semantic correctness
            "skill_quality": 0.7,
        }

        result = compute_adaptive_score(scores, SkillStyle.MINIMAL)

        # Semantic should dominate
        assert result["details"]["semantic_f1"]["weight"] > 0.45

    def test_compute_adaptive_score_missing_metrics(self):
        """Test with missing metrics."""
        scores = {"skill_quality": 0.8}

        result = compute_adaptive_score(scores)

        # Should still compute (missing metrics = 0.0 contribution)
        assert result["composite"] >= 0.0

    def test_compute_adaptive_score_string_style(self):
        """Test with string style input."""
        scores = {"semantic_f1": 0.8}

        result = compute_adaptive_score(scores, "navigation_hub")

        assert result["style"] == "navigation_hub"


class TestIntegration:
    """Integration tests for adaptive weighting."""

    def test_full_workflow_detect_and_apply(self):
        """Test full workflow: detect style → get weights → compute score."""
        weighting = AdaptiveMetricWeighting()

        # Step 1: Detect style
        style, confidence, reasoning = weighting.detect_style(
            skill_title="React Hooks Guide",
            skill_content="Covers useState, useEffect, useReducer. Many examples.",
            skill_description="Complete guide to React hooks",
        )

        assert isinstance(style, SkillStyle)

        # Step 2: Get weights
        weights = weighting.get_weights(style)
        assert weights is not None

        # Step 3: Apply to scores
        scores = {
            "skill_quality": 0.8,
            "semantic_f1": 0.75,
            "readability": 0.9,
            "coverage": 0.85,
            "entity_f1": 0.7,
        }

        composite = weighting.apply_weights(scores, weights)
        assert 0.0 <= composite <= 1.0

    def test_different_styles_different_emphasis(self):
        """Test that different styles produce different weights."""
        same_scores = {
            "skill_quality": 0.8,
            "semantic_f1": 0.75,
            "entity_f1": 0.7,
            "readability": 0.85,
            "coverage": 0.9,
        }

        result_nav = compute_adaptive_score(same_scores, SkillStyle.NAVIGATION_HUB)
        result_min = compute_adaptive_score(same_scores, SkillStyle.MINIMAL)

        # Results should differ due to different weights
        assert result_nav["composite"] != result_min["composite"]

    def test_weights_sum_normalization(self):
        """Test that weights are properly normalized."""
        weighting = AdaptiveMetricWeighting()

        for style in [SkillStyle.NAVIGATION_HUB, SkillStyle.COMPREHENSIVE, SkillStyle.MINIMAL]:
            weights = weighting.get_weights(style)
            weight_dict = weights.to_dict()

            # After normalization, sum should be ~1.0
            total = sum(weight_dict.values())
            assert abs(total - 1.0) < 0.01
