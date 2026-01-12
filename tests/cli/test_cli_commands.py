"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest

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

    @patch("skill_fleet.cli.main.configure_dspy")
    @patch("skill_fleet.cli.main.TaxonomySkillCreator")
    @patch("skill_fleet.cli.main.load_fleet_config")
    @patch("skill_fleet.cli.main.TaxonomyManager")
    def test_create_skill_callable(
        self, mock_taxonomy_class, mock_load_config, mock_creator_class, mock_configure
    ):
        """Test create-skill is callable with args."""
        mock_config = {
            "tasks": {
                "skill_understand": {"role": "planner", "model": "gemini/gemini-3-flash-preview"},
                "skill_plan": {"role": "planner", "model": "gemini/gemini-3-flash-preview"},
                "skill_initialize": {"role": "worker", "model": "gemini/gemini-3-flash-preview"},
                "skill_edit": {"role": "worker", "model": "gemini/gemini-3-flash-preview"},
                "skill_package": {"role": "worker", "model": "gemini/gemini-3-flash-preview"},
                "skill_validate": {"role": "judge", "model": "gemini/gemini-3-flash-preview"},
            },
            "roles": {
                "planner": {"model": "gemini/gemini-3-flash-preview"},
                "worker": {"model": "gemini/gemini-3-flash-preview"},
                "judge": {"model": "gemini/gemini-3-flash-preview"},
            },
            "models": {
                "default": "gemini/gemini-3-flash-preview",
                "registry": {
                    "gemini/gemini-3-flash-preview": {
                        "model": "gemini/gemini-3-flash-preview",
                        "model_type": "chat",
                        "timeout": 60,
                        "parameters": {
                            "temperature": 1.0,
                            "max_tokens": 8192,
                        },
                    },
                },
            },
        }
        mock_load_config.return_value = mock_config

        mock_taxonomy_instance = MagicMock()
        mock_taxonomy_class.return_value = mock_taxonomy_instance

        mock_creator_instance = MagicMock()
        mock_creator_instance.return_value = {
            "status": "approved",
            "skill_id": "test-skill",
            "path": "/tmp/test-skill",
        }
        mock_creator_class.return_value = mock_creator_instance

        args = MagicMock()
        args.task = "Create a test skill"
        args.auto_approve = True
        args.user_id = "test-user"
        args.config = "config.yaml"
        args.skills_root = "/tmp/skills"
        args.feedback_type = "auto"
        args.max_iterations = 3
        args.min_rounds = 1
        args.max_rounds = 4
        args.cache_dir = None
        args.reasoning = "none"
        args.json = False
        args.is_training_run = False

        # Act
        result = create_skill(args)

        # Assert
        assert result == 0


class TestValidateSkillCommand:
    """Test validate-skill command."""

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
            "errors": ["Missing YAML frontmatter"],
            "warnings": [],
        }

        args = MagicMock()
        args.skill_path = "skills/invalid/skill"
        args.skills_root = "/tmp/skills"
        args.json = False

        # Act
        result = validate_skill(args)

        # Assert
        assert result == 2  # Exit code for validation failure


class TestTyperApp:
    """Test Typer-based CLI app."""

    def test_app_initialization(self):
        """Test Typer app is properly initialized."""
        # Act & Assert
        assert app is not None
        assert app.info.help == "Skills Fleet - Interactive mode"
