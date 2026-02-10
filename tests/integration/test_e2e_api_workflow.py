"""End-to-end API workflow test: Create -> Validate -> Generate XML -> Promote."""

from __future__ import annotations

import json
import time
from pathlib import Path
from types import SimpleNamespace

from skill_fleet.api.dependencies import (
    clear_taxonomy_manager_cache,
    get_job_manager,
    get_skill_service,
    get_skills_root,
    get_taxonomy_manager,
)
from skill_fleet.api.services.job_manager import JobManager
from skill_fleet.api.services.jobs import update_job
from skill_fleet.common.paths import ensure_skills_root_initialized
from skill_fleet.taxonomy.manager import TaxonomyManager


class _FakeSkillService:
    """Deterministic service used to exercise end-to-end API routes without LLM calls."""

    def __init__(self, skills_root: Path, taxonomy_manager: TaxonomyManager):
        self.skills_root = skills_root
        self.taxonomy_manager = taxonomy_manager

    async def create_skill(self, request, existing_job_id: str | None = None):
        assert existing_job_id is not None
        skill_name = "e2e-skill"
        taxonomy_path = f"testing/{skill_name}"
        draft_dir = self.skills_root / "_drafts" / existing_job_id / skill_name
        draft_dir.mkdir(parents=True, exist_ok=True)

        skill_md = """---
name: e2e-skill
description: Use when testing API-first end-to-end workflow behavior.
---

# E2E Skill

## Overview
This skill exists to validate the end-to-end API workflow.

## When to Use This Skill
- You are validating create/validate/promote behavior.
- You need a deterministic fixture skill for integration tests.
"""
        (draft_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (draft_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "skill_id": taxonomy_path,
                    "name": skill_name,
                    "description": "Use when testing API-first end-to-end workflow behavior.",
                    "version": "1.0.0",
                    "type": "technical",
                    "weight": "medium",
                    "load_priority": "task_specific",
                    "dependencies": [],
                    "capabilities": [],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        await update_job(
            existing_job_id,
            {
                "status": "completed",
                "draft_path": str(draft_dir.resolve()),
                "intended_taxonomy_path": taxonomy_path,
                "validation_passed": True,
                "validation_status": "passed",
                "validation_score": 1.0,
            },
        )

        return SimpleNamespace(status="completed")


def test_full_api_workflow_create_validate_xml_promote(client, tmp_path):
    """Exercise the full API-first workflow with real endpoints."""
    clear_taxonomy_manager_cache()
    skills_root = ensure_skills_root_initialized(tmp_path / "skills")
    taxonomy_manager = TaxonomyManager(skills_root)
    fake_service = _FakeSkillService(skills_root=skills_root, taxonomy_manager=taxonomy_manager)
    job_manager = JobManager()

    # Set the global job manager instance used by update_job and other utility functions
    import skill_fleet.api.services.job_manager as jm_module

    old_manager = jm_module._job_manager
    jm_module._job_manager = job_manager

    client.app.dependency_overrides[get_skills_root] = lambda: skills_root
    client.app.dependency_overrides[get_taxonomy_manager] = lambda: taxonomy_manager
    client.app.dependency_overrides[get_skill_service] = lambda: fake_service
    client.app.dependency_overrides[get_job_manager] = lambda: job_manager

    try:
        create_response = client.post(
            "/api/v1/skills",
            json={
                "task_description": "Create a deterministic e2e workflow skill for API tests",
                "user_id": "alice",
            },
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Wait briefly for background task completion.
        job_payload = {}
        for _ in range(40):
            job_response = client.get(f"/api/v1/jobs/{job_id}")
            assert job_response.status_code == 200
            job_payload = job_response.json()
            if job_payload["status"] == "completed" and job_payload.get("draft_path"):
                break
            time.sleep(0.05)
        assert job_payload["status"] == "completed"
        assert job_payload.get("draft_path")
        assert job_payload.get("intended_taxonomy_path") == "testing/e2e-skill"

        draft_rel_path = f"_drafts/{job_id}/e2e-skill"
        validate_response = client.post(
            "/api/v1/skills/validate",
            json={"skill_path": draft_rel_path, "use_llm": False},
        )
        assert validate_response.status_code == 200
        validate_payload = validate_response.json()
        assert "passed" in validate_payload
        assert "errors" in validate_payload
        assert "warnings" in validate_payload

        xml_before_response = client.get("/api/v1/taxonomy/xml", params={"user_id": "alice"})
        assert xml_before_response.status_code == 200
        assert "<available_skills>" in xml_before_response.text

        promote_response = client.post(
            f"/api/v1/drafts/{job_id}/promote",
            json={"overwrite": True, "delete_draft": False, "force": False},
        )
        assert promote_response.status_code == 200
        promote_payload = promote_response.json()
        assert promote_payload["status"] == "promoted"
        final_path = Path(promote_payload["final_path"])
        assert (final_path / "SKILL.md").exists()

        # Ensure the promoted skill is loaded into cache before XML generation.
        taxonomy_manager._load_skill_dir_metadata(final_path)

        xml_after_response = client.get("/api/v1/taxonomy/xml")
        assert xml_after_response.status_code == 200
        assert "<name>e2e-skill</name>" in xml_after_response.text
        assert str(final_path / "SKILL.md") in xml_after_response.text
    finally:
        client.app.dependency_overrides.clear()
        jm_module._job_manager = old_manager
