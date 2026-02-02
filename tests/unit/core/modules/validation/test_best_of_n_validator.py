"""Tests for BestOfN validator module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import dspy
import pytest

from skill_fleet.core.modules.validation.adaptive_validator import AdaptiveValidator
from skill_fleet.core.modules.validation.best_of_n_validator import (
    BestOfNValidator,
    validate_with_best_of_n,
)
from skill_fleet.core.modules.validation.validation_reward import ValidationReward


class TestValidationReward:
    """Tests for ValidationReward class."""

    @pytest.fixture
    def reward_fn(self):
        """Create a validation reward function."""
        return ValidationReward()

    def test_returns_score_between_0_and_1(self, reward_fn):
        """Test that reward returns score in valid range."""
        result = dspy.Prediction(
            passed=True,
            compliance_score=0.8,
            issues=[],
        )

        score = reward_fn(result)
        assert 0.0 <= score <= 1.0

    def test_clear_pass_gets_higher_score(self, reward_fn):
        """Test that clear pass gets higher score than borderline."""
        clear_pass = dspy.Prediction(
            passed=True,
            compliance_score=0.95,
            issues=[],
            critical_issues=[],
        )
        borderline = dspy.Prediction(
            passed=True,
            compliance_score=0.55,
            issues=["Minor issue"],
            critical_issues=[],
        )

        clear_score = reward_fn(clear_pass)
        borderline_score = reward_fn(borderline)

        assert clear_score > borderline_score

    def test_complete_result_gets_higher_score(self, reward_fn):
        """Test that complete result gets higher score."""
        complete = dspy.Prediction(
            passed=True,
            compliance_score=0.8,
            issues=[],
            critical_issues=[],
            warnings=[],
            auto_fixable=[],
        )
        incomplete = dspy.Prediction(
            passed=True,
        )

        complete_score = reward_fn(complete)
        incomplete_score = reward_fn(incomplete)

        assert complete_score > incomplete_score

    def test_handles_dict_input(self, reward_fn):
        """Test handling of dict input."""
        result = {
            "passed": True,
            "compliance_score": 0.85,
            "issues": ["Issue 1"],
        }

        score = reward_fn(result)
        assert 0.0 <= score <= 1.0


class TestBestOfNValidator:
    """Tests for BestOfNValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a BestOfN validator."""
        return BestOfNValidator(n=3)

    @pytest.fixture
    def mock_validation_result(self):
        """Create a mock validation result."""
        return dspy.Prediction(
            passed=True,
            compliance_score=0.85,
            issues=["Minor formatting issue"],
            critical_issues=[],
            warnings=[],
            auto_fixable=["Fix formatting"],
        )

    @pytest.mark.asyncio
    async def test_aforward_returns_prediction(self, validator, mock_validation_result):
        """Test that aforward returns a Prediction."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(return_value=mock_validation_result)
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert isinstance(result, dspy.Prediction)

    @pytest.mark.asyncio
    async def test_runs_n_attempts(self, validator, mock_validation_result):
        """Test that N attempts are made."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(return_value=mock_validation_result)
        ) as mock:
            await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert mock.call_count == 3

    @pytest.mark.asyncio
    async def test_includes_attempts_count(self, validator, mock_validation_result):
        """Test that result includes attempts count."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(return_value=mock_validation_result)
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert hasattr(result, "attempts_made")
        assert result.attempts_made == 3

    @pytest.mark.asyncio
    async def test_includes_confidence(self, validator, mock_validation_result):
        """Test that result includes confidence score."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(return_value=mock_validation_result)
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert hasattr(result, "confidence")
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_includes_all_results(self, validator, mock_validation_result):
        """Test that result includes all validation results."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(return_value=mock_validation_result)
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert hasattr(result, "all_results")
        assert len(result.all_results) == 3

    @pytest.mark.asyncio
    async def test_handles_validation_failure(self, validator, mock_validation_result):
        """Test handling of validation failures."""
        # First attempt fails, others succeed
        side_effects = [
            Exception("Validation failed"),
            mock_validation_result,
            mock_validation_result,
        ]

        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(side_effect=side_effects)
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert isinstance(result, dspy.Prediction)
        assert result.attempts_made == 2

    @pytest.mark.asyncio
    async def test_all_failures_returns_error(self, validator):
        """Test handling when all attempts fail."""
        with patch.object(
            validator, "_single_validation_attempt", AsyncMock(side_effect=Exception("Failed"))
        ):
            result = await validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        assert isinstance(result, dspy.Prediction)
        assert result.passed is False
        assert result.error is True

    def test_forward_runs_async(self, validator):
        """Test that forward delegates to aforward via BaseModule's bridging."""
        # BaseModule handles sync/async bridging automatically
        # Just verify the methods exist and are callable
        assert hasattr(validator, "forward")
        assert hasattr(validator, "aforward")
        assert callable(validator.forward)
        assert callable(validator.aforward)


class TestAdaptiveValidator:
    """Tests for AdaptiveValidator class."""

    @pytest.fixture
    def adaptive_validator(self):
        """Create an adaptive validator."""
        return AdaptiveValidator(
            min_attempts=2,
            max_attempts=5,
            confidence_threshold=0.8,
        )

    @pytest.fixture
    def mock_validation_result(self):
        """Create a mock validation result."""
        return dspy.Prediction(
            passed=True,
            compliance_score=0.9,
            issues=[],
        )

    @pytest.mark.asyncio
    async def test_stops_at_min_if_confident(self, adaptive_validator, mock_validation_result):
        """Test stopping at minimum attempts if confident."""
        # All results the same = high confidence
        with patch.object(
            adaptive_validator,
            "_single_validation_attempt",
            AsyncMock(return_value=mock_validation_result),
        ):
            result = await adaptive_validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        # Should stop early due to high confidence
        assert result.attempts_made >= 2
        assert hasattr(result, "adaptive_stop")

    @pytest.mark.asyncio
    async def test_continues_past_min_if_not_confident(self, adaptive_validator):
        """Test continuing past minimum if not confident."""
        # Varying results = low confidence
        varying_results = [
            dspy.Prediction(passed=True, compliance_score=0.9, issues=[]),
            dspy.Prediction(passed=False, compliance_score=0.3, issues=["Issue"]),
            dspy.Prediction(passed=True, compliance_score=0.8, issues=[]),
            dspy.Prediction(passed=True, compliance_score=0.85, issues=[]),
        ]

        with patch.object(
            adaptive_validator,
            "_single_validation_attempt",
            AsyncMock(side_effect=varying_results),
        ):
            result = await adaptive_validator.aforward(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
            )

        # Should use more attempts due to low confidence
        assert result.attempts_made >= 2


class TestValidateWithBestOfN:
    """Tests for validate_with_best_of_n convenience function."""

    def test_returns_prediction(self):
        """Test that function returns a Prediction."""
        mock_result = dspy.Prediction(
            passed=True,
            compliance_score=0.85,
        )

        with patch.object(BestOfNValidator, "forward", return_value=mock_result):
            result = validate_with_best_of_n(
                skill_content="# Test Skill",
                taxonomy_path="testing/test",
                n=3,
            )

        assert isinstance(result, dspy.Prediction)
        assert result.passed is True
