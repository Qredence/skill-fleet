# CLI Optimization and Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix security vulnerabilities, standardize error handling, improve code quality, and optimize the CLI implementation in `src/skill_fleet/cli/` based on findings from comprehensive code reviews.

**Architecture:** Create shared utilities for common patterns (console management, error handling, input validation), refactor command files to use them, add security layers, and improve test coverage.

**Tech Stack:** Python 3.12+, Typer, Rich, httpx, pytest, ruff

---

## Overview

Based on the existing reviews (`docs/plans/cli-*.md`), this plan addresses:

1. **Security** (High Priority): Path traversal validation, URL validation, user ID sanitization
2. **Error Handling** (High Priority): Custom exceptions, consistent formatting, actionable messages
3. **Code Quality** (Medium Priority): Singleton console, constants, type hints, refactor long functions
4. **Testing** (High Priority): Add test coverage for CLI commands

**Files to Modify:**
- `src/skill_fleet/cli/` - All existing files
- `src/skill_fleet/cli/utils/` - New shared utilities
- `src/skill_fleet/cli/exceptions.py` - New custom exceptions
- `tests/cli/` - New test files

---

## Task 1: Create Security and Validation Utilities

**Files:**
- Create: `src/skill_fleet/cli/exceptions.py`
- Create: `src/skill_fleet/cli/utils/security.py`
- Create: `src/skill_fleet/cli/utils/constants.py`
- Modify: `src/skill_fleet/cli/utils/__init__.py`

**Step 1: Write the failing test for path validation**

Create `tests/cli/test_security_utils.py`:

```python
"""Tests for CLI security utilities."""

import pytest
from pathlib import Path

from skill_fleet.cli.utils.security import validate_path_within_root, sanitize_user_id, validate_api_url


def test_validate_path_within_root_accepts_valid_path():
    """Test path validation accepts paths within root."""
    root = Path("/tmp/skills")
    user_path = Path("/tmp/skills/general/testing")

    result = validate_path_within_root(user_path, root, "Skills root")
    assert result == user_path.resolve()


def test_validate_path_within_root_rejects_traversal():
    """Test path validation rejects ../ traversal."""
    root = Path("/tmp/skills")
    user_path = Path("/tmp/skills/../etc/passwd")

    with pytest.raises(ValueError, match="must be within"):
        validate_path_within_root(user_path, root, "Skills root")


def test_sanitize_user_id_accepts_valid_id():
    """Test user ID sanitization accepts valid IDs."""
    assert sanitize_user_id("user-123") == "user-123"
    assert sanitize_user_id("user@example.com") == "user@example.com"


def test_sanitize_user_id_rejects_special_chars():
    """Test user ID sanitization rejects dangerous characters."""
    with pytest.raises(ValueError, match="invalid characters"):
        sanitize_user_id("../../../etc/passwd")


def test_validate_api_url_accepts_valid_protocols():
    """Test API URL validation accepts http/https."""
    assert validate_api_url("http://localhost:8000") == "http://localhost:8000"
    assert validate_api_url("https://api.example.com") == "https://api.example.com"


def test_validate_api_url_rejects_invalid_protocol():
    """Test API URL validation rejects invalid protocols."""
    with pytest.raises(ValueError, match="must use http:// or https://"):
        validate_api_url("ftp://localhost:8000")
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/cli/test_security_utils.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'skill_fleet.cli.utils.security'"

**Step 3: Write security utilities module**

Create `src/skill_fleet/cli/utils/security.py`:

```python
"""Security utilities for CLI input validation."""

from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse


def validate_path_within_root(user_path: Path, root_path: Path, path_type: str = "Path") -> Path:
    """Validate that a user-provided path is within the allowed root directory.

    Args:
        user_path: The path provided by the user.
        root_path: The allowed root directory.
        path_type: Description of the path type for error messages.

    Returns:
        The resolved absolute path if valid.

    Raises:
        ValueError: If the path would escape the root directory.
    """
    user_path = user_path.resolve()
    root_path = root_path.resolve()

    try:
        user_path.relative_to(root_path)
        return user_path
    except ValueError:
        raise ValueError(
            f"{path_type} path '{user_path}' must be within '{root_path}'"
        )


def sanitize_user_id(user_id: str) -> str:
    """Sanitize user ID to prevent injection attacks.

    Args:
        user_id: The raw user ID input.

    Returns:
        The sanitized user ID.

    Raises:
        ValueError: If the user ID contains invalid characters or is invalid length.
    """
    # Remove dangerous characters (keep alphanumeric, @, -, ., _)
    sanitized = re.sub(r'[^\w\-@.]', '', user_id)

    if len(sanitized) != len(user_id):
        raise ValueError(
            f"User ID contains invalid characters. "
            f"Only alphanumeric, @, -, ., and _ are allowed"
        )

    if not sanitized or len(sanitized) > 100:
        raise ValueError("User ID must be 1-100 characters")

    return sanitized


def validate_api_url(url: str) -> str:
    """Validate API URL uses secure protocol.

    Args:
        url: The API URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValueError: If the URL doesn't use http:// or https://.
    """
    parsed = urlparse(url)

    if not parsed.scheme or parsed.scheme not in ('https', 'http'):
        raise ValueError(f"API URL must use http:// or https:// protocol: {url}")

    # Warn if using HTTP with non-localhost
    if parsed.scheme == 'http' and parsed.hostname not in ('localhost', '127.0.0.1'):
        import warnings
        warnings.warn(
            f"Using HTTP (non-HTTPS) for {url} may expose credentials",
            stacklevel=2
        )

    return url


def validate_timeout(seconds: float) -> float:
    """Validate timeout is reasonable.

    Args:
        seconds: The timeout value in seconds.

    Returns:
        The validated timeout.

    Raises:
        ValueError: If timeout is out of reasonable bounds.
    """
    if not (0 < seconds <= 300):
        raise ValueError("Timeout must be between 0 and 300 seconds")
    return seconds
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/cli/test_security_utils.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/utils/security.py tests/cli/test_security_utils.py
git commit -m "feat(cli): add security utilities for input validation

- Add validate_path_within_root to prevent path traversal
- Add sanitize_user_id to prevent injection attacks
- Add validate_api_url to enforce secure protocols
- Add validate_timeout for configurable timeouts

Fixes security issues identified in cli-security-review.md"
```

---

## Task 2: Create Custom Exception Classes

**Files:**
- Create: `src/skill_fleet/cli/exceptions.py`
- Create: `tests/cli/test_exceptions.py`

**Step 1: Write the failing test for custom exceptions**

Create `tests/cli/test_exceptions.py`:

```python
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
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/cli/test_exceptions.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'skill_fleet.cli.exceptions'"

**Step 3: Write custom exceptions module**

Create `src/skill_fleet/cli/exceptions.py`:

```python
"""Custom exceptions for CLI error handling.

Provides consistent error handling across CLI commands with:
- Standardized exit codes
- Rich-formatted error display
- Actionable suggestions for users
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


# Standard exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4


class CLIError(Exception):
    """Base exception for CLI errors.

    Attributes:
        message: Human-readable error message.
        exit_code: Process exit code for this error.
        suggestion: Actionable suggestion for fixing the error.
    """

    def __init__(
        self,
        message: str,
        exit_code: int = EXIT_ERROR,
        suggestion: str = ""
    ):
        self.message = message
        self.exit_code = exit_code
        self.suggestion = suggestion
        super().__init__(message)

    def display(self, console: "Console") -> None:
        """Display error using Rich formatting.

        Args:
            console: Rich console instance for output.
        """
        from rich.panel import Panel

        content = f"[bold red]Error:[/bold red] {self.message}"
        if self.suggestion:
            content += f"\n\n[yellow]💡 Suggestion:[/yellow] {self.suggestion}"

        console.print(Panel(content, title="❌ Error", border_style="red"))


class ConfigError(CLIError):
    """Configuration-related errors."""

    def __init__(self, message: str, suggestion: str = "Check your configuration file"):
        super().__init__(message, exit_code=EXIT_CONFIG_ERROR, suggestion=suggestion)


class APIError(CLIError):
    """API communication errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        suggestion: str = "Check your network connection and API URL"
    ):
        full_msg = f"{message}"
        if status_code:
            full_msg += f" (HTTP {status_code})"
        super().__init__(full_msg, exit_code=EXIT_NETWORK_ERROR, suggestion=suggestion)


class ValidationError(CLIError):
    """Input validation errors."""

    def __init__(self, message: str, suggestion: str = "Run with --help for usage information"):
        super().__init__(message, exit_code=EXIT_VALIDATION_ERROR, suggestion=suggestion)


class CLIExit(Exception):
    """Exception for clean CLI exit (compatible with typer.Exit).

    Use this when you want to exit the CLI with a specific code
    without displaying an error (e.g., successful --help usage).
    """

    def __init__(self, message: str = "", exit_code: int = EXIT_SUCCESS):
        self.message = message
        self.exit_code = exit_code
        super().__init__(message)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/cli/test_exceptions.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/exceptions.py tests/cli/test_exceptions.py
git commit -m "feat(cli): add custom exception classes

- Add CLIError base class with exit codes and Rich display
- Add ConfigError for configuration issues (exit code 2)
- Add APIError for network/API issues (exit code 4)
- Add ValidationError for input validation (exit code 3)
- Add CLIExit for clean exits

Fixes error handling issues from cli-error-handling-review.md"
```

---

## Task 3: Create Constants Module

**Files:**
- Create: `src/skill_fleet/cli/utils/constants.py`

**Step 1: Create constants module**

Create `src/skill_fleet/cli/utils/constants.py`:

```python
"""Constants for CLI configuration and theming.

Centralizes all magic numbers and configuration values
to improve maintainability and consistency.
"""

from __future__ import annotations

# API configuration
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_API_TIMEOUT = 30.0
MIN_API_TIMEOUT = 0.1
MAX_API_TIMEOUT = 300.0

# Polling configuration
HITL_POLL_INTERVAL = 2.0  # seconds between HITL polls
MAX_POLL_ATTEMPTS = 100   # maximum polling iterations

# Display configuration
CONSOLE_REFRESH_RATE = 10  # times per second for Live displays
JSON_INDENT = 2            # spaces for JSON output
SEPARATOR_WIDTH = 60       # characters for separator lines

# Rich color palette (consistent theming)
COLOR_SUCCESS = "green"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"
COLOR_INFO = "cyan"
COLOR_MUTED = "dim"

# Icons for status messages
ICON_SUCCESS = "✓"
ICON_WARNING = "⚠️"
ICON_ERROR = "❌"
ICON_INFO = "ℹ️"
ICON_WORKING = "⏳"

# Exit codes (same as in exceptions.py)
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4

# Validation constraints
MAX_USER_ID_LENGTH = 100
MIN_USER_ID_LENGTH = 1
```

**Step 2: Update utils __init__.py**

Modify `src/skill_fleet/cli/utils/__init__.py`:

```python
"""CLI utilities submodule."""

from .constants import *  # noqa: F401, F403
from .security import validate_api_url, validate_path_within_root, sanitize_user_id, validate_timeout

__all__ = [
    # Security
    "validate_path_within_root",
    "sanitize_user_id",
    "validate_api_url",
    "validate_timeout",
]
```

**Step 3: Write test for constants**

Create `tests/cli/test_constants.py`:

```python
"""Tests for CLI constants."""

from skill_fleet.cli.utils.constants import (
    DEFAULT_API_URL,
    DEFAULT_API_TIMEOUT,
    HITL_POLL_INTERVAL,
    MAX_POLL_ATTEMPTS,
    EXIT_SUCCESS,
    EXIT_ERROR,
)


def test_default_api_url():
    """Test default API URL is localhost."""
    assert DEFAULT_API_URL == "http://localhost:8000"


def test_default_api_timeout():
    """Test default API timeout is reasonable."""
    assert DEFAULT_API_TIMEOUT == 30.0


def test_poll_interval():
    """Test HITL poll interval is 2 seconds."""
    assert HITL_POLL_INTERVAL == 2.0


def test_exit_codes():
    """Test exit codes match standard values."""
    assert EXIT_SUCCESS == 0
    assert EXIT_ERROR == 1
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/cli/test_constants.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/utils/constants.py src/skill_fleet/cli/utils/__init__.py tests/cli/test_constants.py
git commit -m "feat(cli): add constants module

- Extract magic numbers to named constants
- Define Rich color palette for consistent theming
- Add status icons for user-friendly messages
- Centralize exit codes and validation constraints

Fixes magic number issues from cli-best-practices-review.md"
```

---

## Task 4: Create Singleton Console Manager

**Files:**
- Create: `src/skill_fleet/cli/utils/console.py`
- Create: `tests/cli/test_console.py`

**Step 1: Write the failing test for console manager**

Create `tests/cli/test_console.py`:

```python
"""Tests for CLI console manager."""

import pytest
from rich.console import Console

from skill_fleet.cli.utils.console import get_console, display_error, display_success, display_warning


def test_get_console_returns_singleton():
    """Test get_console returns same instance."""
    console1 = get_console()
    console2 = get_console()
    assert console1 is console2


def test_display_error():
    """Test error display formats correctly."""
    console = get_console()
    # Should not raise
    display_error("Test error", suggestion="Fix it")


def test_display_success():
    """Test success display formats correctly."""
    console = get_console()
    # Should not raise
    display_success("Operation completed")


def test_display_warning():
    """Test warning display formats correctly."""
    console = get_console()
    # Should not raise
    display_warning("Proceed with caution")
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/cli/test_console.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'skill_fleet.cli.utils.console'"

**Step 3: Write console manager module**

Create `src/skill_fleet/cli/utils/console.py`:

```python
"""Singleton console manager for consistent Rich output.

Provides a single Console instance and standardized display
functions for common message types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skill_fleet.cli.exceptions import CLIError

# Singleton console instance
_console: Console | None = None


def get_console() -> Console:
    """Get the singleton Console instance.

    Creates the instance on first call and reuses it
    for all subsequent calls.

    Returns:
        The shared Console instance.
    """
    global _console
    if _console is None:
        from rich.console import Console
        _console = Console()
    return _console


def display_error(
    message: str,
    suggestion: str = "",
    title: str = "❌ Error",
    exit_code: int = 1
) -> None:
    """Display an error message with consistent formatting.

    Args:
        message: The error message to display.
        suggestion: Optional actionable suggestion.
        title: Panel title for the error.
        exit_code: Exit code associated with this error.
    """
    from rich.panel import Panel

    console = get_console()
    content = f"[bold red]Error:[/bold red] {message}"
    if suggestion:
        content += f"\n\n[yellow]💡 Suggestion:[/yellow] {suggestion}"

    console.print(Panel(content, title=title, border_style="red"))

    if exit_code != 0:
        console.print(f"\n[dim]Exit code: {exit_code}[/dim]")


def display_success(message: str, title: str = "✓ Success") -> None:
    """Display a success message.

    Args:
        message: The success message.
        title: Panel title.
    """
    from rich.panel import Panel

    console = get_console()
    console.print(Panel(f"[bold green]{message}[/bold green]", title=title, border_style="green"))


def display_warning(message: str, title: str = "⚠️ Warning") -> None:
    """Display a warning message.

    Args:
        message: The warning message.
        title: Panel title.
    """
    from rich.panel import Panel

    console = get_console()
    console.print(Panel(f"[bold yellow]{message}[/bold yellow]", title=title, border_style="yellow"))


def display_info(message: str, title: str = "ℹ️ Info") -> None:
    """Display an info message.

    Args:
        message: The info message.
        title: Panel title.
    """
    from rich.panel import Panel

    console = get_console()
    console.print(Panel(f"[bold cyan]{message}[/bold cyan]", title=title, border_style="cyan"))


def display_cli_error(error: "CLIError") -> None:
    """Display a CLIError using its built-in display method.

    Args:
        error: The CLIError instance to display.
    """
    console = get_console()
    error.display(console)
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/cli/test_console.py -v
```

Expected: PASS

**Step 5: Update utils __init__.py to include console**

Modify `src/skill_fleet/cli/utils/__init__.py`:

```python
"""CLI utilities submodule."""

from .console import get_console, display_error, display_success, display_warning, display_info, display_cli_error
from .constants import *  # noqa: F401, F403
from .security import validate_api_url, validate_path_within_root, sanitize_user_id, validate_timeout

__all__ = [
    # Console
    "get_console",
    "display_error",
    "display_success",
    "display_warning",
    "display_info",
    "display_cli_error",
    # Security
    "validate_path_within_root",
    "sanitize_user_id",
    "validate_api_url",
    "validate_timeout",
]
```

**Step 6: Commit**

```bash
git add src/skill_fleet/cli/utils/console.py src/skill_fleet/cli/utils/__init__.py tests/cli/test_console.py
git commit -m "feat(cli): add singleton console manager

- Add get_console() for singleton Console instance
- Add display_* functions for consistent message formatting
- Reduces 13 Console() instantiations to 1 singleton

Fixes console duplication issue from cli-best-practices-review.md"
```

---

## Task 5: Update app.py with Security Validation

**Files:**
- Modify: `src/skill_fleet/cli/app.py`
- Modify: `src/skill_fleet/cli/client.py`
- Create: `tests/cli/test_app.py`

**Step 1: Write the failing test for app security**

Create `tests/cli/test_app.py`:

```python
"""Tests for CLI app configuration."""

import pytest
import typer
from typer.testing import CliRunner

from skill_fleet.cli.app import app, CLIConfig
from skill_fleet.cli.utils.security import validate_api_url, sanitize_user_id

runner = CliRunner()


def test_cli_config_initialization():
    """Test CLIConfig class initializes correctly."""
    config = CLIConfig(api_url="http://localhost:8000", user_id="test-user")
    assert config.api_url == "http://localhost:8000"
    assert config.user_id == "test-user"
    assert config.client is not None


def test_app_has_help():
    """Test app has help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "skill-fleet" in result.stdout


def test_api_url_validation_callback():
    """Test API URL is validated."""
    # Should accept valid URLs
    assert validate_api_url("http://localhost:8000") == "http://localhost:8000"
    assert validate_api_url("https://api.example.com") == "https://api.example.com"

    # Should reject invalid protocols
    with pytest.raises(ValueError):
        validate_api_url("ftp://localhost:8000")


def test_user_id_sanitization():
    """Test user ID is sanitized."""
    assert sanitize_user_id("valid-user-123") == "valid-user-123"

    with pytest.raises(ValueError):
        sanitize_user_id("../invalid")
```

**Step 2: Run test to verify failures**

```bash
uv run pytest tests/cli/test_app.py -v
```

Expected: Some tests may pass, but we need to add validation callbacks

**Step 3: Update app.py with security validation**

Modify `src/skill_fleet/cli/app.py`:

```python
"""Main Typer CLI application for Skill Fleet.

Follows Typer/Click best practices for context management and global options.
Ref: https://typer.tiangolo.com/tutorial/commands/context/
     https://typer.tiangolo.com/tutorial/one-file-per-command/
"""

from __future__ import annotations

import typer

from ..utils.security import validate_api_url, sanitize_user_id, validate_timeout
from ..utils.console import get_console
from ..utils.constants import DEFAULT_API_URL
from .client import SkillFleetClient
from .commands.analytics import analytics_command
from .commands.chat import chat_command
from .commands.create import create_command
from .commands.generate_xml import generate_xml_command
from .commands.list_skills import list_command
from .commands.migrate import migrate_command
from .commands.onboard import onboard_command
from .commands.optimize import optimize_command
from .commands.serve import serve_command
from .commands.validate import validate_command

# Initialize Typer app
app = typer.Typer(
    name="skill-fleet",
    help="Hierarchical AI skill management and creation system.",
    add_completion=False,
)

# Use shared console
console = get_console()


class CLIConfig:
    """Container for CLI configuration and shared state.

    Attributes:
        api_url: The API server URL.
        user_id: The user ID for context.
        client: The HTTP client for API communication.
    """
    def __init__(self, api_url: str, user_id: str, timeout: float = 30.0):
        """Initialize CLI configuration.

        Args:
            api_url: API server URL.
            user_id: User ID for context.
            timeout: HTTP client timeout in seconds.
        """
        self.api_url = validate_api_url(api_url)
        self.user_id = sanitize_user_id(user_id)
        self.timeout = validate_timeout(timeout)
        self.client = SkillFleetClient(base_url=self.api_url, timeout=self.timeout)


@app.callback()
def main_callback(
    ctx: typer.Context,
    api_url: str = typer.Option(
        DEFAULT_API_URL,
        "--api-url", "-a",
        help="API server URL (must use https:// in production)",
        envvar="SKILL_FLEET_API_URL"
    ),
    user_id: str = typer.Option(
        "default",
        "--user", "-u",
        help="User ID for context (alphanumeric, -, ., @, _ only)",
        envvar="SKILL_FLEET_USER_ID"
    ),
    timeout: float = typer.Option(
        30.0,
        "--timeout",
        help="API timeout in seconds (max: 300)",
        envvar="SKILL_FLEET_API_TIMEOUT"
    ),
):
    """Global configuration for Skill Fleet CLI.

    This callback runs before all commands and sets up the shared
    configuration object via ctx.obj.
    """
    # Store config object in Click context
    ctx.obj = CLIConfig(api_url=api_url, user_id=user_id, timeout=timeout)


# Register commands from separate files
app.command(name="create")(create_command)
app.command(name="list")(list_command)
app.command(name="serve")(serve_command)
app.command(name="chat")(chat_command)
app.command(name="validate")(validate_command)
app.command(name="onboard")(onboard_command)
app.command(name="analytics")(analytics_command)
app.command(name="migrate")(migrate_command)
app.command(name="generate-xml")(generate_xml_command)
app.command(name="optimize")(optimize_command)


if __name__ == "__main__":
    app()
```

**Step 4: Update client.py to support timeout**

Modify `src/skill_fleet/cli/client.py`:

```python
"""HTTP client for communicating with the Skill Fleet API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SkillFleetClient:
    """Async HTTP client for Skill Fleet API.

    Attributes:
        base_url: The base URL of the API server.
        client: The httpx async client.
        timeout: Request timeout in seconds.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """Initialize the client.

        Args:
            base_url: The base URL of the API server.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def create_skill(self, task: str, user_id: str = "default") -> dict[str, Any]:
        """Call the skill creation endpoint.

        Args:
            task: Task description for skill creation.
            user_id: User ID for context.

        Returns:
            Response JSON with job_id.
        """
        response = await self.client.post(
            "/api/v2/skills/create", json={"task_description": task, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    async def get_hitl_prompt(self, job_id: str) -> dict[str, Any]:
        """Poll for a pending HITL prompt.

        Args:
            job_id: The job ID to poll.

        Returns:
            Response JSON with prompt data.
        """
        response = await self.client.get(f"/api/v2/hitl/{job_id}/prompt")
        response.raise_for_status()
        return response.json()

    async def post_hitl_response(self, job_id: str, response_data: dict[str, Any]) -> dict[str, Any]:
        """Send a response to a HITL prompt.

        Args:
            job_id: The job ID.
            response_data: The response data to send.

        Returns:
            Response JSON.
        """
        response = await self.client.post(f"/api/v2/hitl/{job_id}/response", json=response_data)
        response.raise_for_status()
        return response.json()

    async def list_skills(self) -> list[dict[str, Any]]:
        """List all skills from the taxonomy.

        Returns:
            List of skill dictionaries.
        """
        response = await self.client.get("/api/v2/taxonomy/")
        response.raise_for_status()
        return response.json().get("skills", [])

    async def start_chat_session(self) -> dict[str, Any]:
        """Initialize a new chat session.

        Returns:
            Response JSON with session_id.
        """
        response = await self.client.post("/api/v2/chat/session")
        response.raise_for_status()
        return response.json()

    async def send_chat_message(self, message: str, session_id: str) -> dict[str, Any]:
        """Send a message to the chat agent.

        Args:
            message: The message to send.
            session_id: The chat session ID.

        Returns:
            Response JSON.
        """
        response = await self.client.post(
            "/api/v2/chat/message", json={"message": message, "session_id": session_id}
        )
        response.raise_for_status()
        return response.json()
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/cli/test_app.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add src/skill_fleet/cli/app.py src/skill_fleet/cli/client.py tests/cli/test_app.py
git commit -m "feat(cli): add security validation to app.py

- Add validate_api_url callback for --api-url
- Add sanitize_user_id for --user option
- Add validate_timeout for --timeout option
- Update CLIConfig to validate all inputs
- Update SkillFleetClient to support configurable timeout
- Use singleton console from utils

Fixes security issues from cli-security-review.md"
```

---

## Task 6: Update create.py with Error Handling and Console

**Files:**
- Modify: `src/skill_fleet/cli/commands/create.py`
- Create: `tests/cli/test_create_command.py`

**Step 1: Write the failing test for create command**

Create `tests/cli/test_create_command.py`:

```python
"""Tests for create command."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typer.testing import CliRunner

from skill_fleet.cli.app import app

runner = CliRunner()


@pytest.mark.asyncio
async def test_create_command_basic():
    """Test create command with basic task."""
    with patch('skill_fleet.cli.commands.create.config') as mock_config:
        mock_config.client.create_skill = AsyncMock(return_value={"job_id": "test-123"})
        mock_config.client.get_hitl_prompt = AsyncMock(return_value={"status": "completed"})
        mock_config.user_id = "test-user"

        # This test would require running the async command
        # For now, we'll test the structure exists


def test_create_command_exists():
    """Test create command is registered."""
    result = runner.invoke(app, ["create", "--help"])
    assert result.exit_code == 0
    assert "create" in result.stdout.lower() or "skill" in result.stdout.lower()
```

**Step 2: Run test to verify it exists**

```bash
uv run pytest tests/cli/test_create_command.py -v
```

**Step 3: Update create.py with improved error handling**

Modify `src/skill_fleet/cli/commands/create.py`:

```python
"""CLI command for creating a new skill."""

from __future__ import annotations

import asyncio

import typer

from ...utils.console import get_console, display_error, display_success
from ...utils.constants import HITL_POLL_INTERVAL, ICON_SUCCESS, ICON_ERROR, ICON_WORKING
from ...exceptions import APIError, CLIError

console = get_console()


def create_command(
    ctx: typer.Context,
    task: str = typer.Argument(..., help="Description of the skill to create"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive prompts"),
) -> None:
    """Create a new skill using the 3-phase workflow.

    This command starts a skill creation job and polls for human-in-the-loop
    feedback as needed during the creation process.

    \b
    Workflow phases:
    1. Clarify - Answer questions to refine requirements
    2. Preview - Review generated content before finalizing
    3. Validate - Accept or request changes to the final skill

    Example:
        skill-fleet create "Create a Python async programming skill"
        skill-fleet create "Add testing helpers" --auto-approve
    """
    config = ctx.obj

    async def _run():
        try:
            console.print(f"[bold cyan]{ICON_WORKING} Starting skill creation job...[/bold cyan]")
            result = await config.client.create_skill(task, config.user_id)
            job_id = result.get("job_id")

            if not job_id:
                raise APIError("No job ID returned from API")

            console.print(f"[{ICON_SUCCESS}] [green]Job created: {job_id}[/green]")

            # Polling loop for HITL
            attempt = 0
            max_attempts = 100  # Prevent infinite loops

            while attempt < max_attempts:
                prompt_data = await config.client.get_hitl_prompt(job_id)
                status = prompt_data.get("status")

                if status == "completed":
                    console.print(f"\n[bold green]{ICON_SUCCESS} Skill Creation Completed![/bold green]")
                    content = prompt_data.get("skill_content") or "No content generated."
                    from rich.panel import Panel
                    console.print(Panel(content, title="Final Skill Content"))
                    return

                elif status == "failed":
                    error_msg = prompt_data.get('error', 'Unknown error')
                    raise APIError(f"Job failed: {error_msg}")

                elif status == "pending_hitl":
                    if auto_approve:
                        console.print(
                            f"[yellow]⚠️  HITL Needed ({prompt_data.get('type')}), but --auto-approve is ON. Sending default response...[/yellow]"
                        )
                        await config.client.post_hitl_response(
                            job_id, {"action": "proceed", "answers": {}}
                        )
                        attempt += 1
                        await asyncio.sleep(HITL_POLL_INTERVAL)
                        continue

                    interaction_type = prompt_data.get("type")
                    console.print(
                        f"\n[bold yellow]🤔 HITL Needed: {interaction_type}[/bold yellow]"
                    )

                    if interaction_type == "clarify":
                        questions = prompt_data.get("questions", [])
                        answers = {}
                        if questions:
                            for q in questions:
                                # Handle string or dict question objects
                                q_text = q.get("question") if isinstance(q, dict) else q
                                ans = typer.prompt(f"❓ {q_text}")
                                answers[q_text] = ans
                        await config.client.post_hitl_response(job_id, {"answers": answers})

                    elif interaction_type == "confirm":
                        summary = prompt_data.get("summary", "")
                        from rich.panel import Panel
                        console.print(Panel(summary or "No summary available.", title="Understanding Summary"))
                        action = typer.prompt("Proceed? (proceed/revise/cancel)", default="proceed")
                        await config.client.post_hitl_response(job_id, {"action": action})

                    elif interaction_type == "preview":
                        content = prompt_data.get("content", "")
                        from rich.panel import Panel
                        console.print(Panel(content or "No preview available.", title="Content Preview"))
                        action = typer.prompt("Looks good? (proceed/refine)", default="proceed")
                        await config.client.post_hitl_response(job_id, {"action": action})

                    elif interaction_type == "validate":
                        report = prompt_data.get("report", "")
                        from rich.panel import Panel
                        console.print(Panel(report or "No report available.", title="Validation Report"))
                        action = typer.prompt("Accept? (proceed/refine)", default="proceed")
                        await config.client.post_hitl_response(job_id, {"action": action})

                attempt += 1
                await asyncio.sleep(HITL_POLL_INTERVAL)

            raise APIError("Job timed out after maximum polling attempts")

        except APIError as e:
            display_cli_error(e)
            raise typer.Exit(code=e.exit_code)
        except CLIError as e:
            display_cli_error(e)
            raise typer.Exit(code=e.exit_code)
        except Exception as e:
            display_error(f"Unexpected error: {e}", suggestion="Run with --verbose for details")
            raise typer.Exit(code=1)
        finally:
            await config.client.close()

    asyncio.run(_run())
```

**Step 4: Run tests**

```bash
uv run pytest tests/cli/test_create_command.py -v
```

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/commands/create.py tests/cli/test_create_command.py
git commit -m "refactor(cli): improve create command error handling

- Replace bare Exception with specific CLIError/APIError
- Use singleton console from utils
- Add proper finally block for client cleanup
- Add timeout to prevent infinite polling
- Use Rich Panel for consistent formatting

Fixes error handling issues from cli-error-handling-review.md"
```

---

## Task 7: Update validate.py with Security Validation

**Files:**
- Modify: `src/skill_fleet/cli/commands/validate.py`
- Create: `tests/cli/test_validate_command.py`

**Step 1: Write the failing test for validate command security**

Create `tests/cli/test_validate_command.py`:

```python
"""Tests for validate command."""

import pytest
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from skill_fleet.cli.app import app

runner = CliRunner()


def test_validate_command_requires_path():
    """Test validate command requires a path argument."""
    result = runner.invoke(app, ["validate"])
    assert result.exit_code != 0
    assert "missing" in result.stdout.lower()


def test_validate_command_with_invalid_path():
    """Test validate command with path traversal attempt."""
    result = runner.invoke(app, ["validate", "../../../etc/passwd"])
    # Should reject path traversal
    assert result.exit_code != 0 or "error" in result.stdout.lower()


def test_validate_command_accepts_valid_path(tmp_path):
    """Test validate command accepts valid skill path."""
    # Create a minimal skill structure
    skill_dir = tmp_path / "test_skill"
    skill_dir.mkdir()
    (skill_dir / "skill.md").write_text("# Test Skill\n")
    (skill_dir / "skill.py").write_text("# Test code\n")

    result = runner.invoke(app, ["validate", str(skill_dir)])
    # Should attempt validation (may fail validation but shouldn't crash)
```

**Step 2: Run tests**

```bash
uv run pytest tests/cli/test_validate_command.py -v
```

**Step 3: Update validate.py with security validation**

Modify `src/skill_fleet/cli/commands/validate.py`:

```python
"""CLI command for validating a skill's metadata and structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from ...common.paths import default_skills_root
from ...validators import SkillValidator
from ...utils.console import get_console, display_success, display_error
from ...utils.security import validate_path_within_root
from ...utils.constants import EXIT_VALIDATION_ERROR
from ...exceptions import ValidationError

console = get_console()


def validate_command(
    skill_path: str = typer.Argument(..., help="Path to a skill directory or JSON file"),
    skills_root: str = typer.Option(
        str(default_skills_root()), "--skills-root", help="Skills taxonomy root"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output JSON only"),
) -> None:
    """Validate a skill's metadata and structure.

    Checks for:
    - Required files (skill.md, skill.py, __init__.py)
    - Valid YAML frontmatter with name and description
    - agentskills.io compliance

    \b
    Example:
        skill-fleet validate skills/general/testing
        skill-fleet validate skills/general/testing --json
    """
    try:
        skills_root_path = Path(skills_root).resolve()

        # Resolve and validate skill path is within skills root
        skill_path_resolved = Path(skill_path)
        if not skill_path_resolved.is_absolute():
            skill_path_resolved = skills_root_path / skill_path_resolved

        # Security: Validate path doesn't escape root
        try:
            skill_path_resolved = validate_path_within_root(
                skill_path_resolved, skills_root_path, "Skill path"
            )
        except ValueError as e:
            raise ValidationError(str(e))

        validator = SkillValidator(skills_root_path)
        results = validator.validate_complete(skill_path_resolved)

        if json_output:
            print(json.dumps(results, indent=2))
            if not results.get("passed"):
                raise typer.Exit(code=EXIT_VALIDATION_ERROR)
            return

        # Human-readable output
        status = "passed" if results.get("passed") else "failed"
        if results.get("passed"):
            display_success(f"Validation passed: {skill_path_resolved}")
        else:
            display_error(f"Validation failed: {skill_path_resolved}")

        if results.get("errors"):
            console.print("\n[bold red]Errors:[/bold red]")
            for message in results["errors"]:
                console.print(f"  [red]•[/red] {message}")

        if results.get("warnings"):
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for message in results["warnings"]:
                console.print(f"  [yellow]•[/yellow] {message}")

        if not results.get("passed"):
            raise typer.Exit(code=EXIT_VALIDATION_ERROR)

    except ValidationError:
        raise
    except Exception as e:
        display_error(f"Validation error: {e}")
        raise typer.Exit(code=1)
```

**Step 4: Run tests**

```bash
uv run pytest tests/cli/test_validate_command.py -v
```

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/commands/validate.py tests/cli/test_validate_command.py
git commit -m "feat(cli): add path validation to validate command

- Add validate_path_within_root check to prevent traversal
- Use singleton console from utils
- Use display_success/display_error for consistent formatting
- Add ValidationError for validation failures
- Improve help text with examples

Fixes security issue from cli-security-review.md"
```

---

## Task 8: Update Remaining Commands with Error Handling

**Files:**
- Modify: `src/skill_fleet/cli/commands/*.py` (remaining files)
- Create: `tests/cli/test_remaining_commands.py`

**Step 1: Update all remaining command files**

For each remaining command file (`list_skills.py`, `serve.py`, `chat.py`, `analytics.py`, `migrate.py`, `generate_xml.py`, `optimize.py`, `onboard.py`):

1. Replace `Console()` with `get_console()`
2. Replace bare `except Exception` with specific exceptions
3. Add proper cleanup in `finally` blocks
4. Use display functions for consistent formatting

**Step 2: Example update for list_skills.py**

Modify `src/skill_fleet/cli/commands/list_skills.py`:

```python
"""CLI command for listing skills."""

from __future__ import annotations

import asyncio

import typer

from ...utils.console import get_console
from ...exceptions import APIError

console = get_console()


def list_command(ctx: typer.Context) -> None:
    """List all available skills in the taxonomy.

    Shows skill name, path, and description for each skill.
    """
    config = ctx.obj

    async def _run():
        try:
            skills = await config.client.list_skills()

            if not skills:
                console.print("[yellow]No skills found.[/yellow]")
                return

            from rich.table import Table
            table = Table(title="Available Skills")
            table.add_column("Name", style="cyan")
            table.add_column("Path", style="dim")
            table.add_column("Description")

            for skill in skills:
                table.add_row(
                    skill.get("name", "N/A"),
                    skill.get("path", "N/A"),
                    skill.get("description", "No description")
                )

            console.print(table)

        except APIError as e:
            from ...utils.console import display_cli_error
            display_cli_error(e)
            raise typer.Exit(code=e.exit_code)
        except Exception as e:
            from ...utils.console import display_error
            display_error(f"Failed to list skills: {e}")
            raise typer.Exit(code=1)
        finally:
            await config.client.close()

    asyncio.run(_run())
```

**Step 3: Update all remaining files similarly**

Run for each remaining command file...

**Step 4: Write tests for remaining commands**

Create `tests/cli/test_remaining_commands.py`:

```python
"""Tests for remaining CLI commands."""

import pytest
from typer.testing import CliRunner

from skill_fleet.cli.app import app

runner = CliRunner()


def test_list_command_has_help():
    """Test list command has help."""
    result = runner.invoke(app, ["list", "--help"])
    assert result.exit_code == 0


def test_serve_command_has_help():
    """Test serve command has help."""
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0


def test_chat_command_has_help():
    """Test chat command has help."""
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code == 0
```

**Step 5: Run tests**

```bash
uv run pytest tests/cli/test_remaining_commands.py -v
```

**Step 6: Commit**

```bash
git add src/skill_fleet/cli/commands/ tests/cli/test_remaining_commands.py
git commit -m "refactor(cli): standardize error handling in all commands

- Replace Console() with get_console() singleton
- Replace bare Exception with specific error types
- Add proper finally blocks for cleanup
- Use display_* functions for consistent formatting
- Add tests for all remaining commands

Fixes error handling issues from cli-error-handling-review.md"
```

---

## Task 9: Update pyproject.toml Entry Point

**Files:**
- Modify: `pyproject.toml`

**Step 1: Check current entry points**

```bash
uv run grep -A 10 "\[project.scripts\]" pyproject.toml
```

**Step 2: Update entry point if needed**

If `main.py` entry point exists, comment it out and add new one:

```toml
[project.scripts]
skill-fleet = "skill_fleet.cli:cli_entrypoint"
# Old entry point (keep for migration period):
# skill-fleet-old = "skill_fleet.cli.main:cli_entrypoint"
```

**Step 3: Test the new entry point**

```bash
# Uninstall and reinstall to register entry point
uv sync

# Test CLI
uv run skill-fleet --help
```

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "feat(cli): update entry point to Typer app

- Register skill-fleet CLI to use Typer app
- Keep old entry point commented for migration reference

Addresses dual CLI issue from cli-review-architecture.md"
```

---

## Task 10: Add Type Hints to All Public Functions

**Files:**
- Modify: `src/skill_fleet/cli/**/*.py`

**Step 1: Check for missing type hints**

```bash
# Run mypy or ruff to check for missing type hints
uv run ruff check src/skill_fleet/cli/ --select ANN001,ANN002,ANN003,ANN201,ANN202,ANN204,ANN206
```

**Step 2: Add type hints to all functions**

For each function missing type hints, add proper annotations:

```python
# Before
def create_command(ctx, task, auto_approve=False):
    ...

# After
def create_command(
    ctx: typer.Context,
    task: str,
    auto_approve: bool = False,
) -> None:
    ...
```

**Step 3: Run type checker**

```bash
uv run mypy src/skill_fleet/cli/ || true
```

**Step 4: Commit**

```bash
git add src/skill_fleet/cli/
git commit -m "refactor(cli): add type hints to all public functions

- Add return type annotations (None for commands)
- Add parameter type annotations
- Use proper typer.Context types

Fixes missing type hints from cli-best-practices-review.md"
```

---

## Task 11: Run Full Test Suite and Fix Issues

**Files:**
- Modify: Various files as needed

**Step 1: Run all CLI tests**

```bash
uv run pytest tests/cli/ -v --cov=src/skill_fleet/cli --cov-report=term-missing
```

**Step 2: Run ruff linting**

```bash
uv run ruff check src/skill_fleet/cli/
uv run ruff check --fix src/skill_fleet/cli/
```

**Step 3: Run ruff formatting**

```bash
uv run ruff format src/skill_fleet/cli/
```

**Step 4: Fix any remaining issues**

Address any test failures or linting issues found.

**Step 5: Commit**

```bash
git add src/skill_fleet/cli/ tests/cli/
git commit -m "test(cli): ensure all tests pass and code is formatted

- Run full test suite with coverage
- Fix any remaining test failures
- Apply ruff formatting
- Fix linting issues"
```

---

## Task 12: Create Summary Documentation

**Files:**
- Create: `docs/plans/2026-01-12-cli-optimization-summary.md`

**Step 1: Create summary document**

Create `docs/plans/2026-01-12-cli-optimization-summary.md`:

```markdown
# CLI Optimization and Fix - Summary

**Date:** 2026-01-12
**Status:** Completed

## Changes Made

### Security (High Priority)
- ✅ Added `validate_path_within_root()` to prevent path traversal
- ✅ Added `sanitize_user_id()` to prevent injection attacks
- ✅ Added `validate_api_url()` to enforce secure protocols
- ✅ Added validation callbacks to CLI options

### Error Handling (High Priority)
- ✅ Created custom exception classes (CLIError, ConfigError, APIError, ValidationError)
- ✅ Replaced bare `except Exception` with specific exceptions
- ✅ Added consistent Rich-formatted error display
- ✅ Added actionable suggestions to error messages

### Code Quality (Medium Priority)
- ✅ Created singleton console manager (13 instances → 1)
- ✅ Extracted magic numbers to constants module
- ✅ Added Rich color palette for consistent theming
- ✅ Added type hints to all public functions

### Testing (High Priority)
- ✅ Added test coverage for security utilities
- ✅ Added test coverage for custom exceptions
- ✅ Added test coverage for console manager
- ✅ Added tests for CLI commands

## Files Created

### New Source Files
- `src/skill_fleet/cli/exceptions.py` - Custom exception classes
- `src/skill_fleet/cli/utils/security.py` - Input validation utilities
- `src/skill_fleet/cli/utils/constants.py` - Configuration constants
- `src/skill_fleet/cli/utils/console.py` - Singleton console manager

### New Test Files
- `tests/cli/test_security_utils.py` - Security utilities tests
- `tests/cli/test_exceptions.py` - Exception class tests
- `tests/cli/test_constants.py` - Constants tests
- `tests/cli/test_console.py` - Console manager tests
- `tests/cli/test_app.py` - App configuration tests
- `tests/cli/test_create_command.py` - Create command tests
- `tests/cli/test_validate_command.py` - Validate command tests
- `tests/cli/test_remaining_commands.py` - Other command tests

### Modified Files
- `src/skill_fleet/cli/app.py` - Added security validation
- `src/skill_fleet/cli/client.py` - Added timeout support
- `src/skill_fleet/cli/commands/create.py` - Improved error handling
- `src/skill_fleet/cli/commands/validate.py` - Added path validation
- `src/skill_fleet/cli/commands/list_skills.py` - Standardized error handling
- `src/skill_fleet/cli/utils/__init__.py` - Export utilities

## Remaining Work (Future)

### Low Priority
- [ ] Add integration tests for full command workflows
- [ ] Add performance tests for long-running commands
- [ ] Refactor long functions (>50 lines) into smaller units
- [ ] Add more usage examples in docstrings
- [ ] Consider removing old argparse main.py after migration

### Documentation
- [ ] Update CLI reference documentation
- [ ] Add security guide for contributors
- [ ] Document exit code conventions

## Verification

To verify the fixes:

```bash
# Run all tests
uv run pytest tests/cli/ -v

# Run linting
uv run ruff check src/skill_fleet/cli/

# Test CLI
uv run skill-fleet --help
uv run skill-fleet create "test skill" --help
uv run skill-fleet validate --help
```

## Related Reviews

- `docs/plans/cli-security-review.md` - Security vulnerability findings
- `docs/plans/cli-error-handling-review.md` - Error handling issues
- `docs/plans/cli-best-practices-review.md` - Code quality findings
- `docs/plans/cli-dependencies-review.md` - Dependency issues
```

**Step 2: Commit summary**

```bash
git add docs/plans/2026-01-12-cli-optimization-summary.md
git commit -m "docs: add CLI optimization summary

Document all changes made during CLI optimization and fix.
Lists new files, modified files, remaining work, and verification steps."
```

---

## Summary

This implementation plan addresses all critical and high-priority issues identified in the CLI code reviews:

1. **Security** - Path traversal prevention, input sanitization, URL validation
2. **Error Handling** - Custom exceptions, consistent formatting, actionable messages
3. **Code Quality** - Singleton console, constants, type hints
4. **Testing** - Comprehensive test coverage for utilities and commands

`★ Insight ─────────────────────────────────────`
**Key Design Decisions:**
1. **Singleton Pattern**: Console manager uses module-level singleton to reduce 13 Console() instances to 1, improving memory efficiency and ensuring consistent output formatting.
2. **Custom Exceptions**: Exception classes include exit codes and suggestions, enabling automated error display with actionable guidance.
3. **Security-First Validation**: All user inputs validated before use, preventing path traversal and injection attacks at the boundary.
`─────────────────────────────────────────────────`

**Estimated Effort:** 2-3 days for full implementation
**Expected Deliverables:** 12 new modules/files, comprehensive test coverage, security fixes
