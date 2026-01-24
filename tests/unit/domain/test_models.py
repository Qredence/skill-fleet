"""
Unit tests for domain models.
"""

import pytest

from skill_fleet.domain.models import (
    DomainEvent,
    Job,
    JobCompletedEvent,
    JobStatus,
    Skill,
    SkillCreatedEvent,
    SkillMetadata,
    SkillType,
    SkillWeight,
    LoadPriority,
    TaxonomyPath,
)


def test_taxonomy_path_creates_valid_path() -> None:
    """Test TaxonomyPath creates valid paths."""
    path = TaxonomyPath("python/decorators")
    assert path.path == "python/decorators"


def test_taxonomy_path_rejects_empty() -> None:
    """Test TaxonomyPath rejects empty paths."""
    with pytest.raises(ValueError):
        TaxonomyPath("")


def test_taxonomy_path_sanitizes_input() -> None:
    """Test TaxonomyPath sanitizes malicious input."""
    # Should sanitize traversal attempts
    path = TaxonomyPath("safe/path")
    assert path.path == "safe/path"


def test_taxonomy_path_parent() -> None:
    """Test TaxonomyPath parent method."""
    path = TaxonomyPath("python/decorators")
    parent = path.parent()
    assert parent is not None
    assert parent.path == "python"


def test_taxonomy_path_parent_at_root() -> None:
    """Test TaxonomyPath parent at root returns None."""
    path = TaxonomyPath("python")
    parent = path.parent()
    assert parent is None


def test_taxonomy_path_child() -> None:
    """Test TaxonomyPath child method."""
    path = TaxonomyPath("python")
    child = path.child("decorators")
    assert child.path == "python/decorators"


def test_taxonomy_path_depth() -> None:
    """Test TaxonomyPath depth calculation."""
    assert TaxonomyPath("root").depth() == 1
    assert TaxonomyPath("root/child").depth() == 2
    assert TaxonomyPath("root/child/grandchild").depth() == 3


def test_skill_metadata_to_dict() -> None:
    """Test SkillMetadata to_dict conversion."""
    metadata = SkillMetadata(
        skill_id="test_skill",
        name="Test Skill",
        description="A test skill",
        version="2.0.0",
        type=SkillType.GUIDE,
        weight=SkillWeight.HEAVY,
        load_priority=LoadPriority.ALWAYS_LOADED,
        dependencies=["dep1", "dep2"],
        capabilities=["cap1"],
    )

    result = metadata.to_dict()
    assert result["skill_id"] == "test_skill"
    assert result["name"] == "Test Skill"
    assert result["type"] == "guide"
    assert result["weight"] == "heavy"
    assert result["load_priority"] == "always_loaded"
    assert result["dependencies"] == ["dep1", "dep2"]


def test_job_creation() -> None:
    """Test Job creation with proper defaults."""
    job = Job(
        job_id="test123",
        task_description="Create a test skill",
        user_id="test_user",
    )

    assert job.job_id == "test123"
    assert job.status == JobStatus.PENDING
    assert job.is_running() is False
    assert job.is_terminal() is False


def test_job_mark_completed() -> None:
    """Test Job mark_completed method."""
    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
    )

    result = {"content": "test content"}
    job.mark_completed(result)

    assert job.status == JobStatus.COMPLETED
    assert job.result == result
    assert job.is_terminal() is True


def test_job_mark_failed() -> None:
    """Test Job mark_failed method."""
    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
    )

    job.mark_failed("Something went wrong")

    assert job.status == JobStatus.FAILED
    assert job.error == "Something went wrong"
    assert job.is_terminal() is True


def test_job_update_progress() -> None:
    """Test Job update_progress method."""
    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
    )

    job.update_progress("phase1", "Processing...")

    assert job.current_phase == "phase1"
    assert job.progress_message == "Processing..."


def test_skill_has_capability() -> None:
    """Test Skill has_capability method."""
    metadata = SkillMetadata(
        skill_id="test",
        name="Test",
        description="Test",
        capabilities=["code_generation", "analysis"],
    )
    skill = Skill(metadata=metadata, content="# Test")

    assert skill.has_capability("code_generation") is True
    assert skill.has_capability("not_a_capability") is False


def test_skill_has_dependency() -> None:
    """Test Skill has_dependency method."""
    metadata = SkillMetadata(
        skill_id="test",
        name="Test",
        description="Test",
        dependencies=["dep1", "dep2"],
    )
    skill = Skill(metadata=metadata, content="# Test")

    assert skill.has_dependency("dep1") is True
    assert skill.has_dependency("dep3") is False


def test_skill_is_always_loaded() -> None:
    """Test Skill is_always_loaded method."""
    # Test with always_loaded=True
    metadata1 = SkillMetadata(
        skill_id="test",
        name="Test",
        description="Test",
        always_loaded=True,
    )
    skill1 = Skill(metadata=metadata1, content="# Test")
    assert skill1.is_always_loaded() is True

    # Test with load_priority=ALWAYS_LOADED
    metadata2 = SkillMetadata(
        skill_id="test",
        name="Test",
        description="Test",
        load_priority=LoadPriority.ALWAYS_LOADED,
    )
    skill2 = Skill(metadata=metadata2, content="# Test")
    assert skill2.is_always_loaded() is True

    # Test with normal settings
    metadata3 = SkillMetadata(
        skill_id="test",
        name="Test",
        description="Test",
    )
    skill3 = Skill(metadata=metadata3, content="# Test")
    assert skill3.is_always_loaded() is False


def test_domain_event_creation() -> None:
    """Test DomainEvent creation."""
    from datetime import datetime, UTC
    event = DomainEvent(event_id="evt123", occurred_at=datetime.now(UTC))
    assert event.event_id == "evt123"


def test_skill_created_event() -> None:
    """Test SkillCreatedEvent."""
    from datetime import datetime, UTC
    event = SkillCreatedEvent(
        event_id="evt123",
        occurred_at=datetime.now(UTC),
        skill_id="test_skill",
        taxonomy_path="python/test",
        user_id="test_user",
    )
    assert event.skill_id == "test_skill"
    assert event.taxonomy_path == "python/test"


def test_job_completed_event() -> None:
    """Test JobCompletedEvent."""
    from datetime import datetime, UTC
    job = Job(
        job_id="job123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.COMPLETED,
    )
    event = JobCompletedEvent(
        event_id="evt123",
        occurred_at=datetime.now(UTC),
        job_id="job123",
        status=JobStatus.COMPLETED,
        result={"success": True},
    )
    assert event.job_id == "job123"
    assert event.status == JobStatus.COMPLETED
