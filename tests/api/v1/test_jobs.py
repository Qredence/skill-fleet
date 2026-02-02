"""Tests for jobs router endpoints (v1)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from skill_fleet.api.schemas.models import JobState
from skill_fleet.api.services.job_manager import JobManager


class TestGetJobStatus:
    @pytest.mark.asyncio
    async def test_get_job_status_uses_job_manager(self, client) -> None:
        manager = JobManager()
        job = JobState(
            job_id="job-123",
            status="pending_user_input",
            task_description="Test job",
            user_id="default",
            hitl_type="clarify",
            hitl_data={"questions": ["Q1"]},
        )
        await manager.create_job(job)

        with patch("skill_fleet.api.v1.jobs.get_job_manager", return_value=manager):
            resp = client.get("/api/v1/jobs/job-123")

        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == "job-123"
        assert data["status"] == "pending_user_input"
        assert data["hitl_type"] == "clarify"
