"""Custom exception classes for CLI error handling.

This module provides CLI-specific wrappers around common exceptions with
Rich formatting and exit code support. The CLI exceptions inherit from
the common exception hierarchy but add presentation layer functionality.

Design:
- CLIError adds exit codes and Rich formatting to any exception
- ConfigError wraps ConfigurationError from common
- APIError wraps APIError from common
- ValidationError wraps validation exceptions from common
"""

from typing import Any

from rich.panel import Panel
from rich.text import Text

from skill_fleet.common.exceptions import (
    APIError as BaseAPIError,
)
from skill_fleet.common.exceptions import (
    ConfigurationError,
    SkillsFleetError,
    SkillValidationError,
)

# Module constants for exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4


class CLIError(SkillsFleetError):
    """Base exception class for CLI errors.

    Extends SkillsFleetError with CLI-specific features:
    - Exit codes for process termination
    - Rich formatting for terminal display
    - User-friendly suggestions

    Attributes:
        message: Error message to display
        exit_code: Process exit code (default: EXIT_ERROR = 1)
        suggestion: Optional helpful suggestion for the user

    Example:
        raise CLIError("Something went wrong", suggestion="Try again later")
    """

    def __init__(
        self,
        message: str,
        *,
        exit_code: int = EXIT_ERROR,
        suggestion: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Initialize a CLI error.

        Args:
            message: Human-readable error message
            exit_code: Process exit code (default: 1)
            suggestion: Optional helpful suggestion
            details: Optional context details (inherited from SkillsFleetError)
        """
        super().__init__(message, details=details)
        self.exit_code = exit_code
        self.suggestion = suggestion

    def __str__(self) -> str:
        """Return string representation of the error."""
        base_str = super().__str__()
        if self.suggestion:
            return f"{base_str}\n\n💡 {self.suggestion}"
        return base_str

    def display(self, console: Any) -> None:
        """Display the error using Rich formatting.

        Args:
            console: Rich Console instance for output
        """
        # Build error text with suggestion if available
        error_text = Text(self.message, style="bold red")

        if self.suggestion:
            error_text.append("\n\n", style="red")
            error_text.append(f"💡 Suggestion: {self.suggestion}", style="yellow")

        # Display in a panel
        panel = Panel(
            error_text,
            title="❌ Error",
            border_style="red",
            padding=(1, 2),
        )
        console.print(panel)


class ConfigError(CLIError, ConfigurationError):
    """CLI wrapper for configuration errors.

    Combines ConfigurationError from common with CLI display features.
    Used when the CLI configuration is missing, invalid, or malformed.

    Example:
        raise ConfigError("Missing API key in config file")
    """

    def __init__(
        self,
        message: str,
        *,
        config_key: str | None = None,
        suggestion: str | None = "Check your configuration file",
    ) -> None:
        """Initialize a configuration error.

        Args:
            message: Human-readable error message
            config_key: Optional configuration key that caused the error
            suggestion: Optional helpful suggestion (default: "Check your configuration file")
        """
        # Initialize ConfigurationError properly
        ConfigurationError.__init__(self, message, config_key=config_key)
        # Add CLI-specific attributes
        self.exit_code = EXIT_CONFIG_ERROR
        self.suggestion = suggestion


class APIError(CLIError, BaseAPIError):
    """CLI wrapper for API-related errors.

    Combines APIError from common with CLI display features.
    Used when API requests fail due to network issues, server errors,
    or invalid responses.

    Attributes:
        status_code: Optional HTTP status code from the API response

    Example:
        raise APIError("Request failed", status_code=404)
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        suggestion: str | None = "Check your network connection and API URL",
    ) -> None:
        """Initialize an API error.

        Args:
            message: Human-readable error message
            status_code: Optional HTTP status code
            suggestion: Optional helpful suggestion (default: "Check your network connection and API URL")
        """
        self.status_code = status_code
        enhanced_message = message

        # Include status code in message if provided
        if status_code is not None:
            enhanced_message = f"{message} (HTTP {status_code})"

        # Initialize base classes
        BaseAPIError.__init__(self, enhanced_message)
        self.exit_code = EXIT_NETWORK_ERROR
        self.suggestion = suggestion


class ValidationError(CLIError, SkillValidationError):
    """CLI wrapper for validation errors.

    Combines SkillValidationError from common with CLI display features.
    Used when user input fails validation checks (e.g., invalid
    arguments, malformed data, constraint violations).

    Example:
        raise ValidationError("Invalid email address")
    """

    def __init__(
        self,
        message: str,
        *,
        suggestion: str | None = "Run with --help for usage information",
    ) -> None:
        """Initialize a validation error.

        Args:
            message: Human-readable error message
            suggestion: Optional helpful suggestion (default: "Run with --help for usage information")
        """
        SkillValidationError.__init__(self, message)
        self.exit_code = EXIT_VALIDATION_ERROR
        self.suggestion = suggestion


class CLIExit(SkillsFleetError):
    """Exception for clean CLI exits.

    This exception is compatible with typer.Exit and can be used
    for clean exits without displaying error messages.

    Attributes:
        message: Optional exit message
        exit_code: Process exit code (default: EXIT_SUCCESS = 0)

    Example:
        raise CLIExit("Operation completed successfully")
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        exit_code: int = EXIT_SUCCESS,
    ) -> None:
        """Initialize a CLI exit.

        Args:
            message: Optional exit message
            exit_code: Process exit code (default: 0)
        """
        super().__init__(message or "")
        self.exit_code = exit_code

    def __str__(self) -> str:
        """Return string representation of the exit."""
        return self.message or ""
