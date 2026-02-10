"""Tests for CLI commands."""

import json
import re
from importlib.metadata import version
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from skill_fleet.cli.app import app


@pytest.fixture
def mock_taxonomy():
    """Mock taxonomy manager."""
    taxonomy = MagicMock()
    return taxonomy


@pytest.fixture
def mock_creator():
    """Mock skill creator."""
    creator = MagicMock()
    return creator


class TestTyperApp:
    """Test Typer-based CLI app."""

    def test_version_flag_prints_package_version(self):
        """Test --version prints the installed package version."""
        runner = CliRunner()

        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert re.match(r"^\d+\.\d+\.\d+\s*$", result.stdout) is not None
        assert result.stdout.strip() == version("skill-fleet")

    def test_app_initialization(self):
        """Test Typer app is properly initialized."""
        # Act & Assert
        assert app is not None
        assert app.info.help == "Skills Fleet - Hierarchical skills taxonomy + DSPy workflow CLI"


class TestApiFirstCliCommands:
    """Test API-first CLI command behavior."""

    def test_validate_command_calls_api_and_outputs_json(self, tmp_path, monkeypatch):
        class FakeClient:
            captured: dict[str, object] = {}

            def __init__(self, base_url: str, user_id: str = "default"):
                self.base_url = base_url

            async def validate_skill(self, skill_path: str, use_llm: bool = True):
                FakeClient.captured = {
                    "skill_path": skill_path,
                    "use_llm": use_llm,
                    "base_url": self.base_url,
                }
                return {
                    "passed": True,
                    "status": "passed",
                    "score": 0.93,
                    "errors": [],
                    "warnings": [],
                    "checks": [],
                }

            async def close(self):
                return None

        monkeypatch.setattr("skill_fleet.cli.commands.validate.SkillFleetClient", FakeClient)

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "validate",
                "testing/sample",
                "--skills-root",
                str(tmp_path / "skills"),
                "--json",
                "--no-llm",
                "--api-url",
                "http://localhost:8999",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["passed"] is True
        assert FakeClient.captured["skill_path"] == "testing/sample"
        assert FakeClient.captured["use_llm"] is False
        assert FakeClient.captured["base_url"] == "http://localhost:8999"

    def test_validate_command_network_error_returns_exit_1(self, tmp_path, monkeypatch):
        class ErrorClient:
            def __init__(self, base_url: str, user_id: str = "default"):
                self.base_url = base_url

            async def validate_skill(self, skill_path: str, use_llm: bool = True):
                raise ValueError("Failed to connect to the API server. Make sure it is running.")

            async def close(self):
                return None

        monkeypatch.setattr("skill_fleet.cli.commands.validate.SkillFleetClient", ErrorClient)

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["validate", "testing/sample", "--skills-root", str(tmp_path / "skills"), "--json"],
        )

        assert result.exit_code == 1
        assert "Failed to connect to the API server" in result.stderr

    def test_generate_xml_command_writes_file_from_api(self, tmp_path, monkeypatch):
        class FakeClient:
            captured: dict[str, object] = {}

            def __init__(self, base_url: str, user_id: str = "default"):
                self.base_url = base_url

            async def generate_xml(self, user_id: str | None = None):
                FakeClient.captured = {"user_id": user_id, "base_url": self.base_url}
                return "<available_skills></available_skills>"

            async def close(self):
                return None

        monkeypatch.setattr("skill_fleet.cli.commands.generate_xml.SkillFleetClient", FakeClient)

        output_file = tmp_path / "skills.xml"
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "generate-xml",
                "--skills-root",
                str(tmp_path / "skills"),
                "--output",
                str(output_file),
                "--user-id",
                "alice",
                "--api-url",
                "http://localhost:8111",
            ],
        )

        assert result.exit_code == 0
        assert output_file.read_text(encoding="utf-8") == "<available_skills></available_skills>"
        assert FakeClient.captured["user_id"] == "alice"
        assert FakeClient.captured["base_url"] == "http://localhost:8111"

    def test_analytics_command_outputs_json_from_api(self, tmp_path, monkeypatch):
        class FakeClient:
            captured: dict[str, object] = {}

            def __init__(self, base_url: str, user_id: str = "default"):
                self.base_url = base_url

            async def get_analytics(self, user_id: str | None = None):
                FakeClient.captured["analytics_user_id"] = user_id
                return {
                    "total_events": 3,
                    "unique_skills_used": 2,
                    "success_rate": 0.67,
                    "most_used_skills": [["technical/fastapi", 2]],
                    "common_combinations": [],
                    "cold_skills": ["technical/httpx"],
                }

            async def get_recommendations(self, user_id: str):
                FakeClient.captured["recommendations_user_id"] = user_id
                return {
                    "user_id": user_id,
                    "recommendations": [
                        {
                            "skill_id": "technical/httpx",
                            "reason": "Required by frequently used skill: technical/fastapi",
                            "priority": "high",
                        }
                    ],
                    "total_recommendations": 1,
                }

            async def close(self):
                return None

        monkeypatch.setattr("skill_fleet.cli.commands.analytics.SkillFleetClient", FakeClient)

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "analytics",
                "--skills-root",
                str(tmp_path / "skills"),
                "--json",
                "--user-id",
                "all",
                "--api-url",
                "http://localhost:8222",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["analytics"]["total_events"] == 3
        assert payload["recommendations"]["total_recommendations"] == 1
        assert FakeClient.captured["analytics_user_id"] is None
        assert FakeClient.captured["recommendations_user_id"] == "default"
