from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skill_fleet.api.schemas.models import JobState
from skill_fleet.api.services.job_manager import JobManager
from skill_fleet.api.v1.hitl import post_response


@pytest.mark.asyncio
async def test_post_response_notifies_waiter_for_pending_user_input() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-pui-1",
        status="pending_user_input",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    notify = AsyncMock()
    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
    ):
        resp = await post_response(
            job_id=job.job_id,
            response={"answers": {"response": "ok"}},
            skill_service=MagicMock(),
        )

    assert resp.status == "accepted"
    notify.assert_awaited_once()
    updated = await manager.get_job(job.job_id)
    assert updated is not None
    assert updated.status == "running"
    assert isinstance(updated.hitl_data, dict)
    assert updated.hitl_data.get("_resolved") is True


@pytest.mark.asyncio
async def test_post_response_notifies_waiter_for_pending_hitl() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-ph-1",
        status="pending_hitl",
        hitl_type="confirm",
        hitl_data={"summary": "recap"},
    )
    await manager.create_job(job)

    notify = AsyncMock()
    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
    ):
        resp = await post_response(
            job_id=job.job_id,
            response={"action": "proceed"},
            skill_service=MagicMock(),
        )

    assert resp.status == "accepted"
    notify.assert_awaited_once()
    updated = await manager.get_job(job.job_id)
    assert updated is not None
    assert updated.status == "running"


@pytest.mark.asyncio
async def test_post_response_ignores_when_not_pending() -> None:
    manager = JobManager()
    job = JobState(job_id="job-run-1", status="running", hitl_type=None, hitl_data=None)
    await manager.create_job(job)

    notify = AsyncMock()
    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
    ):
        resp = await post_response(
            job_id=job.job_id,
            response={"action": "proceed"},
            skill_service=MagicMock(),
        )

    assert resp.status == "ignored"
    notify.assert_not_awaited()
