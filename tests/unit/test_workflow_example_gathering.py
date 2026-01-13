"""Tests for Step 0: Example Gathering workflow.

Tests for:
- UserExample model
- ExampleGatheringConfig model
- ExampleGatheringSession model
- GatherExamplesModule
"""

import json

import pytest

from skill_fleet.core.dspy.modules import GatherExamplesModule
from skill_fleet.core.models import (
    ClarifyingQuestion,
    ExampleGatheringConfig,
    ExampleGatheringSession,
    UserExample,
)

# =============================================================================
# UserExample Tests
# =============================================================================


def test_user_example_minimal() -> None:
    """Test creating a minimal UserExample."""
    ex = UserExample(
        input_description="User asks to rotate image",
        expected_output="Image is rotated 90 degrees",
    )
    assert ex.input_description == "User asks to rotate image"
    assert ex.expected_output == "Image is rotated 90 degrees"
    assert ex.code_snippet == ""
    assert ex.trigger_phrase == ""
    assert ex.edge_case is False
    assert ex.notes == ""


def test_user_example_full() -> None:
    """Test creating a complete UserExample."""
    ex = UserExample(
        input_description="User provides image file path",
        expected_output="Image rotated 90 degrees clockwise",
        code_snippet="img.rotate(90, expand=True)",
        trigger_phrase="rotate this image 90 degrees",
        edge_case=True,
        notes="Must preserve aspect ratio",
    )
    assert ex.input_description == "User provides image file path"
    assert ex.expected_output == "Image rotated 90 degrees clockwise"
    assert ex.code_snippet == "img.rotate(90, expand=True)"
    assert ex.trigger_phrase == "rotate this image 90 degrees"
    assert ex.edge_case is True
    assert ex.notes == "Must preserve aspect ratio"


def test_user_example_serialization() -> None:
    """Test UserExample can be serialized to dict/JSON."""
    ex = UserExample(
        input_description="Test input",
        expected_output="Test output",
        code_snippet="print('test')",
        trigger_phrase="do test",
        edge_case=True,
    )
    data = ex.model_dump()
    assert isinstance(data, dict)
    assert data["input_description"] == "Test input"
    assert data["edge_case"] is True

    # Should be JSON serializable
    json_str = json.dumps(data)
    assert "Test input" in json_str


# =============================================================================
# ExampleGatheringConfig Tests
# =============================================================================


def test_example_gathering_config_defaults() -> None:
    """Test ExampleGatheringConfig with default values."""
    cfg = ExampleGatheringConfig()
    assert cfg.min_examples == 3
    assert cfg.readiness_threshold == 0.8
    assert cfg.max_questions == 5
    assert cfg.max_rounds == 3


def test_example_gathering_config_custom() -> None:
    """Test ExampleGatheringConfig with custom values."""
    cfg = ExampleGatheringConfig(
        min_examples=5,
        readiness_threshold=0.9,
        max_questions=10,
        max_rounds=5,
    )
    assert cfg.min_examples == 5
    assert cfg.readiness_threshold == 0.9
    assert cfg.max_questions == 10
    assert cfg.max_rounds == 5


def test_example_gathering_config_validation() -> None:
    """Test ExampleGatheringConfig validation."""
    # min_examples must be 1-10
    with pytest.raises(ValueError):
        ExampleGatheringConfig(min_examples=0)
    with pytest.raises(ValueError):
        ExampleGatheringConfig(min_examples=11)

    # readiness_threshold must be 0.0-1.0
    with pytest.raises(ValueError):
        ExampleGatheringConfig(readiness_threshold=-0.1)
    with pytest.raises(ValueError):
        ExampleGatheringConfig(readiness_threshold=1.1)


# =============================================================================
# ExampleGatheringSession Tests
# =============================================================================


def test_example_gathering_session_initialization() -> None:
    """Test ExampleGatheringSession initialization."""
    session = ExampleGatheringSession(task_description="Create an image rotator skill")
    assert session.task_description == "Create an image rotator skill"
    assert isinstance(session.config, ExampleGatheringConfig)
    assert session.questions_asked == []
    assert session.collected_examples == []
    assert session.terminology == {}
    assert session.refined_task == ""
    assert session.readiness_score == 0.0
    assert session.is_ready is False
    assert session.current_round == 0


def test_example_gathering_session_add_examples() -> None:
    """Test adding examples to a session."""
    session = ExampleGatheringSession(task_description="Create a skill")
    ex = UserExample(
        input_description="Input 1",
        expected_output="Output 1",
    )
    session.collected_examples.append(ex)
    assert len(session.collected_examples) == 1
    assert session.collected_examples[0].input_description == "Input 1"


def test_example_gathering_session_update_terminology() -> None:
    """Test updating terminology in a session."""
    session = ExampleGatheringSession(task_description="Create a skill")
    session.terminology["skill"] = "A reusable capability that an agent can invoke"
    session.terminology["example"] = "A concrete usage pattern"
    assert len(session.terminology) == 2
    assert "skill" in session.terminology


def test_example_gathering_session_mark_ready() -> None:
    """Test marking session as ready."""
    session = ExampleGatheringSession(task_description="Create a skill")
    assert session.is_ready is False

    # Add examples to meet minimum
    for i in range(3):
        session.collected_examples.append(
            UserExample(
                input_description=f"Example {i}",
                expected_output=f"Output {i}",
            )
        )
    session.readiness_score = 0.85
    session.is_ready = True

    assert session.is_ready is True
    assert len(session.collected_examples) >= 3
    assert session.readiness_score >= 0.8


# =============================================================================
# GatherExamplesModule Tests
# =============================================================================


def test_gather_examples_module_creation() -> None:
    """Test GatherExamplesModule can be instantiated."""
    pytest.importorskip("dspy")
    module = GatherExamplesModule()
    assert module is not None
    assert hasattr(module, "forward")
    assert hasattr(module, "aforward")
    assert hasattr(module, "gather")


def test_gather_examples_module_forward_signature() -> None:
    """Test GatherExamplesModule.forward() has correct signature."""
    pytest.importorskip("dspy")
    module = GatherExamplesModule()

    # Should accept these parameters
    import inspect

    sig = inspect.signature(module.forward)
    params = list(sig.parameters.keys())

    assert "task_description" in params
    assert "user_responses" in params
    assert "collected_examples" in params
    assert "config" in params


def test_gather_examples_module_aforward_signature() -> None:
    """Test GatherExamplesModule.aforward() has correct signature."""
    pytest.importorskip("dspy")
    module = GatherExamplesModule()

    # Should accept these parameters
    import inspect

    sig = inspect.signature(module.aforward)
    params = list(sig.parameters.keys())

    assert "task_description" in params
    assert "config" in params


# =============================================================================
# Integration Tests
# =============================================================================


def test_full_example_gathering_workflow() -> None:
    """Test a complete example gathering workflow."""
    pytest.importorskip("dspy")

    # Create session
    session = ExampleGatheringSession(task_description="Create a skill for image rotation")

    # Add a clarifying question
    q = ClarifyingQuestion(
        id="q1",
        question="What image formats should be supported?",
        context="To determine dependencies",
        options=[],
    )
    session.questions_asked.append(q)

    # Simulate user response
    ex1 = UserExample(
        input_description="User uploads PNG image",
        expected_output="PNG rotated 90 degrees",
        trigger_phrase="rotate png image",
    )
    session.collected_examples.append(ex1)

    # Update terminology
    session.terminology["PNG"] = "Portable Network Graphics format"

    # Mark as ready
    session.readiness_score = 0.85
    session.is_ready = True

    # Verify state
    assert len(session.questions_asked) == 1
    assert len(session.collected_examples) == 1
    assert len(session.terminology) == 1
    assert session.is_ready is True
    assert session.readiness_score >= 0.8


def test_example_gathering_session_serialization() -> None:
    """Test ExampleGatheringSession can be serialized."""
    session = ExampleGatheringSession(task_description="Test skill")
    session.collected_examples.append(
        UserExample(
            input_description="Test",
            expected_output="Test output",
        )
    )
    session.refined_task = "Refined task description"
    session.readiness_score = 0.75

    # Should be serializable
    data = session.model_dump()
    assert isinstance(data, dict)
    assert data["task_description"] == "Test skill"
    assert len(data["collected_examples"]) == 1

    # Should be JSON serializable
    json_str = json.dumps(data, default=str)
    assert "Test skill" in json_str


def test_example_gathering_config_serialization() -> None:
    """Test ExampleGatheringConfig can be serialized."""
    cfg = ExampleGatheringConfig(
        min_examples=4,
        readiness_threshold=0.85,
        max_questions=6,
        max_rounds=4,
    )

    # model_dump
    data = cfg.model_dump()
    assert isinstance(data, dict)
    assert data["min_examples"] == 4

    # model_dump_json
    json_str = cfg.model_dump_json()
    assert "4" in json_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
