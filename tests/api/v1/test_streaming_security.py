from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch


class _FailingJobManager:
    def __init__(self) -> None:
        self._calls = 0

    async def get_job(self, _job_id: str):
        self._calls += 1
        if self._calls == 1:
            return SimpleNamespace(status="running")
        raise RuntimeError("sensitive runtime details should never leak")


class _EmptyEventRegistry:
    async def get(self, _job_id: str):
        return None


def test_job_stream_redacts_internal_exception_details(client) -> None:
    manager = _FailingJobManager()
    registry = _EmptyEventRegistry()

    with (
        patch("skill_fleet.api.v1.streaming.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.streaming.get_event_registry", return_value=registry),
    ):
        with client.stream("GET", "/api/v1/skills/job-123/stream") as response:
            body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "sensitive runtime details should never leak" not in body
    assert '"error_code": "stream_internal_error"' in body
    assert '"message": "An internal error occurred while streaming job updates."' in body
