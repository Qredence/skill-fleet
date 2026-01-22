"""
CLI command for interactive chat sessions.

Features:
- Connects to the streaming chat API
- Displays real-time thinking and reasoning
- Manages persistent session via API
- Rich interactive prompts using questionary for navigation and selection
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

import httpx
import typer
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from rich.table import Table
from rich.progress_bar import ProgressBar

console = Console()
logger = logging.getLogger(__name__)

# Map conversation states to progress (0.0 to 1.0) and label
PROGRESS_MAP = {
    "EXPLORING": ("Understanding", 0.1),
    "DEEP_UNDERSTANDING": ("Deep Dive", 0.2),
    "MULTI_SKILL_DETECTED": ("Scoping", 0.25),
    "CONFIRMING": ("Confirmation", 0.3),
    "CREATING": ("Generating", 0.4),
    "TDD_RED_PHASE": ("TDD (Red)", 0.5),
    "TDD_GREEN_PHASE": ("TDD (Green)", 0.65),
    "TDD_REFACTOR_PHASE": ("TDD (Refactor)", 0.8),
    "REVIEWING": ("Review", 0.9),
    "REVISING": ("Revising", 0.95),
    "CHECKLIST_COMPLETE": ("Finalizing", 0.98),
    "COMPLETE": ("Done", 1.0),
}


def _render_progress(state: str) -> None:
    """Render a progress header based on current state."""
    label, percent = PROGRESS_MAP.get(state, ("Working", 0.5))

    # Create a compact progress bar
    bar = ProgressBar(
        total=100, completed=percent * 100, width=30, complete_style="green", finished_style="green"
    )

    # Create a grid or table for the header
    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    grid.add_row(f"[bold cyan]Phase:[/bold cyan] {label}", bar)

    console.print(Panel(grid, border_style="dim", padding=(0, 1)))


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
    no_tui: bool = typer.Option(
        False,
        "--no-tui",
        help="Disable Ink TUI and use simple terminal chat",
    ),
):
    """
    Start an interactive guided session to build a skill.
    """
    config = ctx.obj

    async def _run():
        try:
            console.print(
                Panel.fit(
                    "[bold cyan]Skill Fleet — Guided Creator[/bold cyan]\n"
                    "This command uses the streaming API.\n"
                    "Commands: /exit, /quit",
                    border_style="cyan",
                )
            )

            # Create a session ID for this CLI run
            session_id = f"cli_{uuid4().hex[:8]}"
            next_input: str | None = task
            current_state: str = "EXPLORING"

            # Main conversation loop
            while True:
                # 1. Determine input (User prompt or auto-advance)
                if next_input is not None:
                    user_input = next_input
                    next_input = None
                    # Only print if it's a user task, not an internal "continue" signal
                    if user_input != "continue":
                        console.print(f"\n[bold green]Task:[/bold green] {user_input}")
                else:
                    user_input = Prompt.ask("\n[bold green]You[/bold green]")

                if user_input.lower() in {"/exit", "/quit"}:
                    return

                if not user_input.strip():
                    continue

                console.print()

                # State for streaming display
                thinking_text = Text()
                response_data = None

                # Live display for thinking
                with Live(
                    Panel(thinking_text, title="[dim]Thinking...[/dim]", border_style="dim"),
                    console=console,
                    refresh_per_second=10,
                    transient=True,  # Disappear after done
                ) as live:
                    try:
                        async for event in config.client.stream_chat(user_input, session_id):
                            event_type = event.get("type")
                            data = event.get("data")

                            if event_type == "thinking":
                                content = data.get("content", "")
                                thinking_text.append(content, style="dim italic")
                                live.update(
                                    Panel(
                                        thinking_text,
                                        title="[dim]Thinking...[/dim]",
                                        border_style="dim",
                                    )
                                )

                            elif event_type == "response":
                                response_data = data
                                if response_data.get("state"):
                                    current_state = response_data.get("state")

                            elif event_type == "error":
                                console.print(f"[red]Server Error: {data.get('error')}[/red]")
                                break

                            elif event_type == "complete":
                                break

                    except httpx.HTTPStatusError as e:
                        console.print(
                            f"[red]API Error: {e.response.status_code} - {e.response.text}[/red]"
                        )
                        console.print(
                            "[yellow]Make sure 'uv run skill-fleet serve' is running.[/yellow]"
                        )
                        return
                    except Exception as e:
                        console.print(f"[red]Connection Error: {e}[/red]")
                        return

                # Display final response and handle interactions
                if response_data:
                    # Render progress header
                    _render_progress(current_state)

                    message = response_data.get("message", "")

                    # Show thinking summary if requested (optional persistent log)
                    if show_thinking and thinking_text and not message:
                        pass

                    # Format message
                    console.print("[cyan]Agent:[/cyan]")
                    if message:
                        console.print(Markdown(message))

                    # ---------------------------------------------------------
                    # Interactive Options Handling
                    # ---------------------------------------------------------
                    action = response_data.get("action")
                    data = response_data.get("data", {})
                    requires_input = response_data.get("requires_user_input", True)

                    # Determine next step
                    if not requires_input:
                        # Auto-advance
                        console.print("[dim]Proceeding automatically...[/dim]")
                        next_input = "continue"

                    elif action in ["ask_question", "ask_understanding_question"]:
                        # Extract options
                        options = []
                        allow_multiple = False

                        # Structure A: Flat (ask_question)
                        if "question_options" in data:
                            raw_opts = data["question_options"]
                            # Convert string list to objects if needed
                            options = [
                                {"id": str(i), "label": opt, "description": ""}
                                if isinstance(opt, str)
                                else opt
                                for i, opt in enumerate(raw_opts, 1)
                            ]

                        # Structure B: Nested (ask_understanding_question)
                        elif "question" in data and isinstance(data["question"], dict):
                            q_obj = data["question"]
                            if "options" in q_obj:
                                options = q_obj["options"]
                                allow_multiple = q_obj.get("allows_multiple", True)

                        # Render options if found
                        if options:
                            # 1. Show Detailed Table (because questionary cuts off long text)
                            table = Table(show_header=True, header_style="bold magenta", box=None)
                            table.add_column("Option", style="bold")
                            table.add_column("Description", style="dim")

                            choices = []
                            for opt in options:
                                label = opt.get("label", opt.get("text", str(opt)))
                                desc = opt.get("description", "")
                                table.add_row(label, desc)
                                # Use label as the value to send back to LLM
                                choices.append(questionary.Choice(title=label, value=label))

                            console.print(table)
                            console.print()  # Spacer

                            # Add "Custom" option
                            choices.append(
                                questionary.Choice(
                                    title="Type custom answer...", value="__custom__"
                                )
                            )

                            # 2. Interactive Selection using Questionary
                            current_selection = []
                            while True:
                                if allow_multiple:
                                    answer = await questionary.checkbox(
                                        "Select option(s):",
                                        choices=choices,
                                        default=current_selection if current_selection else None,  # type: ignore
                                        instruction="(Space to toggle, Enter to submit)",
                                        style=questionary.Style(
                                            [
                                                ("qmark", "fg:#00ffff bold"),
                                                ("question", "bold"),
                                                ("answer", "fg:#00ff00 bold"),
                                                ("pointer", "fg:#00ffff bold"),
                                                ("highlighted", "fg:#00ffff bold"),
                                                ("selected", "fg:#00ff00"),
                                                ("separator", "fg:#cc5454"),
                                                ("instruction", "fg:#858585 italic"),
                                                ("text", ""),
                                                ("disabled", "fg:#858585 italic"),
                                            ]
                                        ),
                                    ).ask_async()
                                else:
                                    answer = await questionary.select(
                                        "Select option:",
                                        choices=choices,
                                        style=questionary.Style(
                                            [
                                                ("qmark", "fg:#00ffff bold"),
                                                ("question", "bold"),
                                                ("answer", "fg:#00ff00 bold"),
                                                ("pointer", "fg:#00ffff bold"),
                                                ("highlighted", "fg:#00ffff bold"),
                                                ("selected", "fg:#00ff00"),
                                            ]
                                        ),
                                    ).ask_async()

                                # Handle selection
                                if answer is None:
                                    return  # User cancelled

                                if answer == "__custom__":
                                    # Fall through to Prompt.ask
                                    break

                                if isinstance(answer, list):
                                    if "__custom__" in answer:
                                        # Mixed custom + selection -> break to prompt
                                        break

                                    if not answer:
                                        console.print(
                                            "[yellow]Please select at least one option (press Space) or type a custom answer.[/yellow]"
                                        )
                                        current_selection = []
                                        continue

                                    next_input = ", ".join(answer)
                                    break

                                # Single selection string
                                next_input = answer
                                break

                    # Check for completion
                    if action == "complete":
                        console.print("\n[bold green]✨ Session Complete[/bold green]")
                        if Prompt.ask("Start another skill? (y/n)", default="n") == "y":
                            session_id = f"cli_{uuid4().hex[:8]}"
                            console.print("[dim]Started new session[/dim]")
                            next_input = None
                            current_state = "EXPLORING"
                        else:
                            return

        except Exception as e:
            console.print(f"[red]Unexpected error: {type(e).__name__}: {e}[/red]")
        finally:
            await config.client.close()

    asyncio.run(_run())
