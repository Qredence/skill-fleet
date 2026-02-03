"""CLI command for starting the API server."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

from ..ui.prompts import get_default_ui

console = Console()


def validate_port(port: int) -> int:
    """
    Validate that port is in valid range (1-65535).

    Args:
        port: Port number to validate

    Returns:
        Validated port number

    Raises:
        typer.BadParameter: If port is out of range
    """
    if not (1 <= port <= 65535):
        raise typer.BadParameter(f"Port must be between 1 and 65535, got {port}")
    return port


def validate_host(host: str) -> str:
    """
    Validate that host is a valid hostname or IP address.

    Args:
        host: Host string to validate

    Returns:
        Validated host string

    Raises:
        typer.BadParameter: If host is empty or contains invalid characters
    """
    if not host or not host.strip():
        raise typer.BadParameter("Host cannot be empty")
    # Basic validation for host format
    import re

    if not re.match(r"^[a-zA-Z0-9.:-]+$", host):
        raise typer.BadParameter(f"Invalid host format: {host}")
    return host


async def _ask_server_config(
    port: int,
    host: str,
    reload: bool,
    auto_accept: bool,
    force_plain_text: bool,
) -> tuple[int, str, bool]:
    """
    Ask clarifying questions about server configuration.

    Returns:
        (port, host, reload)
    """
    if auto_accept:
        return (port, host, reload)

    console.print(
        Panel.fit(
            "[bold cyan]Skill Fleet API Server[/bold cyan]\n"
            "Configure your server settings (or press Enter for defaults)",
            border_style="cyan",
        )
    )

    ui = get_default_ui(force_plain_text=force_plain_text)

    # Ask about port
    port_input = await ui.ask_text(
        f"[bold]Port[/bold] (default: {port})",
        default=str(port),
    )
    try:
        port = int(port_input)
        # Validate port range (1-65535)
        if not (1 <= port <= 65535):
            console.print(f"[yellow]Port must be between 1-65535, using default {port}[/yellow]")
            port = 8000
    except ValueError:
        console.print(f"[yellow]Invalid port '{port_input}', using default {port}[/yellow]")

    # Ask about host
    host = await ui.ask_text(
        f"[bold]Host[/bold] (default: {host})",
        default=host,
    )

    # Ask about reload mode
    reload_choice = await ui.choose_one(
        "[bold]Development mode[/bold] (auto-reload on file changes)?",
        choices=[
            ("no", "❌ No (production)"),
            ("yes", "🔄 Yes (development)"),
        ],
        default_id="no" if not reload else "yes",
    )
    reload = reload_choice == "yes"

    # Summary
    console.print("\n[dim]Configuration:[/dim]")
    console.print(f"  Host: [cyan]{host}[/cyan]")
    console.print(f"  Port: [cyan]{port}[/cyan]")
    console.print(f"  Reload: [cyan]{'Yes' if reload else 'No'}[/cyan]\n")

    return (port, host, reload)


def serve_command(
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to run the API server on",
        callback=validate_port,
    ),
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        help="Host to bind the server to",
        callback=validate_host,
    ),
    reload: bool = typer.Option(
        False, "--reload", "-r", help="Enable auto-reload on file changes (dev mode)"
    ),
    auto_accept: bool = typer.Option(
        False,
        "--auto-accept",
        help="Skip interactive prompts and use provided options (or defaults)",
    ),
    force_plain_text: bool = typer.Option(
        False,
        "--force-plain-text",
        help="Disable arrow-key dialogs and use plain-text prompts",
    ),
    skip_db_init: bool = typer.Option(
        False,
        "--skip-db-init",
        help="Skip database initialization (assumes DB already initialized)",
    ),
):
    """
    Start the Skill Fleet API server.

    Interactively asks for configuration (port, host, reload mode) unless
    --auto-accept is specified.

    Automatically initializes the database on startup unless --skip-db-init
    is specified.
    """
    import uvicorn

    from skill_fleet.infrastructure.db.database import init_db

    # Initialize database unless skipped
    if not skip_db_init:
        with console.status("[bold green]Initializing database...[/bold green]") as status:
            try:
                init_db()
                status.update("[bold green]✅ Database initialized[/bold green]")
                console.print("[dim]✅ Database initialized[/dim]")
            except Exception as e:
                console.print(f"[red]❌ Database initialization failed: {e}[/red]")
                raise typer.Exit(1) from e

    # Ask for configuration
    final_port, final_host, final_reload = asyncio.run(
        _ask_server_config(port, host, reload, auto_accept, force_plain_text)
    )

    if final_reload:
        console.print("[bold yellow]⚠️  Development mode with auto-reload enabled[/bold yellow]")
        console.print("[dim]Job state now persists across server restarts (via SQLite)[/dim]")

    console.print(
        f"[bold green]🔥 Starting Skill Fleet API on {final_host}:{final_port}...[/bold green]"
    )
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    uvicorn.run("skill_fleet.api.main:app", host=final_host, port=final_port, reload=final_reload)
