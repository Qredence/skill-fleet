"""
Unit tests for domain specifications.
"""

import pytest

from skill_fleet.domain.models import Job, JobStatus, Skill, SkillMetadata, SkillType
from skill_fleet.domain.specifications import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    SkillHasValidName,
    SkillHasValidType,
    SkillHasValidTaxonomyPath,
    SkillIsComplete,
    SkillIsReadyForPublication,
    JobHasValidDescription,
    JobIsPending,
    JobIsRunning,
    JobIsTerminal,
    JobCanBeStarted,
    JobCanBeRetried,
    JobRequiresHITL,
    JobIsStale,
)


def test_skill_has_valid_name_valid() -> None:
    """Test SkillHasValidName with valid names."""
    spec = SkillHasValidName()

    metadata = SkillMetadata(
        skill_id="test",
        name="python-decorators",
        description="Test",
    )
    assert spec.is_satisfied_by(metadata)

    skill = Skill(metadata=metadata, content="# Test")
    assert spec.is_satisfied_by(skill)


def test_skill_has_valid_name_invalid() -> None:
    """Test SkillHasValidName with invalid names."""
    spec = SkillHasValidName()

    # Empty name
    metadata1 = SkillMetadata(skill_id="test", name="", description="Test")
    assert not spec.is_satisfied_by(metadata1)

    # Name with invalid characters
    metadata2 = SkillMetadata(skill_id="test", name="Invalid Name!", description="Test")
    assert not spec.is_satisfied_by(metadata2)

    # Name starting with hyphen
    metadata3 = SkillMetadata(skill_id="test", name="-invalid", description="Test")
    assert not spec.is_satisfied_by(metadata3)


def test_skill_has_valid_type_valid() -> None:
    """Test SkillHasValidType with valid types."""
    spec = SkillHasValidType()

    for skill_type in SkillType:
        metadata = SkillMetadata(
            skill_id="test",
            name="test",
            description="Test",
            type=skill_type,
        )
        assert spec.is_satisfied_by(metadata)


def test_skill_has_valid_type_invalid() -> None:
    """Test SkillHasValidType with invalid type."""
    spec = SkillHasValidType()

    # This would fail type checking in normal use
    # but we can test with a raw dict
    result = spec.is_satisfied_by({"type": "invalid_type"})
    assert result is False


def test_skill_is_complete_complete() -> None:
    """Test SkillIsComplete with complete skill."""
    spec = SkillIsComplete()

    metadata = SkillMetadata(
        skill_id="test",
        name="test",
        description="A complete skill",
        version="1.0.0",
    )
    assert spec.is_satisfied_by(metadata)


def test_skill_is_complete_incomplete() -> None:
    """Test SkillIsComplete with incomplete skill."""
    spec = SkillIsComplete()

    metadata = SkillMetadata(
        skill_id="test",
        name="test",
        description="",  # Empty description
    )
    assert not spec.is_satisfied_by(metadata)


def test_skill_is_ready_for_publication_ready() -> None:
    """Test SkillIsReadyForPublication with ready skill."""
    spec = SkillIsReadyForPublication(require_content=False)

    metadata = SkillMetadata(
        skill_id="python/decorators",
        name="python-decorators",
        description="Python decorators skill",
        version="1.0.0",
        type=SkillType.GUIDE,
        taxonomy_path="python/decorators",
    )
    assert spec.is_satisfied_by(metadata)


def test_skill_is_ready_for_publication_not_ready() -> None:
    """Test SkillIsReadyForPublication with not ready skill."""
    spec = SkillIsReadyForPublication(require_content=False)

    # Invalid name
    metadata = SkillMetadata(
        skill_id="test",
        name="INVALID NAME!",
        description="Test",
    )
    assert not spec.is_satisfied_by(metadata)


def test_job_has_valid_description_valid() -> None:
    """Test JobHasValidDescription with valid description."""
    spec = JobHasValidDescription()

    job = Job(
        job_id="test123",
        task_description="This is a valid task description",
        user_id="test_user",
    )
    assert spec.is_satisfied_by(job)


def test_job_has_valid_description_invalid() -> None:
    """Test JobHasValidDescription with invalid descriptions."""
    spec = JobHasValidDescription()

    # Too short
    job1 = Job(job_id="test123", task_description="Short", user_id="test_user")
    assert not spec.is_satisfied_by(job1)

    # Empty
    job2 = Job(job_id="test123", task_description="", user_id="test_user")
    assert not spec.is_satisfied_by(job2)


def test_job_is_pending_pending() -> None:
    """Test JobIsPending with pending job."""
    spec = JobIsPending()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.PENDING,
    )
    assert spec.is_satisfied_by(job)


def test_job_is_running_running() -> None:
    """Test JobIsRunning with running job."""
    spec = JobIsRunning()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.RUNNING,
    )
    assert spec.is_satisfied_by(job)


def test_job_is_terminal_completed() -> None:
    """Test JobIsTerminal with completed job."""
    spec = JobIsTerminal()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.COMPLETED,
    )
    assert spec.is_satisfied_by(job)


def test_job_is_terminal_failed() -> None:
    """Test JobIsTerminal with failed job."""
    spec = JobIsTerminal()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.FAILED,
    )
    assert spec.is_satisfied_by(job)


def test_job_can_be_started_ready() -> None:
    """Test JobCanBeStarted with ready job."""
    spec = JobCanBeStarted()

    job = Job(
        job_id="test123",
        task_description="This is a valid task description",
        user_id="test_user",
        status=JobStatus.PENDING,
    )
    assert spec.is_satisfied_by(job)


def test_job_can_be_started_not_ready() -> None:
    """Test JobCanBeStarted with not ready job."""
    spec = JobCanBeStarted()

    # Running job cannot be started
    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.RUNNING,
    )
    assert not spec.is_satisfied_by(job)


def test_job_can_be_retried_failed() -> None:
    """Test JobCanBeRetried with failed job."""
    spec = JobCanBeRetried()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.FAILED,
        error="Some error",
    )
    assert spec.is_satisfied_by(job)


def test_job_requires_hitl_waiting() -> None:
    """Test JobRequiresHITL with waiting job."""
    spec = JobRequiresHITL()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.PENDING_HITL,
    )
    assert spec.is_satisfied_by(job)


def test_specification_and_combination() -> None:
    """Test AND combination of specifications."""
    name_spec = SkillHasValidName()
    type_spec = SkillHasValidType()
    combined = name_spec.and_spec(type_spec)

    # Both conditions met
    metadata = SkillMetadata(
        skill_id="test",
        name="valid-name",
        description="Test",
        type=SkillType.GUIDE,
    )
    assert combined.is_satisfied_by(metadata)


def test_specification_or_combination() -> None:
    """Test OR combination of specifications."""
    pending_spec = JobIsPending()
    running_spec = JobIsRunning()
    combined = pending_spec.or_spec(running_spec)

    job1 = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.PENDING,
    )
    assert combined.is_satisfied_by(job1)

    job2 = Job(
        job_id="test456",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.RUNNING,
    )
    assert combined.is_satisfied_by(job2)


def test_specification_not_combination() -> None:
    """Test NOT of specification."""
    running_spec = JobIsRunning()
    not_running = running_spec.not_spec()

    job = Job(
        job_id="test123",
        task_description="Test",
        user_id="test_user",
        status=JobStatus.PENDING,
    )
    assert not_running.is_satisfied_by(job)
