from __future__ import annotations

from pathlib import Path

from skill_fleet.api.schemas.models import JobState


def _create_completed_job(*, job_id: str, draft_skill_dir: Path) -> JobState:
    return JobState(
        job_id=job_id,
        status="completed",
        task_description="Create a test skill",
        user_id="test-user",
        intended_taxonomy_path="testing/test-skill",
        draft_path=str(draft_skill_dir.resolve()),
        validation_passed=True,
    )


def test_promote_draft_delete_draft_deletes_session_and_draft_dir(
    client, temp_skills_root, dependency_override_cleanup, monkeypatch, tmp_path
):
    import skill_fleet.api.services.jobs as jobs
    from skill_fleet.api.dependencies import get_skills_root
    from skill_fleet.common.paths import ensure_skills_root_initialized

    skills_root_initialized = ensure_skills_root_initialized(temp_skills_root)
    client.app.dependency_overrides[get_skills_root] = lambda: skills_root_initialized

    skills_root_resolved = skills_root_initialized
    drafts_root_resolved = (skills_root_resolved / "_drafts").resolve()

    # Point session persistence to a temp directory.
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(jobs, "SESSION_DIR", sessions_dir)

    job_id = "test-job-123"

    draft_job_root = drafts_root_resolved / job_id
    draft_skill_dir = draft_job_root / "testing" / "test-skill"
    draft_skill_dir.mkdir(parents=True, exist_ok=True)
    (draft_skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")

    job = _create_completed_job(job_id=job_id, draft_skill_dir=draft_skill_dir)
    jobs.JOBS[job_id] = job

    assert jobs.save_job_session(job_id) is True
    session_file = sessions_dir / f"{job_id}.json"
    assert session_file.exists()

    resp = client.post(
        f"/api/v1/drafts/{job_id}/promote",
        json={"overwrite": True, "delete_draft": True, "force": False},
    )
    assert resp.status_code == 200, resp.text

    # Draft root and session should be removed when delete_draft=true.
    assert not draft_job_root.exists()
    assert not session_file.exists()

    # Target taxonomy directory should exist.
    target_dir = temp_skills_root / "testing" / "test-skill"
    assert target_dir.exists()

    jobs.JOBS.pop(job_id, None)


def test_promote_draft_without_delete_draft_keeps_session_and_draft_dir(
    client, temp_skills_root, dependency_override_cleanup, monkeypatch, tmp_path
):
    import skill_fleet.api.services.jobs as jobs
    from skill_fleet.api.dependencies import get_skills_root
    from skill_fleet.common.paths import ensure_skills_root_initialized

    skills_root_initialized = ensure_skills_root_initialized(temp_skills_root)
    client.app.dependency_overrides[get_skills_root] = lambda: skills_root_initialized

    skills_root_resolved = skills_root_initialized
    drafts_root_resolved = (skills_root_resolved / "_drafts").resolve()

    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(jobs, "SESSION_DIR", sessions_dir)

    job_id = "test-job-456"

    draft_job_root = drafts_root_resolved / job_id
    draft_skill_dir = draft_job_root / "testing" / "test-skill"
    draft_skill_dir.mkdir(parents=True, exist_ok=True)
    (draft_skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")

    job = _create_completed_job(job_id=job_id, draft_skill_dir=draft_skill_dir)
    jobs.JOBS[job_id] = job

    assert jobs.save_job_session(job_id) is True
    session_file = sessions_dir / f"{job_id}.json"
    assert session_file.exists()

    resp = client.post(
        f"/api/v1/drafts/{job_id}/promote",
        json={"overwrite": True, "delete_draft": False, "force": False},
    )
    assert resp.status_code == 200, resp.text

    # Draft root and session should remain when delete_draft=false.
    assert draft_job_root.exists()
    assert session_file.exists()

    target_dir = temp_skills_root / "testing" / "test-skill"
    assert target_dir.exists()

    jobs.JOBS.pop(job_id, None)
