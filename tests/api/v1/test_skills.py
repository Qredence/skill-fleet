"""Tests for skills router endpoints (v1)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from skill_fleet.api.dependencies import get_skill_service


def _override_skill_service(client, service):
    client.app.dependency_overrides[get_skill_service] = lambda: service


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


class TestCreateSkill:
    def test_create_skill_success(self, client, valid_skill_request):
        mock_service = MagicMock()
        # Background task expects an object with .status and .model_dump()
        mock_service.create_skill = AsyncMock(
            return_value=SimpleNamespace(status="pending_review", model_dump=lambda: {})
        )

        _override_skill_service(client, mock_service)
        try:
            response = client.post("/api/v1/skills", json=valid_skill_request)
            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "pending"
            mock_service.create_skill.assert_awaited_once()
        finally:
            _clear_overrides(client)

    def test_create_skill_missing_description(self, client):
        response = client.post("/api/v1/skills", json={"user_id": "test-user"})
        assert response.status_code == 422

    def test_create_skill_empty_description(self, client):
        response = client.post(
            "/api/v1/skills", json={"task_description": "", "user_id": "test-user"}
        )
        assert response.status_code == 422


class TestGetSkill:
    def test_get_skill_success(self, client, sample_skill):
        mock_service = MagicMock()
        mock_service.get_skill_by_path.return_value = {
            "skill_id": sample_skill["skill_id"],
            "name": sample_skill["name"],
            "description": sample_skill["description"],
            "version": "1.0",
            "type": "technical",
            "metadata": {},
            "content": sample_skill["content"],
        }

        _override_skill_service(client, mock_service)
        try:
            response = client.get(f"/api/v1/skills/{sample_skill['skill_id']}")
            assert response.status_code == 200
            data = response.json()
            assert data["skill_id"] == sample_skill["skill_id"]
            assert data["name"] == sample_skill["name"]
        finally:
            _clear_overrides(client)

    def test_get_skill_not_found(self, client):
        mock_service = MagicMock()
        mock_service.get_skill_by_path.side_effect = FileNotFoundError("not found")

        _override_skill_service(client, mock_service)
        try:
            response = client.get("/api/v1/skills/non-existent-id")
            assert response.status_code == 404
        finally:
            _clear_overrides(client)


class TestUpdateSkill:
    def test_update_skill_updates_files(self, client, tmp_path):
        skills_root = tmp_path / "skills"
        skill_dir = skills_root / "testing" / "test-skill"
        skill_dir.mkdir(parents=True)
        (skills_root / "_core").mkdir(parents=True, exist_ok=True)

        md_path = skill_dir / "SKILL.md"
        meta_path = skill_dir / "metadata.json"
        md_path.write_text("# Old\n", encoding="utf-8")
        meta_path.write_text(json.dumps({"name": "Old"}, indent=2), encoding="utf-8")

        mock_service = MagicMock()
        mock_service.skills_root = skills_root
        mock_service.get_skill_by_path.return_value = {"skill_id": "test-skill"}
        mock_service.taxonomy_manager.resolve_skill_location.return_value = "testing/test-skill"

        _override_skill_service(client, mock_service)
        try:
            response = client.put(
                "/api/v1/skills/test-skill",
                json={"content": "# New\n", "metadata": {"name": "New"}},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "updated"

            assert md_path.read_text(encoding="utf-8") == "# New\n"
            assert json.loads(meta_path.read_text(encoding="utf-8"))["name"] == "New"
        finally:
            _clear_overrides(client)


class TestValidateSkill:
    def test_validate_skill_success(self, client):
        mock_service = MagicMock()
        mock_service.get_skill_by_path.return_value = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "Use when testing.",
            "type": "technical",
            "metadata": {"taxonomy_path": "general/test-skill"},
            "content": "---\nname: test-skill\ndescription: Use when testing.\n---\n\n# Test\n",
        }

        _override_skill_service(client, mock_service)
        try:
            with patch(
                "skill_fleet.api.v1.skills.ValidationWorkflow.execute",
                new=AsyncMock(
                    return_value={
                        "validation_report": {
                            "passed": True,
                            "score": 0.95,
                            "issues": [],
                        }
                    }
                ),
            ):
                response = client.post("/api/v1/skills/test-skill/validate")
                assert response.status_code == 200
                data = response.json()
                assert data["passed"] is True
                assert data["score"] == 0.95
        finally:
            _clear_overrides(client)

    def test_validate_skill_not_found(self, client):
        mock_service = MagicMock()
        mock_service.get_skill_by_path.side_effect = FileNotFoundError("not found")

        _override_skill_service(client, mock_service)
        try:
            response = client.post("/api/v1/skills/non-existent-id/validate")
            assert response.status_code == 404
        finally:
            _clear_overrides(client)


class TestRefineSkill:
    def test_refine_skill_success(self, client):
        mock_service = MagicMock()
        mock_service.get_skill_by_path.return_value = {
            "skill_id": "test-skill",
            "name": "Test Skill",
            "description": "Use when testing.",
            "type": "technical",
            "metadata": {"taxonomy_path": "general/test-skill"},
            "content": "---\nname: test-skill\ndescription: Use when testing.\n---\n\n# Test\n",
        }
        mock_service.taxonomy_manager.resolve_skill_location.return_value = "testing/test-skill"
        mock_service.skills_root = MagicMock()

        _override_skill_service(client, mock_service)
        try:
            with patch(
                "skill_fleet.api.v1.skills.ValidationWorkflow.execute",
                new=AsyncMock(return_value={"refined_content": "# Refined\n"}),
            ):
                response = client.post(
                    "/api/v1/skills/test-skill/refine",
                    json={"feedback": "Add more examples", "focus_areas": ["examples"]},
                )
                assert response.status_code == 200
                data = response.json()
                assert "job_id" in data
                assert data["status"] in ("accepted", "completed")
        finally:
            _clear_overrides(client)


class TestListSkills:
    def test_list_skills_success(self, client, tmp_path):
        meta1 = SimpleNamespace(name="Skill 1", description="Desc 1")
        meta2 = SimpleNamespace(name="Skill 2", description="Desc 2")

        mock_service = MagicMock()
        mock_service.taxonomy_manager.metadata_cache = {"skill-1": meta1, "skill-2": meta2}
        mock_service.taxonomy_manager.skills_root = tmp_path
        mock_service.taxonomy_manager._load_skill_dir_metadata = MagicMock()

        _override_skill_service(client, mock_service)
        try:
            response = client.get("/api/v1/skills")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2
        finally:
            _clear_overrides(client)
