"""
Unit tests for ContentGenerationOrchestrator.

Tests the Phase 2 orchestrator that handles skill content generation
with support for different skill styles (navigation_hub, comprehensive, minimal).
"""

import pytest

from skill_fleet.core.dspy.modules.workflows.content_generation import ContentGenerationOrchestrator


@pytest.fixture
def orchestrator() -> ContentGenerationOrchestrator:
    """Create a ContentGenerationOrchestrator fixture."""
    return ContentGenerationOrchestrator()


def test_initialization(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test orchestrator can be initialized."""
    assert orchestrator is not None
    assert hasattr(orchestrator, "generate")
    assert hasattr(orchestrator, "generate_sync")


def test_orchestrator_module_initialization(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test that orchestrator properly initializes its DSPy modules."""
    # The orchestrator should have initialized the generation module
    assert hasattr(orchestrator, "generation_module")
    from skill_fleet.core.dspy.modules import Phase2GenerationModule

    assert isinstance(orchestrator.generation_module, Phase2GenerationModule)


def test_orchestrator_has_expected_methods(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test that orchestrator has all expected methods."""
    expected_methods = [
        "generate",
        "generate_sync",
    ]

    for method_name in expected_methods:
        assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"
        assert callable(getattr(orchestrator, method_name)), f"{method_name} is not callable"


def test_generate_method_signature(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test that generate method has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.generate)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        "understanding",
        "plan",
        "skill_style",
        "user_feedback",
        "enable_mlflow",
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_generate_sync_method_signature(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test that generate_sync method has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.generate_sync)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        "understanding",
        "plan",
        "skill_style",
        "user_feedback",
        "enable_mlflow",
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_orchestrator_accepts_different_skill_styles(
    orchestrator: ContentGenerationOrchestrator,
) -> None:
    """Test that orchestrator accepts different skill style values."""
    import inspect

    sig = inspect.signature(orchestrator.generate)
    skill_style_param = sig.parameters.get("skill_style")

    assert skill_style_param is not None
    # Check that there's a default value
    assert skill_style_param.default is not inspect.Parameter.empty


def test_orchestrator_handles_user_feedback_parameter(
    orchestrator: ContentGenerationOrchestrator,
) -> None:
    """Test that orchestrator accepts user feedback parameter."""
    import inspect

    sig = inspect.signature(orchestrator.generate)
    user_feedback_param = sig.parameters.get("user_feedback")

    assert user_feedback_param is not None
    # Check that there's a default value (empty string)
    assert user_feedback_param.default == ""


def test_orchestrator_handles_mlflow_parameter(orchestrator: ContentGenerationOrchestrator) -> None:
    """Test that orchestrator accepts enable_mlflow parameter."""
    import inspect

    sig = inspect.signature(orchestrator.generate)
    mlflow_param = sig.parameters.get("enable_mlflow")

    assert mlflow_param is not None
    # Check that the default is True
    assert mlflow_param.default is True
