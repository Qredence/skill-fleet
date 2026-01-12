"""Tests for CLI custom exceptions."""

import pytest
from rich.console import Console

from skill_fleet.cli.exceptions import (
    CLIError,
    ConfigError,
    APIError,
    ValidationError,
    CLIExit,
)


def test_cli_error_has_exit_code():
    """Test CLIError has default exit code."""
    error = CLIError("Test error")
    assert error.exit_code == 1
    assert error.message == "Test error"


def test_cli_error_with_custom_exit_code():
    """Test CLIError accepts custom exit code."""
    error = CLIError("Test error", exit_code=2)
    assert error.exit_code == 2


def test_config_error_has_exit_code_2():
    """Test ConfigError has exit code 2."""
    error = ConfigError("Config failed")
    assert error.exit_code == 2


def test_api_error_with_status_code():
    """Test APIError includes status code in message."""
    error = APIError("Request failed", status_code=404)
    assert "404" in str(error)


def test_validation_error_with_suggestion():
    """Test ValidationError includes suggestion."""
    error = ValidationError("Invalid input", suggestion="Use a valid email")
    assert "Use a valid email" in error.suggestion


def test_cli_exit_sets_exit_code():
    """Test CLIExit for typer.Exit compatibility."""
    error = CLIExit("Exiting", exit_code=0)
    assert error.exit_code == 0


def test_error_display_with_rich():
    """Test errors can be displayed with Rich."""
    console = Console()
    error = ConfigError("Bad config", suggestion="Check config.yaml")
    # Should not raise when rendering
    error.display(console)
