"""Tests for understanding modules."""

from unittest.mock import Mock, patch

import dspy
import pytest

from skill_fleet.common.serialization import normalize_dict_output
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.understanding.requirements import GatherRequirementsModule


class TestBaseModule:
    """Test BaseModule functionality."""

    def test_base_module_can_be_instantiated(self):
        """Should create instance without errors."""
        module = BaseModule()
        assert module is not None

    def test_forward_raises_not_implemented(self):
        """Should require subclasses to implement forward."""
        module = BaseModule()
        with pytest.raises(NotImplementedError):
            module.forward()

    def test_validate_result_with_dict(self):
        """Should validate dict results."""
        module = BaseModule()
        result = {"field1": "value1", "field2": "value2"}
        assert module._validate_result(result, ["field1", "field2"]) is True

    def test_validate_result_missing_fields(self):
        """Should detect missing fields."""
        module = BaseModule()
        result = {"field1": "value1"}
        assert module._validate_result(result, ["field1", "field2"]) is False

    def test_sanitize_input_truncates_long_strings(self):
        """Should truncate inputs over max length."""
        module = BaseModule()
        long_input = "x" * 20000
        result = module._sanitize_input(long_input, max_length=1000)
        assert len(result) < 1500  # Should be truncated
        assert "truncated" in result

    def test_sanitize_input_handles_none(self):
        """Should handle None input."""
        module = BaseModule()
        result = module._sanitize_input(None)
        assert result == ""


class TestGatherRequirementsModule:
    """Test GatherRequirementsModule."""

    def test_module_can_be_instantiated(self):
        """Should create instance with ChainOfThought."""
        module = GatherRequirementsModule()
        assert module is not None
        assert hasattr(module, "gather")

    @patch("skill_fleet.core.modules.understanding.requirements.dspy.ChainOfThought")
    def test_forward_returns_structured_output(self, mock_cot):
        """Should return dict with required fields."""
        # Mock the ChainOfThought result
        mock_result = Mock()
        mock_result.domain = "technical"
        mock_result.category = "web"
        mock_result.target_level = "intermediate"
        mock_result.topics = ["react", "components"]
        mock_result.constraints = ["typescript"]
        mock_result.ambiguities = []

        mock_cot.return_value.return_value = mock_result

        module = GatherRequirementsModule()
        result = module.forward(task_description="Build a React app", user_context={})

        assert isinstance(result, dspy.Prediction)
        result_dict = normalize_dict_output(result)
        assert result_dict["domain"] == "technical"
        assert result_dict["category"] == "web"
        assert "topics" in result_dict

    @pytest.mark.skip(reason="Integration test - requires actual LM configuration")
    def test_forward_handles_empty_ambiguities(self):
        """Should handle tasks with no ambiguities."""
        # Integration test - requires actual LM
        module = GatherRequirementsModule()

        result = module.forward(
            task_description="Create a Python function to format dates",
            user_context={"experience": "beginner"},
        )

        # Should return structured result
        assert "domain" in result
        assert "topics" in result
        assert isinstance(result.get("ambiguities"), list)

    @pytest.mark.skip(reason="Integration test - requires actual LM configuration")
    def test_forward_detects_ambiguities(self):
        """Should detect ambiguities in vague descriptions."""
        module = GatherRequirementsModule()

        result = module.forward(task_description="Help me build something", user_context={})

        # Vague task should have ambiguities
        assert len(result.get("ambiguities", [])) > 0


class TestModuleIntegration:
    """Integration tests for understanding modules."""

    @pytest.mark.skip(reason="Integration test - requires actual LM configuration")
    def test_requirements_module_output_format(self):
        """Requirements output should have correct structure."""
        module = GatherRequirementsModule()

        result = module.forward(task_description="Build a REST API with FastAPI", user_context={})

        # Check all required fields
        required = ["domain", "category", "target_level", "topics", "constraints", "ambiguities"]
        for field in required:
            assert field in result, f"Missing field: {field}"

        # Check types
        assert isinstance(result["topics"], list)
        assert isinstance(result["constraints"], list)
        assert isinstance(result["ambiguities"], list)
