"""Integration tests for the complete workflow with real LLM calls."""

import dspy
import pytest

from skill_fleet.core.dspy.skill_creator import SkillCreationProgram


@pytest.fixture(autouse=True)
def setup_dspy():
    """Configure DSPy with a real LLM for integration tests."""
    lm = dspy.LM("gemini/gemini-3-flash-preview", cache=False)
    dspy.settings.configure(lm=lm)


@pytest.mark.integration
@pytest.mark.anyio
async def test_workflow_with_real_llm():
    """Test the complete workflow with a real LLM call to verify Capability serialization."""
    # Configure DSPy
    lm = dspy.LM("gemini/gemini-3-flash-preview", cache=False)
    dspy.settings.configure(lm=lm)

    # Create program
    program = SkillCreationProgram()

    # Use a simple task that should succeed quickly
    task = "Create a skill that teaches how to use Python list comprehensions"

    # Mock dependencies for aforward
    existing_skills = []
    taxonomy_structure = {"programming": {"python": {}}}

    def mock_parent_skills_getter(path):
        return []

    import json

    # This should not raise a JSON serialization error anymore
    result = await program.aforward(
        task_description=task,
        existing_skills=json.dumps(existing_skills),
        taxonomy_structure=json.dumps(taxonomy_structure),
        user_context={"user_id": "test"},
    )

    # Basic validation
    assert result is not None
    assert "package" in result

    # If we got here without a JSON serialization error, the bug is fixed!
    print(f"✓ Integration test passed! Result: {result.model_dump().keys()}")


@pytest.mark.integration
@pytest.mark.anyio
async def test_capability_serialization():
    """Specifically test that Capability objects are properly serialized."""
    from skill_fleet.core.dspy.modules import InitializeModule  # type: ignore[attr-defined]
    from skill_fleet.core.models import Capability

    # Create module
    module = InitializeModule()

    # Create test data with actual Capability objects
    skill_metadata = {"name": "test-skill", "description": "A test skill"}

    capabilities = [
        Capability(
            name="test-capability",
            description="Test capability",
            test_criteria="Can verify this capability works correctly",
        )
    ]

    taxonomy_path = "programming/python"

    # This should not raise a JSON serialization error
    try:
        result = module.forward(
            skill_metadata=skill_metadata, capabilities=capabilities, taxonomy_path=taxonomy_path
        )
        print("✓ Capability serialization test passed!")
        assert result is not None
        assert "skill_skeleton" in result
        assert "validation_checklist" in result
    except TypeError as e:
        if "not JSON serializable" in str(e):
            pytest.fail(f"Capability serialization failed: {e}")
        raise
