"""
Unit tests for QualityAssuranceOrchestrator.

Tests the Phase 3 orchestrator that handles skill validation,
refinement, and quality assessment.
"""

import pytest

from skill_fleet.workflows.quality_assurance import QualityAssuranceOrchestrator


@pytest.fixture
def orchestrator() -> QualityAssuranceOrchestrator:
    """Create a QualityAssuranceOrchestrator fixture."""
    return QualityAssuranceOrchestrator()


def test_initialization(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test orchestrator can be initialized."""
    assert orchestrator is not None
    assert hasattr(orchestrator, "validate_and_refine")
    assert hasattr(orchestrator, "validate_and_refine_sync")


def test_orchestrator_module_initialization(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test that orchestrator properly initializes its DSPy modules."""
    assert hasattr(orchestrator, "validation_module")
    from skill_fleet.core.dspy.modules import Phase3ValidationModule

    assert isinstance(orchestrator.validation_module, Phase3ValidationModule)


def test_orchestrator_has_expected_methods(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test that orchestrator has all expected methods."""
    expected_methods = [
        "validate_and_refine",
        "validate_and_refine_sync",
    ]

    for method_name in expected_methods:
        assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"
        assert callable(getattr(orchestrator, method_name)), f"{method_name} is not callable"


def test_validate_and_refine_method_signature(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test that validate_and_refine has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.validate_and_refine)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        "skill_content",
        "skill_metadata",
        "content_plan",
        "validation_rules",
        "user_feedback",
        "target_level",
        "enable_mlflow",
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_validate_and_refine_default_parameters(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test that validate_and_refine has appropriate default values."""
    import inspect

    sig = inspect.signature(orchestrator.validate_and_refine)

    # Check default values
    assert sig.parameters["user_feedback"].default == ""
    assert sig.parameters["target_level"].default == "intermediate"
    assert sig.parameters["enable_mlflow"].default is True


def test_validate_and_refine_sync_signature(orchestrator: QualityAssuranceOrchestrator) -> None:
    """Test that validate_and_refine_sync has the same signature as async version."""
    import inspect

    async_sig = inspect.signature(orchestrator.validate_and_refine)
    sync_sig = inspect.signature(orchestrator.validate_and_refine_sync)

    async_params = set(async_sig.parameters.keys())
    sync_params = set(sync_sig.parameters.keys())

    # Both methods should have the same parameters
    assert async_params == sync_params
