"""Tests for parallel analysis module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import dspy
import pytest

from skill_fleet.core.modules.understanding.parallel_analysis import (
    ParallelAnalyzer,
    ParallelUnderstandingAnalysis,
    run_parallel_understanding,
)


class TestParallelUnderstandingAnalysis:
    """Tests for ParallelUnderstandingAnalysis class."""

    @pytest.fixture
    def analyzer(self):
        """Create a parallel analyzer."""
        return ParallelUnderstandingAnalysis()

    @pytest.fixture
    def mock_intent_result(self):
        """Create mock intent result."""
        return dspy.Prediction(
            purpose="Test purpose",
            problem_statement="Test problem",
            target_audience="Test audience",
            value_proposition="Test value",
            skill_type="how_to",
            scope="Test scope",
            success_criteria=["Criterion 1"],
        )

    @pytest.fixture
    def mock_taxonomy_result(self):
        """Create mock taxonomy result."""
        return dspy.Prediction(
            recommended_path="technical/test",
            alternative_paths=["other/test"],
            path_rationale="Test rationale",
            new_directories=[],
            confidence=0.85,
        )

    @pytest.fixture
    def mock_dependency_result(self):
        """Create mock dependency result."""
        return dspy.Prediction(
            prerequisite_skills=["skill1", "skill2"],
            recommended_skills=["skill3"],
            can_extend_existing=True,
            dependency_rationale="Test rationale",
        )

    @pytest.mark.asyncio
    async def test_aforward_returns_prediction(
        self, analyzer, mock_intent_result, mock_taxonomy_result, mock_dependency_result
    ):
        """Test that aforward returns a Prediction."""
        with patch.object(
            analyzer.intent_module, "aforward", AsyncMock(return_value=mock_intent_result)
        ):
            with patch.object(
                analyzer.taxonomy_module, "aforward", AsyncMock(return_value=mock_taxonomy_result)
            ):
                with patch.object(
                    analyzer.dependency_module,
                    "aforward",
                    AsyncMock(return_value=mock_dependency_result),
                ):
                    result = await analyzer.aforward(
                        task_description="Build a React app",
                        requirements={"domain": "technical"},
                    )

        assert isinstance(result, dspy.Prediction)
        assert hasattr(result, "intent_analysis")
        assert hasattr(result, "taxonomy_analysis")
        assert hasattr(result, "dependency_analysis")

    @pytest.mark.asyncio
    async def test_aforward_contains_all_results(
        self, analyzer, mock_intent_result, mock_taxonomy_result, mock_dependency_result
    ):
        """Test that result contains all analysis results."""
        with patch.object(
            analyzer.intent_module, "aforward", AsyncMock(return_value=mock_intent_result)
        ):
            with patch.object(
                analyzer.taxonomy_module, "aforward", AsyncMock(return_value=mock_taxonomy_result)
            ):
                with patch.object(
                    analyzer.dependency_module,
                    "aforward",
                    AsyncMock(return_value=mock_dependency_result),
                ):
                    result = await analyzer.aforward(
                        task_description="Build a React app",
                        requirements={"domain": "technical"},
                    )

        assert "purpose" in result.intent_analysis
        assert "recommended_path" in result.taxonomy_analysis
        assert "prerequisite_skills" in result.dependency_analysis

    @pytest.mark.asyncio
    async def test_handles_module_failure(
        self, analyzer, mock_taxonomy_result, mock_dependency_result
    ):
        """Test handling of module failure."""
        with patch.object(
            analyzer.intent_module,
            "aforward",
            AsyncMock(side_effect=Exception("Intent failed")),
        ):
            with patch.object(
                analyzer.taxonomy_module, "aforward", AsyncMock(return_value=mock_taxonomy_result)
            ):
                with patch.object(
                    analyzer.dependency_module,
                    "aforward",
                    AsyncMock(return_value=mock_dependency_result),
                ):
                    result = await analyzer.aforward(
                        task_description="Build a React app",
                        requirements={"domain": "technical"},
                    )

        assert isinstance(result, dspy.Prediction)
        assert hasattr(result, "intent_analysis")
        assert "error" in result.intent_analysis or "fallback" in result.intent_analysis
        assert result.all_succeeded is False

    @pytest.mark.asyncio
    async def test_parallel_efficiency_calculated(
        self, analyzer, mock_intent_result, mock_taxonomy_result, mock_dependency_result
    ):
        """Test that parallel efficiency is calculated."""
        with patch.object(
            analyzer.intent_module, "aforward", AsyncMock(return_value=mock_intent_result)
        ):
            with patch.object(
                analyzer.taxonomy_module, "aforward", AsyncMock(return_value=mock_taxonomy_result)
            ):
                with patch.object(
                    analyzer.dependency_module,
                    "aforward",
                    AsyncMock(return_value=mock_dependency_result),
                ):
                    result = await analyzer.aforward(
                        task_description="Build a React app",
                        requirements={"domain": "technical"},
                    )

        assert hasattr(result, "parallel_efficiency")
        assert 0.0 <= result.parallel_efficiency <= 1.0
        assert hasattr(result, "execution_time_ms")

    def test_forward_runs_async_version(self, analyzer):
        """Test that forward runs the async version."""
        with patch.object(analyzer, "aforward", AsyncMock(return_value=dspy.Prediction())) as mock:
            analyzer.forward(
                task_description="Test",
                requirements={},
            )
            mock.assert_called_once()


class TestParallelAnalyzer:
    """Tests for ParallelAnalyzer class."""

    @pytest.fixture
    def parallel_analyzer(self):
        """Create a parallel analyzer."""
        return ParallelAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self, parallel_analyzer):
        """Test that analyze returns a dictionary."""
        with patch.object(
            parallel_analyzer, "_run_parallel_intent", AsyncMock(return_value={"purpose": "test"})
        ):
            with patch.object(
                parallel_analyzer,
                "_run_parallel_taxonomy",
                AsyncMock(return_value={"path": "test"}),
            ):
                with patch.object(
                    parallel_analyzer,
                    "_run_parallel_dependencies",
                    AsyncMock(return_value={"deps": []}),
                ):
                    result = await parallel_analyzer.analyze(
                        task_description="Build a React app",
                    )

        assert isinstance(result, dict)
        assert "intent_analysis" in result
        assert "taxonomy_analysis" in result
        assert "dependency_analysis" in result

    @pytest.mark.asyncio
    async def test_handles_errors_in_parallel_methods(self, parallel_analyzer):
        """Test handling of errors in parallel methods."""
        result = await parallel_analyzer._run_parallel_intent("test", {})

        assert isinstance(result, dict)
        # Should return fallback on error
        assert "error" in result or "fallback" in result


class TestRunParallelUnderstanding:
    """Tests for run_parallel_understanding convenience function."""

    def test_returns_prediction(self):
        """Test that function returns a Prediction."""
        mock_result = dspy.Prediction(
            intent_analysis={},
            taxonomy_analysis={},
            dependency_analysis={},
        )

        with patch.object(ParallelUnderstandingAnalysis, "forward", return_value=mock_result):
            result = run_parallel_understanding(
                task_description="Build a React app",
                requirements={"domain": "technical"},
            )

        assert isinstance(result, dspy.Prediction)
