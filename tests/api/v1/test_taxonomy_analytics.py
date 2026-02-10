"""Integration-style tests for taxonomy XML and analytics API endpoints."""

from __future__ import annotations

import json
from types import SimpleNamespace

from skill_fleet.api.dependencies import get_taxonomy_manager
from skill_fleet.common.paths import ensure_skills_root_initialized
from skill_fleet.taxonomy.discovery import generate_available_skills_xml
from skill_fleet.taxonomy.manager import TaxonomyManager
from skill_fleet.taxonomy.metadata import InfrastructureSkillMetadata


def _override_taxonomy_manager(client, manager):
    client.app.dependency_overrides[get_taxonomy_manager] = lambda: manager


def _clear_overrides(client):
    client.app.dependency_overrides.clear()


class TestTaxonomyXmlEndpoint:
    def test_generates_available_skills_xml(self, client, tmp_path):
        skills_root = tmp_path / "skills"
        skill_dir = skills_root / "testing" / "xml-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# XML Skill\n", encoding="utf-8")
        metadata_path = skill_dir / "metadata.json"
        metadata_path.write_text("{}", encoding="utf-8")

        manager = SimpleNamespace(
            skills_root=skills_root,
            metadata_cache={
                "testing/xml-skill": InfrastructureSkillMetadata(
                    skill_id="testing/xml-skill",
                    version="1.0.0",
                    type="technical",
                    weight="medium",
                    load_priority="task_specific",
                    dependencies=[],
                    capabilities=[],
                    path=metadata_path,
                    name="xml-skill",
                    description="Skill used for XML endpoint testing",
                )
            },
            generate_available_skills_xml=lambda user_id=None: generate_available_skills_xml(
                {
                    "testing/xml-skill": InfrastructureSkillMetadata(
                        skill_id="testing/xml-skill",
                        version="1.0.0",
                        type="technical",
                        weight="medium",
                        load_priority="task_specific",
                        dependencies=[],
                        capabilities=[],
                        path=metadata_path,
                        name="xml-skill",
                        description="Skill used for XML endpoint testing",
                    )
                },
                skills_root,
                user_id=user_id,
            ),
        )

        _override_taxonomy_manager(client, manager)
        try:
            response = client.get("/api/v1/taxonomy/xml", params={"user_id": "alice"})
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/plain")
            assert "<available_skills>" in response.text
            assert "<name>xml-skill</name>" in response.text
            assert "<description>Skill used for XML endpoint testing</description>" in response.text
            assert "<location>" in response.text
            assert str(skill_dir / "SKILL.md") in response.text
        finally:
            _clear_overrides(client)

    def test_xml_endpoint_loads_uncached_metadata_skill(self, client, tmp_path):
        skills_root = ensure_skills_root_initialized(tmp_path / "skills")
        skill_dir = skills_root / "testing" / "uncached-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Uncached Skill\n", encoding="utf-8")
        (skill_dir / "metadata.json").write_text(
            json.dumps(
                {
                    "skill_id": "testing/uncached-skill",
                    "name": "uncached-skill",
                    "description": "Loaded from disk during XML generation",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        manager = TaxonomyManager(skills_root)

        _override_taxonomy_manager(client, manager)
        try:
            response = client.get("/api/v1/taxonomy/xml")
            assert response.status_code == 200
            assert "<name>uncached-skill</name>" in response.text
            assert str(skill_dir / "SKILL.md") in response.text
        finally:
            _clear_overrides(client)

    def test_xml_endpoint_includes_skill_without_metadata_json(self, client, tmp_path):
        skills_root = ensure_skills_root_initialized(tmp_path / "skills")
        skill_dir = skills_root / "testing" / "v2-no-metadata"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: v2-no-metadata\ndescription: v2 skill without metadata.json\n---\n\n# V2 Skill\n",
            encoding="utf-8",
        )

        manager = TaxonomyManager(skills_root)

        _override_taxonomy_manager(client, manager)
        try:
            response = client.get("/api/v1/taxonomy/xml")
            assert response.status_code == 200
            assert "<name>v2-no-metadata</name>" in response.text
            assert "<description>v2 skill without metadata.json</description>" in response.text
            assert str(skill_dir / "SKILL.md") in response.text
        finally:
            _clear_overrides(client)

    def test_xml_endpoint_user_id_filters_to_mounted_skills(self, client, tmp_path):
        skills_root = ensure_skills_root_initialized(tmp_path / "skills")

        alpha_dir = skills_root / "testing" / "alpha"
        alpha_dir.mkdir(parents=True)
        (alpha_dir / "SKILL.md").write_text("# Alpha\n", encoding="utf-8")
        (alpha_dir / "metadata.json").write_text(
            json.dumps(
                {"skill_id": "testing/alpha", "name": "alpha", "description": "Alpha skill"},
                indent=2,
            ),
            encoding="utf-8",
        )

        beta_dir = skills_root / "testing" / "beta"
        beta_dir.mkdir(parents=True)
        (beta_dir / "SKILL.md").write_text("# Beta\n", encoding="utf-8")
        (beta_dir / "metadata.json").write_text(
            json.dumps(
                {"skill_id": "testing/beta", "name": "beta", "description": "Beta skill"},
                indent=2,
            ),
            encoding="utf-8",
        )

        manager = TaxonomyManager(skills_root)
        manager.get_mounted_skills = lambda _user_id: ["testing/alpha"]  # type: ignore[method-assign]

        _override_taxonomy_manager(client, manager)
        try:
            all_response = client.get("/api/v1/taxonomy/xml")
            assert all_response.status_code == 200
            assert "<name>alpha</name>" in all_response.text
            assert "<name>beta</name>" in all_response.text

            filtered_response = client.get("/api/v1/taxonomy/xml", params={"user_id": "alice"})
            assert filtered_response.status_code == 200
            assert "<name>alpha</name>" in filtered_response.text
            assert "<name>beta</name>" not in filtered_response.text
        finally:
            _clear_overrides(client)


class TestAnalyticsEndpoints:
    def test_returns_empty_analytics_when_usage_log_missing(self, client, tmp_path):
        skills_root = tmp_path / "skills"
        skills_root.mkdir(parents=True)
        manager = SimpleNamespace(
            skills_root=skills_root, get_skill_metadata=lambda _skill_id: None
        )

        _override_taxonomy_manager(client, manager)
        try:
            response = client.get("/api/v1/analytics")
            assert response.status_code == 200
            data = response.json()
            assert data["total_events"] == 0
            assert data["unique_skills_used"] == 0
            assert data["most_used_skills"] == []
            assert data["common_combinations"] == []
            assert data["cold_skills"] == []

            rec_response = client.get(
                "/api/v1/analytics/recommendations", params={"user_id": "alice"}
            )
            assert rec_response.status_code == 200
            rec_data = rec_response.json()
            assert rec_data["user_id"] == "alice"
            assert rec_data["recommendations"] == []
            assert rec_data["total_recommendations"] == 0
        finally:
            _clear_overrides(client)

    def test_filters_analytics_by_user_and_returns_recommendations(self, client, tmp_path):
        skills_root = tmp_path / "skills"
        analytics_dir = skills_root / "_analytics"
        analytics_dir.mkdir(parents=True)
        usage_file = analytics_dir / "usage_log.jsonl"

        entries = [
            {
                "timestamp": "2026-02-09T12:00:00Z",
                "skill_id": "technical/fastapi",
                "user_id": "alice",
                "success": True,
                "task_id": "task-1",
                "metadata": {},
            },
            {
                "timestamp": "2026-02-09T12:05:00Z",
                "skill_id": "technical/fastapi",
                "user_id": "alice",
                "success": True,
                "task_id": "task-2",
                "metadata": {},
            },
            {
                "timestamp": "2026-02-09T12:10:00Z",
                "skill_id": "technical/react",
                "user_id": "bob",
                "success": False,
                "task_id": "task-3",
                "metadata": {},
            },
        ]
        usage_file.write_text(
            "\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8"
        )

        class _Meta:
            dependencies = ["technical/httpx"]

        manager = SimpleNamespace(
            skills_root=skills_root,
            get_skill_metadata=lambda skill_id: _Meta()
            if skill_id == "technical/fastapi"
            else None,
        )

        _override_taxonomy_manager(client, manager)
        try:
            response = client.get("/api/v1/analytics", params={"user_id": "alice"})
            assert response.status_code == 200
            data = response.json()
            assert data["total_events"] == 2
            assert data["unique_skills_used"] == 1
            assert data["most_used_skills"][0][0] == "technical/fastapi"
            assert data["success_rate"] == 1.0

            rec_response = client.get(
                "/api/v1/analytics/recommendations", params={"user_id": "alice"}
            )
            assert rec_response.status_code == 200
            rec_data = rec_response.json()
            assert rec_data["user_id"] == "alice"
            assert rec_data["total_recommendations"] >= 1
            assert any(rec["skill_id"] == "technical/httpx" for rec in rec_data["recommendations"])
        finally:
            _clear_overrides(client)
