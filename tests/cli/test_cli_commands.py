"""Tests for CLI commands."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from skill_fleet.cli.app import CLIConfig, app
from skill_fleet.cli.commands.create import create_command
from skill_fleet.cli.commands.validate import validate_command


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


class TestCreateSkillCommand:
    """Test create command behavior."""

    def test_create_command_imports(self):
        """create_command should be importable and callable."""
        from skill_fleet.cli.commands.create import create_command as imported

        assert callable(imported)

    def test_create_command_invokes_client(self):
        """create_command should call the client and close it on completion."""

        # Arrange
        client = MagicMock()
        client.create_skill = AsyncMock(return_value={"job_id": "job-123"})
        client.get_hitl_prompt = AsyncMock(
            return_value={"status": "completed", "saved_path": "/tmp/skill"}
        )
        client.close = AsyncMock()

        config = CLIConfig(api_url="http://localhost:8000", user_id="tester")
        config.client = client

        ctx = MagicMock()
        ctx.obj = config

        # Act
        create_command(ctx, task="Create a test skill", auto_approve=True)

        # Assert
        client.create_skill.assert_awaited_once_with("Create a test skill", "tester")
        client.get_hitl_prompt.assert_awaited()
        client.close.assert_awaited_once()


class TestValidateSkillCommand:
    """Test validate command behavior."""

    @patch("skill_fleet.cli.commands.validate.SkillValidator")
    def test_validate_valid_skill(self, mock_validator_class):
        """validate_command should exit cleanly when validation passes."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        validate_command("skills/general/testing", skills_root="/tmp/skills", json_output=False)

        mock_validator.validate_complete.assert_called_once()

    @patch("skill_fleet.cli.commands.validate.SkillValidator")
    def test_validate_invalid_skill(self, mock_validator_class):
        """validate_command should raise typer.Exit with code 2 on failure."""
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": False,
            "errors": ["Missing YAML frontmatter"],
            "warnings": [],
        }

        with pytest.raises(typer.Exit) as exc_info:
            validate_command("skills/invalid/skill", skills_root="/tmp/skills", json_output=False)

        assert exc_info.value.exit_code == 2


class TestTyperApp:
    """Test Typer-based CLI app."""

    def test_app_initialization(self):
        """Test Typer app is properly initialized."""
        # Act & Assert
        assert app.info.name == "skill-fleet"
        assert app is not None

    def test_cli_config_class(self):
        """Test CLIConfig class initialization."""
        # Act
        config = CLIConfig(api_url="http://localhost:8000", user_id="test-user")

        # Assert
        assert config.api_url == "http://localhost:8000"
        assert config.user_id == "test-user"
        assert config.client is not None
