"""
Main Typer CLI application for Skill Fleet.

Follows Typer/Click best practices for context management and global options.
Ref: https://typer.tiangolo.com/tutorial/commands/context/
     https://typer.tiangolo.com/tutorial/one-file-per-command/
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import typer
from rich.console import Console

from .client import SkillFleetClient
from .commands.analytics import analytics_command
from .commands.chat import chat_command
from .commands.create import create_command
from .commands.db import db_app
from .commands.dev import dev_command
from .commands.generate_xml import generate_xml_command
from .commands.list_skills import list_command
from .commands.migrate import migrate_command
from .commands.promote import promote_command
from .commands.serve import serve_command
from .commands.terminal import terminal_command
from .commands.tui import tui_command
from .commands.validate import validate_command
from .utils.security import sanitize_user_id, validate_api_url

# Initialize Typer app
app = typer.Typer(
    name="skill-fleet",
    help="Skills Fleet - Hierarchical skills taxonomy + DSPy workflow CLI",
    add_completion=True,
    no_args_is_help=True,
)

console = Console()


def _print_version_and_exit() -> None:
    try:
        package_version = version("skill-fleet")
    except PackageNotFoundError:
        package_version = "unknown"

    console.print(package_version)
    raise typer.Exit(0)


def _version_callback(value: bool) -> bool:
    if value:
        _print_version_and_exit()
    return value


class CLIConfig:
    """
    Container for CLI configuration and shared state.

    Attributes:
        api_url: The API server URL for backend communication
        user_id: The user ID for context and analytics
        client: HTTP client for API requests

    """

    def __init__(self, api_url: str, user_id: str):
        """
        Initialize CLI configuration.

        Args:
            api_url: The API server URL
            user_id: The user identifier

        """
        self.api_url = api_url
        self.user_id = user_id
        self.client = SkillFleetClient(base_url=api_url, user_id=user_id)


@app.callback()
def main_callback(
    ctx: typer.Context,
    _show_version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        is_eager=True,
        callback=_version_callback,
    ),
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        "-a",
        help="API server URL (default: http://localhost:8000)",
        envvar="SKILL_FLEET_API_URL",
    ),
    user_id: str = typer.Option(
        "default",
        "--user",
        "-u",
        help="User ID for context and analytics (default: default)",
        envvar="SKILL_FLEET_USER_ID",
    ),
):
    r"""
    Skill Fleet CLI - Hierarchical skills taxonomy + DSPy workflow management.

    This CLI provides a comprehensive interface for managing AI agent skills,
    including creation, validation, optimization, and deployment capabilities.

    \b
    Common workflows:
      - Create skills: uv run skill-fleet create "Your task description"
      - Start server: uv run skill-fleet serve
      - Validate skills: uv run skill-fleet validate <skill-path>
      - Interactive mode: uv run skill-fleet chat

    \b
    Global options:
      --api-url/-a: Set the API server URL
      --user/-u: Set the user ID for context

    \b
    Environment variables:
      SKILL_FLEET_API_URL: Default API server URL
      SKILL_FLEET_USER_ID: Default user ID
    """
    # Validate and sanitize inputs
    try:
        validated_api_url = validate_api_url(api_url)
        sanitized_user_id = sanitize_user_id(user_id)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", style="bold red")
        raise typer.Exit(1) from e

    # Store config object in Click context
    ctx.obj = CLIConfig(api_url=validated_api_url, user_id=sanitized_user_id)


# Register commands from separate files
app.command(name="create")(create_command)
app.command(name="list")(list_command)
app.command(name="serve")(serve_command)
app.command(name="dev")(dev_command)
app.command(name="chat")(chat_command)
app.command(name="terminal")(terminal_command)
app.command(name="tui")(tui_command)
app.command(name="validate")(validate_command)
app.command(name="analytics")(analytics_command)
app.command(name="migrate")(migrate_command)
app.command(name="generate-xml")(generate_xml_command)
app.command(name="promote")(promote_command)

# Register database command group
app.add_typer(db_app, name="db")

if __name__ == "__main__":
    app()
