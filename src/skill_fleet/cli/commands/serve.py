"""CLI command for starting the API server."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def serve_command(
    port: int = typer.Option(8000, "--port", "-p", help="Port to run the API server on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the server to"),
    reload: bool = typer.Option(
        False, "--reload", "-r", help="Enable auto-reload on file changes (dev mode)"
    ),
):
    """Start the Skill Fleet API server."""
    import uvicorn

    if reload:
        console.print("[bold yellow]⚠️  Development mode with auto-reload enabled[/bold yellow]")
        console.print("[dim]Warning: Server restarts will lose in-memory job state[/dim]")
    console.print(f"[bold green]🔥 Starting Skill Fleet API on {host}:{port}...[/bold green]")
    uvicorn.run("skill_fleet.api.app:app", host=host, port=port, reload=reload)
