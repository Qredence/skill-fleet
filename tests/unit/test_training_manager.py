"""Tests for TrainingDataManager."""

import json

import pytest

from skill_fleet.config.training.manager import (
    ExampleMetadata,
    TrainingDataManager,
)


@pytest.fixture
def temp_training_dir(tmp_path):
    """Create temporary training directory with dummy data."""
    training_dir = tmp_path / "config" / "training"
    training_dir.mkdir(parents=True)

    # Create trainset
    trainset = [
        {"task_description": "Task 1", "output": "Output 1"},
        {"task_description": "Task 2", "output": "Output 2"},
        {"task_description": "Task 3", "output": "Output 3"},
    ]
    (training_dir / "trainset.json").write_text(json.dumps(trainset))

    return training_dir


def test_manager_initialization(temp_training_dir):
    """Test manager initialization."""
    manager = TrainingDataManager(temp_training_dir)
    assert manager.metadata_file == temp_training_dir / "example_metadata.json"
    assert manager._metadata == {}


def test_get_trainset_filtering(temp_training_dir):
    """Test filtering logic."""
    manager = TrainingDataManager(temp_training_dir)

    # Mock metadata
    import hashlib

    def get_id(task):
        return hashlib.md5(task.encode()).hexdigest()

    id1 = get_id("Task 1")
    id2 = get_id("Task 2")

    manager._metadata = {
        id1: ExampleMetadata(
            example_id=id1,
            task_description="Task 1",
            category="technical",
            quality_score=0.9,
            success_rate=1.0,
        ),
        id2: ExampleMetadata(
            example_id=id2,
            task_description="Task 2",
            category="domain",
            quality_score=0.1,  # Low score
            success_rate=0.0,
        ),
    }

    # Test with default config
    examples = manager.get_trainset()
    # Should include Task 1 (high score) and Task 3 (neutral/new), but maybe exclude Task 2
    # Task 3 is new, so score 0.5. Task 2 score approx 0.06 < 0.7 default threshold

    tasks = [ex["task_description"] for ex in examples]
    assert "Task 1" in tasks
    assert "Task 3" in tasks
    assert "Task 2" not in tasks


def test_update_scores(temp_training_dir):
    """Test score updates."""
    manager = TrainingDataManager(temp_training_dir)

    # Setup initial metadata
    import hashlib

    id1 = hashlib.md5(b"Task 1").hexdigest()

    manager._metadata = {
        id1: ExampleMetadata(
            example_id=id1,
            task_description="Task 1",
            category="technical",
            quality_score=0.5,
            success_rate=0.5,
        )
    }

    # Update
    results = [{"example_id": id1, "score": 1.0, "passed": True}]

    manager.update_scores(results)

    # Check updates (moving average)
    meta = manager._metadata[id1]
    assert meta.quality_score > 0.5  # Should increase
    assert meta.success_rate > 0.5  # Should increase

    # Verify persistence
    assert (temp_training_dir / "example_metadata.json").exists()
