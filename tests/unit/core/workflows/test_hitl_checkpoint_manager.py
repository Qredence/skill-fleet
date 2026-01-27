"""
Unit tests for HITLCheckpointManager.

Tests the Human-in-the-Loop checkpoint manager that handles
clarifying questions, previews, feedback analysis, and checkpoint management.
"""

import pytest

from skill_fleet.core.dspy.modules.workflows.hitl_checkpoint import (
    CheckpointPhase,
    HITLCheckpointManager,
)


@pytest.fixture
def manager() -> HITLCheckpointManager:
    """Create a HITLCheckpointManager fixture."""
    return HITLCheckpointManager()


def test_initialization(manager: HITLCheckpointManager) -> None:
    """Test manager can be initialized."""
    assert manager is not None
    assert hasattr(manager, "determine_strategy")
    assert hasattr(manager, "generate_clarifying_questions")
    assert hasattr(manager, "confirm_understanding")
    assert hasattr(manager, "generate_preview")
    assert hasattr(manager, "analyze_feedback")
    assert hasattr(manager, "format_validation_results")
    assert hasattr(manager, "plan_refinement")
    assert hasattr(manager, "assess_readiness")


def test_manager_has_expected_modules(manager: HITLCheckpointManager) -> None:
    """Test that manager has all expected DSPy modules."""
    expected_modules = [
        "strategy_module",
        "clarifying_questions_module",
        "confirm_understanding_module",
        "preview_generator_module",
        "feedback_analyzer_module",
        "validation_formatter_module",
        "refinement_planner_module",
        "readiness_assessor_module",
    ]

    for module_name in expected_modules:
        assert hasattr(manager, module_name), f"Missing module: {module_name}"


def test_manager_has_sync_wrappers(manager: HITLCheckpointManager) -> None:
    """Test that manager has synchronous wrappers for async methods."""
    expected_sync_methods = [
        "determine_strategy_sync",
        "generate_clarifying_questions_sync",
        "confirm_understanding_sync",
        "generate_preview_sync",
        "analyze_feedback_sync",
        "format_validation_results_sync",
        "plan_refinement_sync",
        "assess_readiness_sync",
    ]

    for method_name in expected_sync_methods:
        assert hasattr(manager, method_name), f"Missing sync wrapper: {method_name}"
        assert callable(getattr(manager, method_name)), f"{method_name} is not callable"


def test_checkpoint_lifecycle(manager: HITLCheckpointManager) -> None:
    """Test creating, retrieving, and updating checkpoints."""
    # Create checkpoint
    checkpoint = manager.create_checkpoint(
        phase=CheckpointPhase.PHASE1_UNDERSTANDING,
        checkpoint_type="clarification",
        data={"question": "What is your goal?"},
    )

    assert checkpoint.checkpoint_id
    assert checkpoint.status == "pending"
    assert checkpoint.phase == CheckpointPhase.PHASE1_UNDERSTANDING

    # Retrieve checkpoint
    retrieved = manager.get_checkpoint(checkpoint.checkpoint_id)
    assert retrieved is not None
    assert retrieved.checkpoint_id == checkpoint.checkpoint_id

    # Update checkpoint
    updated = manager.update_checkpoint_status(
        checkpoint.checkpoint_id,
        status="approved",
        user_response={"answer": "Learn decorators"},
    )
    assert updated is True

    # Verify update
    retrieved = manager.get_checkpoint(checkpoint.checkpoint_id)
    assert retrieved.status == "approved"
    assert retrieved.user_response == {"answer": "Learn decorators"}


def test_checkpoint_to_dict(manager: HITLCheckpointManager) -> None:
    """Test converting checkpoint to dictionary."""
    checkpoint = manager.create_checkpoint(
        phase=CheckpointPhase.PHASE2_CONTENT_GENERATION,
        checkpoint_type="preview",
        data={"content": "Preview content"},
    )

    checkpoint_dict = checkpoint.to_dict()
    assert isinstance(checkpoint_dict, dict)
    assert checkpoint_dict["checkpoint_id"] == checkpoint.checkpoint_id
    assert checkpoint_dict["phase"] == "phase2_content_generation"
    assert checkpoint_dict["checkpoint_type"] == "preview"
    assert checkpoint_dict["status"] == "pending"


def test_get_nonexistent_checkpoint(manager: HITLCheckpointManager) -> None:
    """Test getting a non-existent checkpoint returns None."""
    result = manager.get_checkpoint("nonexistent_id")
    assert result is None


def test_update_nonexistent_checkpoint(manager: HITLCheckpointManager) -> None:
    """Test updating a non-existent checkpoint returns False."""
    result = manager.update_checkpoint_status(
        "nonexistent_id",
        status="approved",
    )
    assert result is False


def test_checkpoint_phase_enum() -> None:
    """Test CheckpointPhase enum values."""
    assert CheckpointPhase.PHASE1_UNDERSTANDING.value == "phase1_understanding"
    assert CheckpointPhase.PHASE2_CONTENT_GENERATION.value == "phase2_content_generation"
    assert CheckpointPhase.PHASE3_VALIDATION.value == "phase3_validation"


def test_checkpoint_manager_has_checkpoints_dict(manager: HITLCheckpointManager) -> None:
    """Test that manager maintains checkpoints dictionary."""
    assert hasattr(manager, "checkpoints")
    assert isinstance(manager.checkpoints, dict)

    # Create a checkpoint and verify it's in the dict
    checkpoint = manager.create_checkpoint(
        phase=CheckpointPhase.PHASE1_UNDERSTANDING,
        checkpoint_type="test",
        data={},
    )
    assert checkpoint.checkpoint_id in manager.checkpoints
