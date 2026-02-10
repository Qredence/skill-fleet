from __future__ import annotations

from types import SimpleNamespace

from skill_fleet.api.dependencies import get_job_manager
from skill_fleet.api.services.event_registry import get_event_registry


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

    client.app.dependency_overrides[get_job_manager] = lambda: manager
    client.app.dependency_overrides[get_event_registry] = lambda: registry

    try:
        with client.stream("GET", "/api/v1/skills/job-123/stream") as response:
            body = "".join(response.iter_text())

        assert response.status_code == 200
        assert "sensitive runtime details should never leak" not in body
        assert '"error_code": "stream_internal_error"' in body
        assert '"message": "An internal error occurred while streaming job updates."' in body
        assert '"sequence": -1' in body
    finally:
        client.app.dependency_overrides.clear()
