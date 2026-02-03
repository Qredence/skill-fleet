"""CLI command for creating a new skill."""

from __future__ import annotations

import asyncio

import httpx
import typer
from rich.console import Console
from rich.text import Text

from ..hitl.runner import run_hitl_job
from ..ui.completion import display_completion_result, display_connection_error

console = Console()


def create_command(
    ctx: typer.Context,
    task: str = typer.Argument(..., help="Description of the skill to create"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive prompts"),
):
    """Create a new skill using the 3-phase workflow."""
    config = ctx.obj

    async def _run():
        try:
            console.print("[bold cyan]🚀 Starting skill creation job...[/bold cyan]")
            try:
                result = await config.client.create_skill(task, config.user_id)
            except Exception as conn_err:
                display_connection_error(console, config.api_url)
                raise conn_err

            job_id = result.get("job_id")

            console.print(f"[green]✓ Job created: {job_id}[/green]")

            prompt_data = await run_hitl_job(
                console=console,
                client=config.client,
                job_id=job_id,
                auto_approve=auto_approve,
            )

            # Display completion results
            display_completion_result(console, prompt_data, show_content_panel=True)
            return
        except httpx.HTTPStatusError as e:
            error_text = ""
            try:
                error_text = e.response.text
            except Exception:
                error_text = "(unable to read response)"
            console.print(Text(f"HTTP Error: {e.response.status_code} - {error_text}", style="red"))
        except ValueError as e:
            console.print(Text(f"Error: {e}", style="red"))
        except Exception as e:
            console.print(Text(f"Unexpected error: {type(e).__name__}: {e}", style="red"))
        finally:
            await config.client.close()

    asyncio.run(_run())
