"""CLI command for listing available skills."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console

console = Console()


def list_command(ctx: typer.Context):
    """List all available skills in the taxonomy."""
    config = ctx.obj

    async def _run():
        try:
            skills = await config.client.list_skills()
            if not skills:
                console.print("[yellow]No skills found.[/yellow]")
                return
            for s in skills:
                console.print(
                    f"- [bold]{s.get('name', 'Unknown')}[/bold] ({s.get('skill_id', 'N/A')})"
                )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
        finally:
            await config.client.close()

    asyncio.run(_run())
