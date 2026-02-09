"""Tests for CLI commands."""

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
