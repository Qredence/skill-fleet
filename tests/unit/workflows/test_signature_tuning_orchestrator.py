"""
Unit tests for SignatureTuningOrchestrator.

Tests the signature optimization workflow orchestrator that handles
signature tuning, iterative improvement, and version history tracking.
"""

import pytest

from skill_fleet.workflows.signature_optimization import SignatureTuningOrchestrator


@pytest.fixture
def orchestrator() -> SignatureTuningOrchestrator:
    """Create a SignatureTuningOrchestrator fixture."""
    return SignatureTuningOrchestrator()


def test_initialization(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test orchestrator can be initialized."""
    assert orchestrator is not None
    assert hasattr(orchestrator, 'tune_signature')
    assert hasattr(orchestrator, 'tune_iteratively')
    assert hasattr(orchestrator, 'get_version_history')


def test_initialization_with_custom_params() -> None:
    """Test orchestrator initialization with custom parameters."""
    orchestrator = SignatureTuningOrchestrator(
        improvement_threshold=0.1,
        max_iterations=5,
        quality_threshold=0.8,
    )

    assert orchestrator.improvement_threshold == 0.1
    assert orchestrator.max_iterations == 5
    assert orchestrator.quality_threshold == 0.8


def test_default_parameters(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that orchestrator has correct default parameters."""
    assert orchestrator.improvement_threshold == 0.05
    assert orchestrator.max_iterations == 3
    assert orchestrator.quality_threshold == 0.75


def test_orchestrator_module_initialization(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that orchestrator properly initializes its DSPy modules."""
    assert hasattr(orchestrator, 'tuner')


def test_orchestrator_has_sync_wrappers(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that orchestrator has synchronous wrappers for async methods."""
    expected_sync_methods = [
        'tune_signature_sync',
        'tune_iteratively_sync',
    ]

    for method_name in expected_sync_methods:
        assert hasattr(orchestrator, method_name), f"Missing sync wrapper: {method_name}"
        assert callable(getattr(orchestrator, method_name)), f"{method_name} is not callable"


def test_get_version_history_nonexistent(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test getting version history for non-existent signature."""
    result = orchestrator.get_version_history("nonexistent_sig")
    assert result is None


def test_tune_signature_signature(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that tune_signature has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.tune_signature)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        'skill_content',
        'current_signature',
        'metric_score',
        'target_score',
        'skill_type',
        'signature_id',
        'enable_mlflow',
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_tune_signature_default_parameters(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that tune_signature has appropriate default values."""
    import inspect

    sig = inspect.signature(orchestrator.tune_signature)

    # Check default values
    assert sig.parameters['target_score'].default == 0.80
    assert sig.parameters['skill_type'].default == "comprehensive"
    assert sig.parameters['signature_id'].default is None
    assert sig.parameters['enable_mlflow'].default is True


def test_tune_iteratively_signature(orchestrator: SignatureTuningOrchestrator) -> None:
    """Test that tune_iteratively has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.tune_iteratively)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        'skill_content',
        'current_signature',
        'metric_score',
        'target_score',
        'skill_type',
        're_evaluate_fn',
        'enable_mlflow',
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"
