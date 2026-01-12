"""CLI command for interactive chat sessions."""

from __future__ import annotations

import asyncio

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from ...hitl.runner import run_hitl_job

console = Console()


def chat_command(
    ctx: typer.Context,
    task: str | None = typer.Argument(None, help="Optional task to run immediately"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive prompts"),
):
    """Start an interactive guided session to build a skill (job + HITL)."""
    config = ctx.obj

    async def _run():
        try:
            console.print(
                Panel.fit(
                    "[bold cyan]Skill Fleet — Guided Creator[/bold cyan]\n"
                    "This command uses the FastAPI job + HITL workflow.\n"
                    "Commands: /help, /exit",
                    border_style="cyan",
                )
            )

            def _print_help() -> None:
                console.print(
                    Panel.fit(
                        "[bold]Commands[/bold]\n"
                        "- /help: show this message\n"
                        "- /exit: quit\n\n"
                        "[bold]Tips[/bold]\n"
                        "- Use [dim]create[/dim] for one-shot runs: `uv run skill-fleet create \"...\"`\n"
                        "- Run the server first: `uv run skill-fleet serve`",
                        title="Help",
                        border_style="cyan",
                    )
                )

            pending_task: str | None = task
            while True:
                if pending_task is not None:
                    task_description = pending_task
                    pending_task = None
                else:
                    task_description = Prompt.ask(
                        "\n[bold green]What capability would you like to build?[/bold green]"
                    )
                if task_description.lower() in {"/exit", "/quit"}:
                    return
                if task_description.lower() in {"/help"}:
                    _print_help()
                    continue
                if not task_description.strip():
                    continue

                console.print("[dim]Creating job...[/dim]")
                try:
                    result = await config.client.create_skill(task_description, config.user_id)
                except Exception as conn_err:
                    console.print(f"[red]Could not connect to API server at {config.api_url}[/red]")
                    console.print("[yellow]Make sure the server is running:[/yellow]")
                    console.print("  uv run skill-fleet serve")
                    raise conn_err

                job_id = result.get("job_id")
                if not job_id:
                    console.print(f"[red]Unexpected response: {result}[/red]")
                    continue

                console.print(f"[bold green]🚀 Skill creation job started: {job_id}[/bold green]")

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
                elif status == "failed":
                    console.print(f"[red]❌ Job failed: {prompt_data.get('error')}[/red]")
                elif status == "cancelled":
                    console.print("[yellow]Job cancelled.[/yellow]")
                else:
                    console.print(f"[yellow]Job ended with status: {status}[/yellow]")

                # Offer to continue in the same session.
                again = Prompt.ask("Create another skill? (y/n)", choices=["y", "n"], default="n")
                if again == "y":
                    continue
                return

        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error: {e.response.status_code} - {e.response.text}[/red]")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
        except Exception as e:
            console.print(f"[red]Unexpected error: {type(e).__name__}: {e}[/red]")
        finally:
            await config.client.close()

    asyncio.run(_run())
