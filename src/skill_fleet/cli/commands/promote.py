"""CLI command for promoting a draft into the taxonomy."""

from __future__ import annotations

import asyncio

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def promote_command(
    ctx: typer.Context,
    job_id: str = typer.Argument(..., help="Job ID to promote"),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite the existing skill at the intended taxonomy path",
    ),
    delete_draft: bool = typer.Option(
        False,
        "--delete-draft",
        help="Delete the draft directory after successful promotion",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Promote even if workflow validation failed",
    ),
):
    """Promote a completed job's draft into the taxonomy."""
    config = ctx.obj

    async def _run():
        try:
            console.print(Panel.fit(f"[bold cyan]Promoting draft for job[/bold cyan]\n{job_id}"))
            result = await config.client.promote_draft(
                job_id, overwrite=overwrite, delete_draft=delete_draft, force=force
            )
            final_path = result.get("final_path")
            if final_path:
                console.print(f"[bold green]✓ Promoted to:[/bold green] {final_path}")
            else:
                console.print(f"[yellow]Promotion completed:[/yellow] {result}")
        except httpx.HTTPStatusError as e:
            console.print(
                Text(f"HTTP Error: {e.response.status_code} - {e.response.text}", style="red")
            )
        except ValueError as e:
            console.print(Text(f"Error: {e}", style="red"))
        except Exception as e:
            console.print(Text(f"Unexpected error: {type(e).__name__}: {e}", style="red"))
        finally:
            await config.client.close()

    asyncio.run(_run())
