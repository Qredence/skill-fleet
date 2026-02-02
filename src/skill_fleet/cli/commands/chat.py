"""
CLI command for interactive chat sessions.

Features:
- Real-time streaming with live updates and AI reasoning display
- Hybrid mode: streaming for progress, polling for HITL interactions
- Arrow key navigation for multi-choice questions
- Interactive terminal-based workflow
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from ..hitl.runner import run_hitl_job
from ..streaming_runner import run_hybrid_job

console = Console()
logger = logging.getLogger(__name__)


def chat_command(
    ctx: typer.Context,
    task: str | None = typer.Argument(None, help="Optional task to run immediately"),
    auto_approve: bool = typer.Option(False, "--auto-approve", help="Skip interactive prompts"),
    show_thinking: bool = typer.Option(
        True,
        "--show-thinking/--no-show-thinking",
        help="Show rationale/thinking panels when available",
    ),
    force_plain_text: bool = typer.Option(
        False,
        "--force-plain-text",
        help="Disable arrow-key dialogs and use plain-text prompts",
    ),
    fast: bool = typer.Option(
        True,
        "--fast/--slow",
        help="Use fast polling (100ms) for real-time updates",
    ),
    stream: bool = typer.Option(
        True,
        "--stream/--poll",
        help="Use streaming mode with live progress (default) or polling-only mode",
    ),
):
    """
    Start an interactive guided session to build a skill (job + HITL).

    Features real-time streaming with:
    - Live progress updates with phase transitions
    - AI reasoning/thinking display as it happens
    - Arrow key navigation for questions
    - Immediate response to user input

    Use --stream (default) for live progress display, or --poll for
    compatibility mode that only polls for HITL prompts.
    """
    config = ctx.obj

    async def _run():
        try:
            mode_label = "streaming" if stream else "polling"
            console.print(
                Panel.fit(
                    "[bold cyan]Skill Fleet — Interactive Creator[/bold cyan]\n"
                    f"Mode: {mode_label} with live thinking display\n"
                    "Commands: /help, /exit",
                    border_style="cyan",
                )
            )

            def _print_help():
                console.print(
                    Panel.fit(
                        "[bold]Commands[/bold]\n"
                        "- /help: show this message\n"
                        "- /exit: quit\n\n"
                        "[bold]Features[/bold]\n"
                        "- Real-time progress updates (100ms)\n"
                        "- Live thinking/reasoning display\n"
                        "- Arrow key navigation for choices\n"
                        "- Immediate response to questions",
                        title="Help",
                        border_style="cyan",
                    )
                )

            pending_task = task
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

                # Use fast polling for real-time updates
                poll_interval = 0.1 if fast else 2.0
                job_id: str | None = None

                if stream:
                    # Streaming mode: live progress + HITL handling
                    prompt_data = await run_hybrid_job(
                        console=console,
                        client=config.client,
                        task_description=task_description,
                        user_id=config.user_id,
                        show_thinking=show_thinking,
                        force_plain_text=force_plain_text,
                        poll_interval=poll_interval,
                    )
                else:
                    # Polling mode: create job first, then poll
                    with console.status("[bold green]Creating job...[/bold green]") as status:
                        try:
                            result = await config.client.create_skill(
                                task_description, config.user_id
                            )
                            job_id = result.get("job_id")
                            status.update(
                                f"[bold green]🚀 Skill creation job started: {job_id}[/bold green]"
                            )
                        except Exception as conn_err:
                            console.print(
                                f"[red]Could not connect to API server at {config.api_url}[/red]"
                            )
                            console.print("[yellow]Make sure the server is running:[/yellow]")
                            console.print("  uv run skill-fleet serve")
                            raise conn_err

                    if not job_id:
                        console.print(f"[red]Unexpected response: {result}[/red]")
                        continue

                    console.print(
                        f"[bold green]🚀 Skill creation job started: {job_id}[/bold green]"
                    )

                    prompt_data = await run_hitl_job(
                        console=console,
                        client=config.client,
                        job_id=job_id,
                        auto_approve=auto_approve,
                        show_thinking=show_thinking,
                        force_plain_text=force_plain_text,
                        poll_interval=poll_interval,
                    )

                status = prompt_data.get("status")
                if status == "completed":
                    validation_passed = prompt_data.get("validation_passed")
                    if validation_passed is False:
                        console.print(
                            "\n[bold yellow]✨ Skill Creation Completed (validation failed)[/bold yellow]"
                        )
                    else:
                        console.print("\n[bold green]✨ Skill Creation Completed![/bold green]")

                    intended = prompt_data.get("intended_taxonomy_path") or prompt_data.get("path")
                    if intended:
                        console.print(f"[dim]Intended path:[/dim] {intended}")

                    final_path = prompt_data.get("final_path") or prompt_data.get("saved_path")
                    draft_path = prompt_data.get("draft_path")

                    if final_path:
                        console.print(f"[bold cyan]📁 Skill saved to:[/bold cyan] {final_path}")
                    elif draft_path:
                        console.print(f"[bold cyan]📝 Draft saved to:[/bold cyan] {draft_path}")
                        if job_id:
                            console.print(
                                f"[dim]Promote when ready:[/dim] `uv run skill-fleet promote {job_id}`"
                            )

                    validation_score = prompt_data.get("validation_score")
                    if validation_passed is not None:
                        status_label = "PASS" if validation_passed else "FAIL"
                        score_suffix = (
                            f" (score: {validation_score})" if validation_score is not None else ""
                        )
                        style = "green" if validation_passed else "yellow"
                        console.print(
                            f"[{style}]Validation: {status_label}{score_suffix}[/{style}]"
                        )

                    # Display the on-disk artifact when possible (draft or final).
                    content: str | None = None
                    for base in (final_path, draft_path):
                        if not base:
                            continue
                        skill_md = Path(str(base)) / "SKILL.md"
                        if skill_md.exists():
                            content = skill_md.read_text(encoding="utf-8")
                            break
                    if content is None:
                        content = prompt_data.get("skill_content") or "No content generated."

                    console.print(Panel(content, title="Final Skill Content"))

                elif status == "failed":
                    console.print(Text(f"❌ Job failed: {prompt_data.get('error')}", style="red"))
                elif status == "cancelled":
                    console.print(Text("Job cancelled.", style="yellow"))
                else:
                    console.print(Text(f"Job ended with status: {status}", style="yellow"))

                # Offer to continue in the same session.
                again = Prompt.ask("Create another skill? (y/n)", choices=["y", "n"], default="n")
                if again == "y":
                    continue
                return

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
