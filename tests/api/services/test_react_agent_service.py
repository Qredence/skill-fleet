# type: ignore
# Type errors in tests are from mocking patterns; runtime behavior is correct

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from skill_fleet.api.schemas.models import JobState
from skill_fleet.api.services.react_agent_service import ReActAgentService


class _DummySkillService:
    def __init__(self, skills_root: Path):
        self.skills_root = skills_root
        self.drafts_root = skills_root / "_drafts"

    async def create_skill(self, *args, **kwargs):
        return MagicMock(status="completed")


class _DummyTaxonomyManager:
    def __init__(self, skills_root: Path):
        self.skills_root = skills_root
        self.metadata_cache = {}

    def _load_skill_dir_metadata(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_get_job_status_handles_missing_progress_percent(monkeypatch, tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    service = ReActAgentService(
        taxonomy_manager=_DummyTaxonomyManager(skills_root),
        skill_service=_DummySkillService(skills_root),
    )

    manager = MagicMock()
    manager.get_job = AsyncMock(return_value=JobState(job_id="job-1", status="running"))
    monkeypatch.setattr(
        "skill_fleet.api.services.react_agent_service.get_job_manager",
        lambda: manager,
    )

    payload = await service.get_job_status(job_id="job-1")

    assert payload["found"] is True
    assert payload["job_id"] == "job-1"
    assert payload["progress_percent"] is None


@pytest.mark.asyncio
async def test_send_message_start_skill_creation_sets_active_job(monkeypatch, tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    service = ReActAgentService(
        taxonomy_manager=_DummyTaxonomyManager(skills_root),
        skill_service=_DummySkillService(skills_root),
    )
    service.start_skill_creation = AsyncMock(
        return_value={
            "job_id": "job-start",
            "found": True,
            "status": "pending",
            "phase": "understanding",
        }
    )
    service._refresh_workflow_state = AsyncMock()

    payload = await service.send_message(
        message="Create a skill for decorators in Python",
        session_id="s-1",
        user_id="default",
        context={},
        workflow_intent="start_skill_creation",
    )

    assert payload["active_job_id"] == "job-start"
    assert payload["next_step"] == {"type": "check_status", "job_id": "job-start"}
    assert "Started a new skill creation workflow" in payload["response"]


@pytest.mark.asyncio
async def test_send_message_submit_hitl_normalizes_payload(monkeypatch, tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    service = ReActAgentService(
        taxonomy_manager=_DummyTaxonomyManager(skills_root),
        skill_service=_DummySkillService(skills_root),
    )
    service.submit_hitl_response = AsyncMock(
        return_value={
            "response": {"status": "accepted"},
            "status": {"found": True, "status": "running"},
            "prompt": None,
        }
    )
    service._refresh_workflow_state = AsyncMock()

    session_state = service._workflow_sessions["s-1"]
    session_state.active_job_id = "job-hitl"
    session_state.awaiting_hitl = True
    session_state.hitl_type = "confirm"

    await service.send_message(
        message="proceed",
        session_id="s-1",
        user_id="default",
        context={},
        workflow_intent="submit_hitl",
    )

    service.submit_hitl_response.assert_awaited_once()
    call_kwargs = service.submit_hitl_response.await_args.kwargs
    assert call_kwargs["job_id"] == "job-hitl"
    assert call_kwargs["payload"]["action"] == "proceed"


@pytest.mark.asyncio
async def test_send_message_check_status_takes_priority_over_hitl(monkeypatch, tmp_path):
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    service = ReActAgentService(
        taxonomy_manager=_DummyTaxonomyManager(skills_root),
        skill_service=_DummySkillService(skills_root),
    )
    service.submit_hitl_response = AsyncMock()
    service._refresh_workflow_state = AsyncMock()

    session_state = service._workflow_sessions["s-check"]
    session_state.active_job_id = "job-check"
    session_state.awaiting_hitl = True
    session_state.hitl_type = "clarify"
    session_state.job_status = "pending_user_input"
    session_state.current_phase = "understanding"

    payload = await service.send_message(
        message="check status",
        session_id="s-check",
        user_id="default",
        context={},
    )

    service.submit_hitl_response.assert_not_awaited()
    assert "Workflow status is" in payload["response"]
