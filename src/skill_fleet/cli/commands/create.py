"""CLI command for creating a new skill."""

from __future__ import annotations

import asyncio

import httpx
import typer
from rich.console import Console
from rich.panel import Panel

from ..hitl.runner import run_hitl_job

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
                console.print(f"[red]Could not connect to API server at {config.api_url}[/red]")
                console.print("[yellow]Make sure the server is running:[/yellow]")
                console.print("  uv run skill-fleet serve")
                raise conn_err

            job_id = result.get("job_id")

            console.print(f"[green]✓ Job created: {job_id}[/green]")

            prompt_data = await run_hitl_job(
                console=console,
                client=config.client,
                job_id=job_id,
                auto_approve=auto_approve,
            )

            status = prompt_data.get("status")
            if status == "completed":
                console.print("\n[bold green]✨ Skill Creation Completed![/bold green]")
                saved_path = prompt_data.get("saved_path")
                if saved_path:
                    console.print(f"[bold cyan]📁 Skill saved to:[/bold cyan] {saved_path}")
                content = prompt_data.get("skill_content") or "No content generated."
                console.print(Panel(content, title="Final Skill Content"))
                return

            if status == "failed":
                console.print(f"[red]❌ Job failed: {prompt_data.get('error')}[/red]")
                return

            console.print(f"[yellow]Job ended with status: {status}[/yellow]")
        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error: {e.response.status_code} - {e.response.text}[/red]")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error: {type(e).__name__}: {e}[/red]")
        finally:
            await config.client.close()

    asyncio.run(_run())
