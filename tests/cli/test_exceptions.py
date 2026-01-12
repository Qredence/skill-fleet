"""Tests for CLI custom exceptions."""

from rich.console import Console

from skill_fleet.cli.exceptions import (
    APIError,
    CLIError,
    CLIExit,
    ConfigError,
    ValidationError,
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


# CLIError string representation tests
def test_cli_error_str_without_suggestion():
    """Test CLIError string representation without suggestion."""
    error = CLIError("Test error")
    assert str(error) == "Test error"


def test_cli_error_str_with_suggestion():
    """Test CLIError string representation with suggestion."""
    error = CLIError("Test error", suggestion="Try again")
    result = str(error)
    assert "Test error" in result
    assert "Try again" in result


# CLIError display base class test
def test_cli_error_display_base_class():
    """Test CLIError base class display method."""
    console = Console()
    error = CLIError("Base error", suggestion="Help")
    error.display(console)  # Should not raise


# APIError without status code test
def test_api_error_without_status_code():
    """Test APIError without status code doesn't include HTTP in message."""
    error = APIError("Failed")
    assert error.status_code is None
    assert "HTTP" not in str(error)


# Default suggestion tests
def test_config_error_default_suggestion():
    """Test ConfigError has default suggestion."""
    error = ConfigError("Bad config")
    assert "Check your configuration file" in error.suggestion


def test_api_error_default_suggestion():
    """Test APIError has default suggestion."""
    error = APIError("Failed")
    assert "Check your network connection and API URL" in error.suggestion


def test_validation_error_default_suggestion():
    """Test ValidationError has default suggestion."""
    error = ValidationError("Invalid")
    assert "Run with --help for usage information" in error.suggestion


# CLIExit tests
def test_cli_exit_str_representation():
    """Test CLIExit string representation."""
    error = CLIExit("Done")
    assert str(error) == "Done"


def test_cli_exit_with_none_message():
    """Test CLIExit with None message."""
    error = CLIExit()
    assert error.message is None
    assert str(error) == ""


# Edge case tests
def test_cli_error_with_empty_message():
    """Test CLIError with empty message."""
    error = CLIError("")
    assert error.message == ""


def test_cli_exit_with_zero_exit_code():
    """Test CLIExit with zero exit code."""
    error = CLIExit(exit_code=0)
    assert error.exit_code == 0
