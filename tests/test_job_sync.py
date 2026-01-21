"""Test job persistence sync between JOBS dict and JobManager."""

import pytest

from skill_fleet.api.job_manager import get_job_manager
from skill_fleet.api.jobs import JOBS, create_job, get_job
from skill_fleet.api.schemas import JobState


def test_create_job_returns_valid_id():
    """Test that create_job returns a non-empty string."""
    JOBS.clear()  # Reset
    job_id = create_job()
    assert job_id
    assert isinstance(job_id, str)
    assert len(job_id) > 0


def test_create_job_stores_in_jobs_dict():
    """Test that create_job stores job in JOBS dict."""
    JOBS.clear()
    job_id = create_job()

    assert job_id in JOBS
    assert isinstance(JOBS[job_id], JobState)
    assert JOBS[job_id].job_id == job_id


def test_create_job_registers_with_job_manager():
    """Test that create_job also registers with JobManager."""
    JOBS.clear()
    job_id = create_job()

    manager = get_job_manager()
    retrieved = manager.get_job(job_id)

    assert retrieved is not None
    assert retrieved.job_id == job_id


def test_get_job_from_jobs_dict():
    """Test that get_job retrieves from JOBS dict."""
    JOBS.clear()
    job_id = create_job()

    retrieved = get_job(job_id)
    assert retrieved is not None
    assert retrieved.job_id == job_id


def test_get_job_from_job_manager():
    """Test that JobManager retrieves what create_job registered."""
    JOBS.clear()
    job_id = create_job()

    # Directly test JobManager.get_job()
    manager = get_job_manager()
    retrieved = manager.get_job(job_id)

    assert retrieved is not None
    assert retrieved.job_id == job_id


def test_job_manager_sync():
    """Test that JOBS dict and JobManager stay in sync."""
    JOBS.clear()

    # Create multiple jobs
    job_ids = [create_job() for _ in range(3)]

    manager = get_job_manager()

    for job_id in job_ids:
        # Check JOBS dict
        assert job_id in JOBS

        # Check JobManager
        retrieved = manager.get_job(job_id)
        assert retrieved is not None
        assert retrieved.job_id == job_id

        # Verify they're the same object (or at least same state)
        assert JOBS[job_id].job_id == retrieved.job_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
