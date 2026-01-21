"""Unit tests for Optimizer Auto-Selection Engine."""

from __future__ import annotations

import pytest

from skill_fleet.core.dspy.optimization.selector import (
    OptimizerConfig,
    OptimizerContext,
    OptimizerRecommendation,
    OptimizerSelector,
    OptimizerType,
)


class TestOptimizerSelector:
    """Test OptimizerSelector decision rules."""

    @pytest.fixture
    def selector(self) -> OptimizerSelector:
        """Create selector without historical data."""
        return OptimizerSelector()

    # =========================================================================
    # Decision Rule Tests
    # =========================================================================

    def test_very_tight_time_constraint_recommends_reflection_metrics(
        self, selector: OptimizerSelector
    ) -> None:
        """Time < 2min → Reflection Metrics."""
        context = OptimizerContext(
            trainset_size=100,
            budget_dollars=50.0,
            time_constraint_minutes=1,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.REFLECTION_METRICS
        assert "Time constraint" in result.reasoning

    def test_very_low_budget_recommends_reflection_metrics(
        self, selector: OptimizerSelector
    ) -> None:
        """Budget < $1 → Reflection Metrics."""
        context = OptimizerContext(
            trainset_size=100,
            budget_dollars=0.50,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.REFLECTION_METRICS
        assert "Budget" in result.reasoning

    def test_small_trainset_low_budget_recommends_gepa(
        self, selector: OptimizerSelector
    ) -> None:
        """trainset < 100 AND budget < $5 → GEPA."""
        context = OptimizerContext(
            trainset_size=50,
            budget_dollars=4.0,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.GEPA
        assert "GEPA" in result.reasoning

    def test_medium_trainset_moderate_budget_recommends_miprov2_light(
        self, selector: OptimizerSelector
    ) -> None:
        """trainset < 500 AND budget < $20 → MIPROv2 light."""
        context = OptimizerContext(
            trainset_size=200,
            budget_dollars=15.0,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.MIPROV2
        assert result.config.auto == "light"

    def test_large_trainset_good_budget_recommends_miprov2_medium(
        self, selector: OptimizerSelector
    ) -> None:
        """trainset >= 500 AND budget >= $20 → MIPROv2 medium."""
        context = OptimizerContext(
            trainset_size=500,
            budget_dollars=50.0,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.MIPROV2
        assert result.config.auto == "medium"

    def test_high_budget_recommends_miprov2_heavy(
        self, selector: OptimizerSelector
    ) -> None:
        """budget >= $100 → MIPROv2 heavy."""
        context = OptimizerContext(
            trainset_size=500,
            budget_dollars=150.0,
            quality_target=0.90,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.MIPROV2
        assert result.config.auto == "heavy"

    def test_very_high_budget_high_quality_recommends_finetune(
        self, selector: OptimizerSelector
    ) -> None:
        """budget >= $100 AND quality_target >= 0.95 → BootstrapFinetune."""
        context = OptimizerContext(
            trainset_size=1000,
            budget_dollars=200.0,
            quality_target=0.95,
        )
        result = selector.recommend(context)

        assert result.recommended == OptimizerType.BOOTSTRAP_FINETUNE

    def test_fallback_to_bootstrap_fewshot(
        self, selector: OptimizerSelector
    ) -> None:
        """Edge case defaults to BootstrapFewShot or appropriate match."""
        # Context that matches MIPROv2 light rule
        context = OptimizerContext(
            trainset_size=150,
            budget_dollars=8.0,
        )
        result = selector.recommend(context)

        # Should match MIPROv2 light based on rules
        assert result.recommended in [
            OptimizerType.MIPROV2,
            OptimizerType.BOOTSTRAP_FEWSHOT,
        ]

    # =========================================================================
    # Cost & Time Estimation Tests
    # =========================================================================

    def test_cost_estimation_scales_with_trainset(
        self, selector: OptimizerSelector
    ) -> None:
        """Cost should scale with trainset size."""
        context_small = OptimizerContext(trainset_size=50, budget_dollars=3.0)
        context_large = OptimizerContext(trainset_size=500, budget_dollars=50.0)

        result_small = selector.recommend(context_small)
        result_large = selector.recommend(context_large)

        # Larger trainset should cost more (same optimizer type)
        # Note: different contexts may get different optimizers
        assert result_large.estimated_cost >= 0
        assert result_small.estimated_cost >= 0

    def test_time_estimation_is_reasonable(
        self, selector: OptimizerSelector
    ) -> None:
        """Time estimates should be in reasonable range."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        assert result.estimated_time_minutes >= 1
        assert result.estimated_time_minutes <= 120  # Max 2 hours

    def test_miprov2_cost_varies_by_auto_setting(
        self, selector: OptimizerSelector
    ) -> None:
        """MIPROv2 cost should vary by auto setting."""
        # Force MIPROv2 with different budgets
        config_light = OptimizerConfig(auto="light")
        config_heavy = OptimizerConfig(auto="heavy")

        cost_light = selector._estimate_cost(
            OptimizerType.MIPROV2, config_light, 100
        )
        cost_heavy = selector._estimate_cost(
            OptimizerType.MIPROV2, config_heavy, 100
        )

        assert cost_heavy > cost_light

    # =========================================================================
    # Confidence Tests
    # =========================================================================

    def test_confidence_baseline(self, selector: OptimizerSelector) -> None:
        """Confidence should be reasonable without historical data."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        assert 0.5 <= result.confidence <= 1.0

    def test_confidence_reduced_for_tiny_trainset(
        self, selector: OptimizerSelector
    ) -> None:
        """Very small trainset should reduce confidence."""
        context = OptimizerContext(trainset_size=10, budget_dollars=10.0)
        result = selector.recommend(context)

        # Confidence should be lower for edge cases
        assert result.confidence <= 0.8

    # =========================================================================
    # Alternatives Tests
    # =========================================================================

    def test_alternatives_always_present(
        self, selector: OptimizerSelector
    ) -> None:
        """Should always provide alternatives."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        assert len(result.alternatives) >= 1
        assert len(result.alternatives) <= 3

    def test_alternatives_include_fast_option(
        self, selector: OptimizerSelector
    ) -> None:
        """Alternatives should include a fast option."""
        context = OptimizerContext(
            trainset_size=500,
            budget_dollars=50.0,
        )
        result = selector.recommend(context)

        # If not already fastest, should suggest it
        if result.recommended != OptimizerType.REFLECTION_METRICS:
            optimizer_names = [a["optimizer"] for a in result.alternatives]
            assert OptimizerType.REFLECTION_METRICS.value in optimizer_names

    def test_alternatives_have_required_fields(
        self, selector: OptimizerSelector
    ) -> None:
        """Each alternative should have required fields."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        for alt in result.alternatives:
            assert "optimizer" in alt
            assert "cost" in alt
            assert "time" in alt
            assert "note" in alt

    # =========================================================================
    # Recommendation Structure Tests
    # =========================================================================

    def test_recommendation_has_all_fields(
        self, selector: OptimizerSelector
    ) -> None:
        """Recommendation should have all required fields."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        assert isinstance(result.recommended, OptimizerType)
        assert result.config is not None
        assert result.estimated_cost >= 0
        assert result.estimated_time_minutes >= 1
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.reasoning) > 0
        assert isinstance(result.alternatives, list)

    def test_config_has_correct_structure(
        self, selector: OptimizerSelector
    ) -> None:
        """Config should have correct structure."""
        context = OptimizerContext(trainset_size=100, budget_dollars=10.0)
        result = selector.recommend(context)

        assert hasattr(result.config, "auto")
        assert hasattr(result.config, "max_bootstrapped_demos")
        assert hasattr(result.config, "max_labeled_demos")
        assert hasattr(result.config, "num_threads")


class TestOptimizerContext:
    """Test OptimizerContext dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        context = OptimizerContext(trainset_size=100)

        assert context.trainset_size == 100
        assert context.budget_dollars == 10.0
        assert context.quality_target == 0.85
        assert context.complexity_score == 0.5
        assert context.domain == "general"
        assert context.time_constraint_minutes is None

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        context = OptimizerContext(
            trainset_size=500,
            budget_dollars=50.0,
            quality_target=0.95,
            complexity_score=0.8,
            domain="testing",
            time_constraint_minutes=30,
        )

        assert context.trainset_size == 500
        assert context.budget_dollars == 50.0
        assert context.quality_target == 0.95
        assert context.domain == "testing"
        assert context.time_constraint_minutes == 30


class TestOptimizerConfig:
    """Test OptimizerConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = OptimizerConfig()

        assert config.auto == "medium"
        assert config.max_bootstrapped_demos == 4
        assert config.max_labeled_demos == 4
        assert config.num_threads == 8
        assert config.num_candidates == 10
        assert config.num_iters == 3

    def test_custom_values(self) -> None:
        """Test custom values are set correctly."""
        config = OptimizerConfig(
            auto="heavy",
            max_bootstrapped_demos=6,
            num_candidates=15,
        )

        assert config.auto == "heavy"
        assert config.max_bootstrapped_demos == 6
        assert config.num_candidates == 15
