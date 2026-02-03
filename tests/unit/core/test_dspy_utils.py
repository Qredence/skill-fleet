"""Tests for DSPy utility functions."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import dspy
import pytest

from skill_fleet.core.dspy_utils import (
    ModuleRegistry,
    ValidationReward,
    create_ensemble_predictor,
    fast_generation,
    get_module_info,
    high_quality_generation,
    load_compiled_module,
    save_compiled_module,
)


class TestGetModuleInfo:
    """Tests for get_module_info function."""

    def test_returns_basic_info(self):
        """Test that module info includes basic fields."""

        class SimpleModule(dspy.Module):
            def __init__(self):
                super().__init__()
                self.predictor = dspy.Predict("input -> output")

        module = SimpleModule()
        info = get_module_info(module)

        assert "name" in info
        assert info["name"] == "SimpleModule"
        assert "signatures" in info
        assert "nested_modules" in info

    def test_handles_empty_module(self):
        """Test handling of module with no predictors."""

        class EmptyModule(dspy.Module):
            pass

        module = EmptyModule()
        info = get_module_info(module)

        assert info["name"] == "EmptyModule"
        assert info["signatures"] == []


class TestSaveAndLoadCompiledModule:
    """Tests for save_compiled_module and load_compiled_module."""

    def test_save_creates_file(self, tmp_path: Path):
        """Test that saving creates a file."""

        class SimpleModule(dspy.Module):
            def __init__(self):
                super().__init__()
                self.predictor = dspy.Predict("input -> output")

        module = SimpleModule()
        filepath = tmp_path / "test_module.json"

        result = save_compiled_module(module, filepath, metadata={"version": "1.0"})

        assert result.exists()
        assert result.suffix == ".json"

        # Check content
        with open(result) as f:
            data = json.load(f)
        assert data["module_class"] == "SimpleModule"
        assert data["metadata"]["version"] == "1.0"

    def test_load_requires_class(self, tmp_path: Path):
        """Test that loading requires module class."""

        class SimpleModule(dspy.Module):
            pass

        # First save a module
        module = SimpleModule()
        filepath = tmp_path / "test_module.json"
        save_compiled_module(module, filepath)

        # Loading without class should raise error
        with pytest.raises(ValueError, match="module_class"):
            load_compiled_module(filepath)

    def test_load_with_class(self, tmp_path: Path):
        """Test loading with provided class."""

        class SimpleModule(dspy.Module):
            def __init__(self):
                super().__init__()
                self.value = 42

        # Save
        module = SimpleModule()
        filepath = tmp_path / "test_module.json"
        save_compiled_module(module, filepath)

        # Load
        loaded = load_compiled_module(filepath, SimpleModule)

        assert isinstance(loaded, SimpleModule)

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading file that doesn't exist."""

        class SimpleModule(dspy.Module):
            pass

        with pytest.raises(FileNotFoundError):
            load_compiled_module(tmp_path / "nonexistent.json", SimpleModule)


class TestFastGeneration:
    """Tests for fast_generation context manager."""

    def test_context_manager_yields_lm(self):
        """Test that context manager yields the LM."""
        # Create a mock LM with kwargs attribute
        mock_lm = MagicMock()
        mock_lm.kwargs = {"temperature": 0.5}

        with patch("dspy.settings.lm", mock_lm):
            with fast_generation(mock_lm) as lm:
                assert lm is mock_lm

    def test_restores_original_temperature(self):
        """Test that original temperature is restored."""
        mock_lm = MagicMock()
        mock_lm.kwargs = {"temperature": 0.5}

        with patch("dspy.settings.lm", mock_lm):
            with fast_generation(mock_lm):
                assert mock_lm.kwargs["temperature"] == 0.9

        # After context, should be restored
        assert mock_lm.kwargs["temperature"] == 0.5

    def test_handles_no_lm(self):
        """Test handling when no LM is available."""
        with patch("dspy.settings.lm", None):
            with fast_generation() as lm:
                assert lm is None


class TestHighQualityGeneration:
    """Tests for high_quality_generation context manager."""

    def test_sets_low_temperature(self):
        """Test that low temperature is set for quality."""
        mock_lm = MagicMock()
        mock_lm.kwargs = {"temperature": 0.7}

        with patch("dspy.settings.lm", mock_lm):
            with high_quality_generation(mock_lm):
                assert mock_lm.kwargs["temperature"] == 0.2

    def test_restores_temperature(self):
        """Test restoration of original temperature."""
        mock_lm = MagicMock()
        mock_lm.kwargs = {"temperature": 0.7}

        with patch("dspy.settings.lm", mock_lm):
            with high_quality_generation(mock_lm):
                pass

        assert mock_lm.kwargs["temperature"] == 0.7


class TestModuleRegistry:
    """Tests for ModuleRegistry class."""

    def test_register_saves_module(self, tmp_path: Path):
        """Test registering a module."""

        class SimpleModule(dspy.Module):
            pass

        registry = ModuleRegistry(tmp_path)
        module = SimpleModule()

        path = registry.register("test_module", module, {"accuracy": 0.95})

        assert path.exists()
        assert "test_module" in registry.list_versions()

    def test_load_registered_module(self, tmp_path: Path):
        """Test loading a registered module."""

        class SimpleModule(dspy.Module):
            def __init__(self):
                super().__init__()
                self.value = 42

        registry = ModuleRegistry(tmp_path)
        module = SimpleModule()
        registry.register("test_module", module)

        loaded = registry.load("test_module", SimpleModule)
        assert isinstance(loaded, SimpleModule)

    def test_list_versions(self, tmp_path: Path):
        """Test listing registered versions."""

        class SimpleModule(dspy.Module):
            pass

        registry = ModuleRegistry(tmp_path)
        module = SimpleModule()
        registry.register("v1", module, {"accuracy": 0.9})
        registry.register("v2", module, {"accuracy": 0.95})

        versions = registry.list_versions()
        assert "v1" in versions
        assert "v2" in versions

    def test_unregister_removes_module(self, tmp_path: Path):
        """Test unregistering a module."""

        class SimpleModule(dspy.Module):
            pass

        registry = ModuleRegistry(tmp_path)
        module = SimpleModule()
        registry.register("test_module", module)

        registry.unregister("test_module")

        assert "test_module" not in registry.list_versions()

    def test_unregister_missing_raises(self, tmp_path: Path):
        """Test that unregistering missing module raises error."""
        registry = ModuleRegistry(tmp_path)

        with pytest.raises(KeyError):
            registry.unregister("nonexistent")

    def test_load_missing_raises(self, tmp_path: Path):
        """Test that loading missing module raises error."""
        registry = ModuleRegistry(tmp_path)

        class SimpleModule(dspy.Module):
            pass

        with pytest.raises(KeyError):
            registry.load("nonexistent", SimpleModule)


class TestCreateEnsemblePredictor:
    """Tests for create_ensemble_predictor function."""

    def test_creates_ensemble(self):
        """Test creating an ensemble predictor."""

        class SimpleModule(dspy.Module):
            def forward(self, **kwargs):
                return dspy.Prediction(result="test")

        modules = [SimpleModule(), SimpleModule()]
        ensemble = create_ensemble_predictor(modules, aggregation="majority")

        assert ensemble is not None
        assert hasattr(ensemble, "modules")
        assert len(ensemble.modules) == 2

    def test_ensemble_majority_vote(self):
        """Test majority voting in ensemble."""

        class ModA(dspy.Module):
            def forward(self, **kwargs):
                return dspy.Prediction(value="A")

        class ModB(dspy.Module):
            def forward(self, **kwargs):
                return dspy.Prediction(value="B")

        class ModC(dspy.Module):
            def forward(self, **kwargs):
                return dspy.Prediction(value="A")

        modules = [ModA(), ModB(), ModC()]
        ensemble = create_ensemble_predictor(modules, aggregation="majority")

        result = ensemble.forward()
        assert result.value == "A"  # Majority wins

    def test_unknown_aggregation_raises(self):
        """Test that unknown aggregation raises error."""

        class SimpleModule(dspy.Module):
            pass

        modules = [SimpleModule()]
        ensemble = create_ensemble_predictor(modules, aggregation="unknown")

        with pytest.raises(ValueError, match="Unknown aggregation"):
            ensemble.forward()


class TestValidationReward:
    """Tests for ValidationReward class."""

    @pytest.fixture
    def reward_fn(self):
        """Create a validation reward function."""
        return ValidationReward()

    def test_scores_valid_result(self, reward_fn):
        """Test scoring a valid result."""
        result = dspy.Prediction(
            passed=True,
            compliance_score=0.9,
            issues=[],
            critical_issues=[],
            warnings=[],
        )

        score = reward_fn(result)
        assert 0.0 <= score <= 1.0

    def test_scores_with_issues(self, reward_fn):
        """Test scoring a result with issues."""
        result = dspy.Prediction(
            passed=False,
            compliance_score=0.5,
            issues=["Issue 1", "Issue 2"],
            critical_issues=["Critical issue"],
            warnings=["Warning"],
        )

        score = reward_fn(result)
        assert 0.0 <= score <= 1.0

    def test_scores_dict_input(self, reward_fn):
        """Test scoring a dict input."""
        result = {
            "passed": True,
            "compliance_score": 0.8,
            "issues": [],
        }

        score = reward_fn(result)
        assert 0.0 <= score <= 1.0
