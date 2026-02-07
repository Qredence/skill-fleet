from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skill_fleet.api.exceptions import ForbiddenException
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


@pytest.mark.asyncio
async def test_post_response_throttles_duplicate_payload() -> None:
    """Test that duplicate HITL responses are throttled when sent too quickly."""
    manager = JobManager()
    job = JobState(
        job_id="job-rate-1",
        status="pending_user_input",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    notify = AsyncMock()
    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
        patch("skill_fleet.api.v1.hitl.save_job_session_async", AsyncMock(return_value=True)),
    ):
        # First response should be accepted
        payload = {"answers": {"response": "first"}}
        resp1 = await post_response(
            job_id=job.job_id,
            response=payload,
            skill_service=MagicMock(),
        )
        assert resp1.status == "accepted"

        # Reset job status for second attempt
        job.status = "pending_user_input"
        await manager.update_job(job.job_id, {"status": "pending_user_input"})

        # Second rapid response with identical payload should be throttled
        resp2 = await post_response(
            job_id=job.job_id,
            response=payload,
            skill_service=MagicMock(),
        )
        assert resp2.status == "ignored"
        assert "Duplicate response" in (resp2.detail or "")


@pytest.mark.asyncio
async def test_post_response_saves_session_async() -> None:
    """Test that HITL response triggers async session save."""
    manager = JobManager()
    job = JobState(
        job_id="job-save-1",
        status="pending_user_input",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    notify = AsyncMock()
    save_session = AsyncMock(return_value=True)

    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
        patch("skill_fleet.api.v1.hitl.save_job_session_async", save_session),
    ):
        resp = await post_response(
            job_id=job.job_id,
            response={"answers": {"response": "ok"}},
            skill_service=MagicMock(),
        )

    assert resp.status == "accepted"
    save_session.assert_awaited_once_with(job.job_id)


@pytest.mark.asyncio
async def test_post_response_requires_owner_header_for_non_default_owner() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-owner-1",
        status="pending_user_input",
        user_id="alice",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    notify = AsyncMock()
    with (
        patch("skill_fleet.api.v1.hitl.get_job_manager", return_value=manager),
        patch("skill_fleet.api.v1.hitl.notify_hitl_response", notify),
        pytest.raises(ForbiddenException, match="Owner header required"),
    ):
        await post_response(
            job_id=job.job_id,
            response={"answers": {"response": "ok"}},
            skill_service=MagicMock(),
        )

    notify.assert_not_awaited()


@pytest.mark.asyncio
async def test_post_response_accepts_matching_owner_header_for_non_default_owner() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-owner-2",
        status="pending_user_input",
        user_id="alice",
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
            x_user_id="alice",
        )

    assert resp.status == "accepted"
    notify.assert_awaited_once()
