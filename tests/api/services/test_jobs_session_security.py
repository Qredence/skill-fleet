from __future__ import annotations

import uuid

from skill_fleet.api.schemas.models import JobState
from skill_fleet.api.services import jobs


def test_save_job_session_uses_canonical_uuid_filename(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(jobs, "SESSION_DIR", tmp_path)

    canonical_job_id = str(uuid.uuid4())
    upper_job_id = canonical_job_id.upper()
    jobs.JOBS[canonical_job_id] = JobState(
        job_id=canonical_job_id,
        status="pending",
        task_description="Create a test skill",
        user_id="test-user",
    )

    try:
        assert jobs.save_job_session(upper_job_id) is True
        assert (tmp_path / f"{canonical_job_id}.json").exists()
        saved_files = sorted(path.name for path in tmp_path.glob("*.json"))
        assert saved_files == [f"{canonical_job_id}.json"]
    finally:
        jobs.JOBS.pop(canonical_job_id, None)


def test_session_operations_reject_unsafe_job_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(jobs, "SESSION_DIR", tmp_path)

    unsafe_job_id = "../evil"
    assert jobs.save_job_session(unsafe_job_id) is False
    assert jobs.load_job_session(unsafe_job_id) is None
    assert jobs.delete_job_session(unsafe_job_id) is False
    assert list(tmp_path.iterdir()) == []
