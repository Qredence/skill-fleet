"""CLI command for starting the API server."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel

from ..ui.prompts import get_default_ui

console = Console()


async def _ask_server_config(
    port: int,
    host: str,
    reload: bool,
    auto_accept: bool,
    force_plain_text: bool,
) -> tuple[int, str, bool]:
    """Ask clarifying questions about server configuration.

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
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the API server on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the server to"),
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
    """Start the Skill Fleet API server.

    Interactively asks for configuration (port, host, reload mode) unless
    --auto-accept is specified.
    
    Automatically initializes the database on startup unless --skip-db-init
    is specified.
    """
    import uvicorn

    from skill_fleet.db.database import init_db

    # Initialize database unless skipped
    if not skip_db_init:
        try:
            console.print("[dim]Initializing database...[/dim]")
            init_db()
            console.print("[dim]✅ Database initialized[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Database initialization failed: {e}[/red]")
            raise typer.Exit(1)

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
    uvicorn.run("skill_fleet.api.app:app", host=final_host, port=final_port, reload=final_reload)
