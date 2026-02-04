"""Tests for CLI commands."""

import re
from importlib.metadata import version
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from skill_fleet.cli.app import app
from skill_fleet.cli.main import create_skill, validate_skill


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
    """Test create-skill command."""

    def test_create_skill_imports(self):
        """Test that create_skill can be imported."""
        from skill_fleet.cli.main import create_skill

        assert callable(create_skill)

    def test_create_skill_returns_error(self):
        """Test create-skill returns error (deprecated)."""
        """Test that create_skill returns error code (deprecated function)."""
        args = MagicMock()
        args.task = "Create a test skill"

        # Act
        result = create_skill(args)

        # Assert - should return 1 (error) since it's deprecated
        assert result == 1

    @patch("skill_fleet.cli.main.SkillValidator")
    def test_validate_valid_skill(self, mock_validator_class):
        """Test validate-skill with valid skill."""
        # Arrange
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": True,
            "errors": [],
            "warnings": [],
        }

        args = MagicMock()
        args.skill_path = "skills/general/testing"
        args.skills_root = "/tmp/skills"
        args.json = False

        # Act
        result = validate_skill(args)

        # Assert
        assert result == 0

    @patch("skill_fleet.cli.main.SkillValidator")
    def test_validate_invalid_skill(self, mock_validator_class):
        """Test validate-skill with invalid skill."""
        # Arrange
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": False,
            "errors": ["Missing frontmatter"],
            "warnings": [],
        }

        args = MagicMock()
        args.skill_path = "skills/general/testing"
        args.skills_root = "/tmp/skills"
        args.json = False

        # Act
        result = validate_skill(args)

        # Assert
        assert result == 2


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
