import pytest

from skill_fleet.api.exceptions import ForbiddenException
from skill_fleet.api.schemas.models import JobState
from skill_fleet.api.services.job_manager import JobManager
from skill_fleet.api.v1.hitl import get_prompt
from skill_fleet.core.models import SkillCreationResult


@pytest.mark.asyncio
async def test_get_prompt_self_heals_running_to_pending_user_input() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-1",
        status="running",
        hitl_type="clarify",
        hitl_data={
            "questions": [
                {
                    "text": "What is the primary use case?",
                    "question_type": "single",
                    "options": [{"id": "code", "label": "Code search"}],
                }
            ]
        },
    )
    await manager.create_job(job)

    resp = await get_prompt(job.job_id, manager=manager)

    assert resp.status == "pending_user_input"
    job_state = await manager.get_job(job.job_id)
    assert job_state is not None
    assert job_state.status == "pending_user_input"


@pytest.mark.asyncio
async def test_get_prompt_does_not_revive_resolved_prompt() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-2",
        status="running",
        hitl_type="clarify",
        hitl_data={
            "_resolved": True,
            "questions": [
                {
                    "text": "What is the primary use case?",
                    "question_type": "single",
                    "options": [{"id": "code", "label": "Code search"}],
                }
            ],
        },
    )
    await manager.create_job(job)

    resp = await get_prompt(job.job_id, manager=manager)

    assert resp.status == "running"
    job_state = await manager.get_job(job.job_id)
    assert job_state is not None
    assert job_state.status == "running"


@pytest.mark.asyncio
async def test_get_prompt_supports_dict_job_result() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-3",
        status="completed",
        result={"skill_content": "# Skill\n\nContent"},
    )
    await manager.create_job(job)

    resp = await get_prompt(job.job_id, manager=manager)

    assert resp.status == "completed"
    assert resp.skill_content == "# Skill\n\nContent"


@pytest.mark.asyncio
async def test_get_prompt_supports_pydantic_job_result() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-4",
        status="completed",
        result=SkillCreationResult(status="completed", skill_content="# Skill\n\nContent"),
    )
    await manager.create_job(job)

    resp = await get_prompt(job.job_id, manager=manager)

    assert resp.status == "completed"
    assert resp.skill_content == "# Skill\n\nContent"


@pytest.mark.asyncio
async def test_get_prompt_requires_owner_header_for_non_default_owner() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-5",
        status="pending_user_input",
        user_id="alice",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    with pytest.raises(ForbiddenException, match="Owner header required"):
        await get_prompt(job.job_id, manager=manager)


@pytest.mark.asyncio
async def test_get_prompt_accepts_matching_owner_header_for_non_default_owner() -> None:
    manager = JobManager()
    job = JobState(
        job_id="job-6",
        status="pending_user_input",
        user_id="alice",
        hitl_type="clarify",
        hitl_data={"questions": [{"text": "Q?", "options": [{"id": "a", "label": "A"}]}]},
    )
    await manager.create_job(job)

    resp = await get_prompt(job.job_id, x_user_id="alice", manager=manager)

    assert resp.status == "pending_user_input"
