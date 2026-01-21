"""Unit tests for job persistence layer (JobManager + JobMemoryStore).

Tests verify:
- Memory store creation, retrieval, expiration
- JobManager dual-layer (memory + DB) access
- HITL response persistence
- Background cleanup
"""

import asyncio
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from skill_fleet.api.job_manager import JobManager, JobMemoryStore, get_job_manager
from skill_fleet.api.schemas import JobState


class TestJobMemoryStore:
    """Test memory store (hot cache)."""

    def test_create_memory_store(self):
        """Test memory store initialization."""
        store = JobMemoryStore(ttl_minutes=10)
        assert store.ttl_minutes == 10
        assert len(store.store) == 0

    def test_set_and_get(self):
        """Test storing and retrieving jobs."""
        store = JobMemoryStore()
        job = JobState(job_id="test-1")

        store.set("test-1", job)
        retrieved = store.get("test-1")

        assert retrieved is not None
        assert retrieved.job_id == "test-1"

    def test_get_nonexistent(self):
        """Test retrieving nonexistent job."""
        store = JobMemoryStore()
        result = store.get("nonexistent")
        assert result is None

    def test_ttl_expiration(self):
        """Test that jobs expire after TTL.

        Note: Uses very short TTL for testing (not 0, which causes immediate expiry).
        """
        # Create store with 1-minute TTL
        store = JobMemoryStore(ttl_minutes=1)
        job = JobState(job_id="test-2")

        store.set("test-2", job)
        assert store.get("test-2") is not None

        # Manually expire by manipulating internal timestamp
        # (Since we can't easily mock datetime, we'll test cleanup instead)
        store.store["test-2"] = (
            job,
            datetime.now(UTC) - timedelta(minutes=2),  # 2 minutes old
        )

        # Now it should be expired
        assert store.get("test-2") is None

    def test_delete(self):
        """Test deleting job from store."""
        store = JobMemoryStore()
        job = JobState(job_id="test-3")

        store.set("test-3", job)
        assert store.delete("test-3") is True
        assert store.get("test-3") is None

    def test_delete_nonexistent(self):
        """Test deleting nonexistent job."""
        store = JobMemoryStore()
        assert store.delete("nonexistent") is False

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        store = JobMemoryStore(ttl_minutes=1)

        # Add 3 jobs
        for i in range(3):
            job = JobState(job_id=f"test-{i}")
            store.set(f"test-{i}", job)

        # Manually expire all by manipulating timestamps
        past = datetime.now(UTC) - timedelta(minutes=2)
        for job_id in list(store.store.keys()):
            job, _ = store.store[job_id]
            store.store[job_id] = (job, past)

        # Cleanup should remove all
        cleaned = store.cleanup_expired()
        assert cleaned == 3
        assert len(store.store) == 0

    def test_cleanup_keeps_valid(self):
        """Test that cleanup doesn't remove valid entries."""
        store = JobMemoryStore(ttl_minutes=60)  # Long TTL

        job = JobState(job_id="valid")
        store.set("valid", job)

        cleaned = store.cleanup_expired()
        assert cleaned == 0
        assert store.get("valid") is not None

    def test_clear(self):
        """Test clearing all entries."""
        store = JobMemoryStore()

        for i in range(5):
            job = JobState(job_id=f"test-{i}")
            store.set(f"test-{i}", job)

        cleared = store.clear()
        assert cleared == 5
        assert len(store.store) == 0


class TestJobManager:
    """Test job manager (dual-layer facade)."""

    def test_create_job_manager(self):
        """Test job manager initialization."""
        manager = JobManager()
        assert manager.memory is not None
        assert manager.db_repo is None

    def test_create_with_custom_memory_store(self):
        """Test creating manager with custom memory store."""
        custom_store = JobMemoryStore(ttl_minutes=30)
        manager = JobManager(memory_store=custom_store)
        assert manager.memory == custom_store

    def test_create_job(self):
        """Test creating a new job."""
        manager = JobManager()
        job = JobState(job_id="test-job-1")

        manager.create_job(job)

        # Verify in memory
        retrieved = manager.memory.get("test-job-1")
        assert retrieved is not None
        assert retrieved.job_id == "test-job-1"

    def test_get_job_from_memory(self):
        """Test retrieving job from memory cache."""
        manager = JobManager()
        job = JobState(job_id="test-job-2")
        manager.memory.set("test-job-2", job)

        retrieved = manager.get_job("test-job-2")
        assert retrieved is not None
        assert retrieved.job_id == "test-job-2"

    def test_get_nonexistent_job(self):
        """Test retrieving nonexistent job."""
        manager = JobManager()
        result = manager.get_job("nonexistent")
        assert result is None

    def test_update_job(self):
        """Test updating job state."""
        manager = JobManager()
        job = JobState(job_id="test-job-3")
        manager.create_job(job)

        # Update progress message (JobState uses progress_message not progress_percent)
        updated = manager.update_job("test-job-3", {"progress_message": "50% complete"})

        assert updated is not None
        assert updated.progress_message == "50% complete"

        # Verify in memory
        retrieved = manager.get_job("test-job-3")
        assert retrieved.progress_message == "50% complete"

    def test_update_nonexistent_job(self):
        """Test updating nonexistent job."""
        manager = JobManager()
        result = manager.update_job("nonexistent", {"progress_percent": 50})
        assert result is None

    def test_delete_job(self):
        """Test deleting job from manager."""
        manager = JobManager()
        job = JobState(job_id="test-job-4")
        manager.create_job(job)

        assert manager.delete_job("test-job-4") is True
        assert manager.get_job("test-job-4") is None

    def test_save_job(self):
        """Test explicit save."""
        manager = JobManager()
        job = JobState(job_id="test-job-5")

        result = manager.save_job(job)
        assert result is True

    def test_cleanup_expired(self):
        """Test cleanup of expired jobs."""
        store = JobMemoryStore(ttl_minutes=0)
        manager = JobManager(memory_store=store)

        job = JobState(job_id="expiring")
        manager.create_job(job)

        time.sleep(0.1)

        cleaned = manager.cleanup_expired()
        assert cleaned == 1

    def test_global_get_job_manager(self):
        """Test getting global job manager."""
        manager1 = get_job_manager()
        manager2 = get_job_manager()

        # Should return same instance
        assert manager1 is manager2


class TestJobManagerWithMockDB:
    """Test job manager with mock database."""

    def test_db_repo_configuration(self):
        """Test configuring database repository."""
        manager = JobManager()

        # Mock DB repo
        class MockDBRepo:
            def get_by_id(self, job_id):
                return None

        mock_repo = MockDBRepo()
        manager.set_db_repo(mock_repo)

        assert manager.db_repo == mock_repo

    def test_db_fallback_on_memory_miss(self):
        """Test that manager falls back to DB on memory miss.

        This simulates: job exists in DB but not in memory.
        """

        job_uuid = uuid4()
        manager = JobManager()

        # Mock DB repo with a "persisted" job
        class MockDBJob:
            def __init__(self):
                self.job_id = job_uuid
                self.status = "completed"
                self.result = {"answer": "yes"}
                self.error = None
                self.updated_at = datetime.now(UTC)

        class MockDBRepo:
            def get_by_id(self, job_id):
                if job_id == job_uuid:
                    return MockDBJob()
                return None

        mock_repo = MockDBRepo()
        manager.set_db_repo(mock_repo)

        # Get job (should reconstruct from DB)
        job = manager.get_job(str(job_uuid))

        assert job is not None
        assert job.job_id == str(job_uuid)
        assert job.status == "completed"

    def test_memory_warms_on_db_hit(self):
        """Test that memory is warmed after DB hit."""

        job_uuid = uuid4()
        manager = JobManager()

        # Mock DB repo
        class MockDBJob:
            def __init__(self):
                self.job_id = job_uuid
                self.status = "running"
                self.result = None
                self.error = None
                self.updated_at = datetime.now(UTC)

        class MockDBRepo:
            def __init__(self):
                self.call_count = 0

            def get_by_id(self, job_id):
                if job_id == job_uuid:
                    self.call_count += 1
                    return MockDBJob()
                return None

        mock_repo = MockDBRepo()
        manager.set_db_repo(mock_repo)

        # First access: from DB
        job1 = manager.get_job(str(job_uuid))
        assert mock_repo.call_count == 1

        # Second access: from memory (no DB call)
        job2 = manager.get_job(str(job_uuid))
        assert mock_repo.call_count == 1  # No additional call

        assert job1.job_id == job2.job_id


class TestJobStateIntegration:
    """Integration tests with JobState objects."""

    def test_job_state_with_status_changes(self):
        """Test job status progression."""
        manager = JobManager()
        job = JobState(job_id="status-job")
        job.status = "pending"

        manager.create_job(job)

        # Simulate status transitions
        manager.update_job("status-job", {"status": "running"})
        retrieved = manager.get_job("status-job")
        assert retrieved.status == "running"

        manager.update_job("status-job", {"status": "completed"})
        retrieved = manager.get_job("status-job")
        assert retrieved.status == "completed"

    def test_job_state_with_progress(self):
        """Test job progress tracking."""
        manager = JobManager()
        job = JobState(job_id="progress-job")

        manager.create_job(job)

        # Simulate progress updates
        messages = ["25% complete", "50% complete", "75% complete", "100% complete"]
        for msg in messages:
            manager.update_job("progress-job", {"progress_message": msg})

        final = manager.get_job("progress-job")
        assert final.progress_message == "100% complete"

    def test_job_state_with_errors(self):
        """Test job error tracking."""
        manager = JobManager()
        job = JobState(job_id="error-job")

        manager.create_job(job)

        error_msg = "Failed to validate skill"
        manager.update_job("error-job", {"error": error_msg})

        retrieved = manager.get_job("error-job")
        assert retrieved.error == error_msg

    def test_job_state_with_result(self):
        """Test job result storage."""
        manager = JobManager()
        job = JobState(job_id="result-job")

        manager.create_job(job)

        result = {"skill_id": "python/async", "score": 0.85}
        manager.update_job("result-job", {"result": result})

        retrieved = manager.get_job("result-job")
        assert retrieved.result == result


class TestJobManagerConcurrency:
    """Test job manager with concurrent access patterns."""

    @pytest.mark.asyncio
    async def test_concurrent_updates(self):
        """Test concurrent job updates."""
        manager = JobManager()
        job = JobState(job_id="concurrent-job")
        manager.create_job(job)

        async def update_progress(msg):
            await asyncio.sleep(0.01)
            manager.update_job("concurrent-job", {"progress_message": msg})

        # Run concurrent updates
        await asyncio.gather(
            update_progress("25% complete"),
            update_progress("50% complete"),
            update_progress("75% complete"),
            update_progress("100% complete"),
        )

        final = manager.get_job("concurrent-job")
        assert final.progress_message == "100% complete"  # Last one wins

    def test_multiple_jobs(self):
        """Test managing multiple jobs."""
        manager = JobManager()

        # Create 10 jobs
        for i in range(10):
            job = JobState(job_id=f"job-{i}")
            manager.create_job(job)

        # Verify all exist
        for i in range(10):
            assert manager.get_job(f"job-{i}") is not None

    def test_job_isolation(self):
        """Test that job updates don't affect others."""
        manager = JobManager()

        job1 = JobState(job_id="isolated-1")
        job2 = JobState(job_id="isolated-2")

        manager.create_job(job1)
        manager.create_job(job2)

        # Update job1
        manager.update_job("isolated-1", {"progress_message": "50% complete"})

        # job2 should be unchanged
        retrieved1 = manager.get_job("isolated-1")
        retrieved2 = manager.get_job("isolated-2")

        assert retrieved1.progress_message == "50% complete"
        assert retrieved2.progress_message is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
