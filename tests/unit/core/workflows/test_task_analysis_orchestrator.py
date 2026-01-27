"""
Unit tests for TaskAnalysisOrchestrator.

Tests the Phase 1 orchestrator that handles requirements gathering,
intent analysis, taxonomy path finding, and dependency analysis.
"""

import pytest

from skill_fleet.core.dspy.modules.workflows.task_analysis import TaskAnalysisOrchestrator


@pytest.fixture
def orchestrator() -> TaskAnalysisOrchestrator:
    """Create a TaskAnalysisOrchestrator fixture."""
    return TaskAnalysisOrchestrator()


def test_initialization(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test orchestrator can be initialized."""
    assert orchestrator is not None
    assert hasattr(orchestrator, "analyze")
    assert hasattr(orchestrator, "analyze_sync")


def test_orchestrator_module_initialization(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that orchestrator properly initializes its DSPy modules."""
    # TaskAnalysisOrchestrator uses a consolidated Phase1UnderstandingModule
    assert hasattr(orchestrator, "understanding_module")
    from skill_fleet.core.dspy.modules import Phase1UnderstandingModule

    assert isinstance(orchestrator.understanding_module, Phase1UnderstandingModule)


def test_orchestrator_has_expected_methods(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that orchestrator has all expected methods."""
    expected_methods = [
        "analyze",
        "analyze_sync",
    ]

    for method_name in expected_methods:
        assert hasattr(orchestrator, method_name), f"Missing method: {method_name}"
        assert callable(getattr(orchestrator, method_name)), f"{method_name} is not callable"


def test_analyze_method_signature(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that analyze has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.analyze)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        "task_description",
        "user_context",
        "taxonomy_structure",
        "existing_skills",
        "user_confirmation",
        "enable_mlflow",
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_analyze_default_parameters(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that analyze has appropriate default values."""
    import inspect

    sig = inspect.signature(orchestrator.analyze)

    # Check default values
    assert sig.parameters["user_context"].default == ""
    assert sig.parameters["taxonomy_structure"].default == ""
    assert sig.parameters["existing_skills"].default is None
    assert sig.parameters["user_confirmation"].default == ""
    assert sig.parameters["enable_mlflow"].default is True


def test_analyze_sync_signature(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that analyze_sync has the same signature as async version."""
    import inspect

    async_sig = inspect.signature(orchestrator.analyze)
    sync_sig = inspect.signature(orchestrator.analyze_sync)

    async_params = set(async_sig.parameters.keys())
    sync_params = set(sync_sig.parameters.keys())

    # Both methods should have the same parameters
    assert async_params == sync_params


def test_orchestrator_has_expected_modules(orchestrator: TaskAnalysisOrchestrator) -> None:
    """Test that orchestrator has all expected DSPy modules."""
    # TaskAnalysisOrchestrator uses a consolidated Phase1UnderstandingModule
    # that handles all Phase 1 tasks (requirements, intent, taxonomy, dependencies, plan)
    expected_modules = [
        "understanding_module",
    ]

    for module_name in expected_modules:
        assert hasattr(orchestrator, module_name), f"Missing module: {module_name}"
