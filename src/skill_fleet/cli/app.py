"""Main Typer CLI application for Skill Fleet.

Follows Typer/Click best practices for context management and global options.
Ref: https://typer.tiangolo.com/tutorial/commands/context/
     https://typer.tiangolo.com/tutorial/one-file-per-command/
"""

from __future__ import annotations

import typer
from rich.console import Console

from .client import SkillFleetClient
from .commands.analytics import analytics_command
from .commands.chat import chat_command
from .commands.create import create_command
from .commands.evaluate import evaluate_batch_command, evaluate_command
from .commands.generate_xml import generate_xml_command
from .commands.list_skills import list_command
from .commands.migrate import migrate_command
from .commands.onboard import onboard_command
from .commands.optimize import optimize_command
from .commands.promote import promote_command
from .commands.serve import serve_command
from .commands.validate import validate_command

# Initialize Typer app
app = typer.Typer(
    name="skill-fleet",
    help="Skills Fleet - Interactive mode",
    add_completion=False,
)

console = Console()


class CLIConfig:
    """Container for CLI configuration and shared state."""

    def __init__(self, api_url: str, user_id: str):
        self.api_url = api_url
        self.user_id = user_id
        self.client = SkillFleetClient(base_url=api_url)


@app.callback()
def main_callback(
    ctx: typer.Context,
    api_url: str = typer.Option(
        "http://localhost:8000",
        "--api-url",
        "-a",
        help="API server URL",
        envvar="SKILL_FLEET_API_URL",
    ),
    user_id: str = typer.Option(
        "default", "--user", "-u", help="User ID for context", envvar="SKILL_FLEET_USER_ID"
    ),
):
    """
    Global configuration for Skill Fleet CLI.
    """
    # Store config object in Click context
    ctx.obj = CLIConfig(api_url=api_url, user_id=user_id)


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
app.command(name="promote")(promote_command)
app.command(name="evaluate")(evaluate_command)
app.command(name="evaluate-batch")(evaluate_batch_command)

if __name__ == "__main__":
    app()
