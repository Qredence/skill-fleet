"""Unit tests for Capability serialization bug fix."""

import json
from unittest.mock import Mock, patch

import pytest

from skill_fleet.core.dspy.modules import InitializeModule
from skill_fleet.core.models import Capability


def test_initialize_module_serializes_capabilities():
    """Test that InitializeModule properly serializes Capability objects to JSON."""
    # Create module
    module = InitializeModule()

    # Create test data with actual Capability Pydantic models
    skill_metadata = {"name": "test-skill", "description": "A test skill for serialization"}

    capabilities = [
        Capability(
            name="test_capability_one",
            description="First test capability",
            test_criteria="Verify capability one works",
        ),
        Capability(
            name="test_capability_two",
            description="Second test capability",
            test_criteria="Verify capability two works",
        ),
    ]

    taxonomy_path = "programming/python/basics"

    # Mock the DSPy signature call to avoid real LLM calls
    mock_result = Mock()
    mock_result.skill_skeleton = json.dumps(
        {"title": "Test Skill", "sections": ["Introduction", "Usage"]}
    )
    mock_result.validation_checklist = json.dumps(["Check implementation", "Verify examples"])

    with patch.object(module, "initialize", return_value=mock_result):
        # This should NOT raise TypeError about JSON serialization
        try:
            result = module.forward(
                skill_metadata=skill_metadata,
                capabilities=capabilities,
                taxonomy_path=taxonomy_path,
            )

            # Verify result structure
            assert "skill_skeleton" in result
            assert "validation_checklist" in result
            assert isinstance(result["skill_skeleton"], dict)
            assert isinstance(result["validation_checklist"], list)

        except TypeError as e:
            if "not JSON serializable" in str(e):
                pytest.fail(f"Capability serialization failed: {e}")
            raise


def test_capability_model_dump():
    """Test that Capability.model_dump() produces correct JSON-serializable dict."""
    capability = Capability(
        name="example_capability",
        description="Example for testing",
        test_criteria="Verify it works",
    )

    # Test model_dump() returns dict
    dumped = capability.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["name"] == "example_capability"
    assert dumped["description"] == "Example for testing"
    assert dumped["test_criteria"] == "Verify it works"

    # Test it's JSON serializable
    try:
        json_str = json.dumps(dumped)
        assert isinstance(json_str, str)

        # Verify round-trip
        reloaded = json.loads(json_str)
        assert reloaded == dumped
    except TypeError as e:
        pytest.fail(f"model_dump() result not JSON serializable: {e}")


def test_capabilities_list_serialization():
    """Test that a list of Capabilities can be serialized with our pattern."""
    capabilities = [
        Capability(
            name=f"capability_{i}",
            description=f"Capability number {i}",
            test_criteria=f"Test criteria {i}",
        )
        for i in range(3)
    ]

    # This is the pattern we use in InitializeModule
    serialized = [c.model_dump() if hasattr(c, "model_dump") else c for c in capabilities]

    # Should be JSON serializable
    try:
        json_str = json.dumps(serialized, indent=2)
        assert isinstance(json_str, str)

        # Verify structure
        reloaded = json.loads(json_str)
        assert len(reloaded) == 3
        assert all("name" in item for item in reloaded)
        assert reloaded[0]["name"] == "capability_0"
        assert reloaded[2]["description"] == "Capability number 2"

    except TypeError as e:
        pytest.fail(f"Capability list serialization failed: {e}")
