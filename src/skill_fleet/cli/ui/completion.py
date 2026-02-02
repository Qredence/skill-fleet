"""Shared utilities for displaying job completion results."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def display_completion_result(
    console: Console,
    prompt_data: dict,
    *,
    show_content_panel: bool = True,
) -> None:
    """
    Display job completion results in a consistent format.

    Args:
        console: Rich console for output
        prompt_data: Dictionary containing job completion data with keys:
            - status: Job status (completed, failed, etc.)
            - validation_passed: Boolean indicating validation result
            - validation_score: Numeric validation score
            - intended_taxonomy_path: Intended skill location
            - final_path: Final saved path
            - draft_path: Draft location
            - skill_content: Generated skill content
            - error: Error message if failed
        show_content_panel: Whether to display the final content panel

    """
    status = prompt_data.get("status")

    if status == "completed":
        validation_passed = prompt_data.get("validation_passed")
        if validation_passed is False:
            console.print(
                "\n[bold yellow]✨ Skill Creation Completed (validation failed)[/bold yellow]"
            )
        else:
            console.print("\n[bold green]✨ Skill Creation Completed![/bold green]")

        # Show intended path
        intended = prompt_data.get("intended_taxonomy_path") or prompt_data.get("path")
        if intended:
            console.print(f"[dim]Intended path:[/dim] {intended}")

        # Show saved location
        final_path = prompt_data.get("final_path") or prompt_data.get("saved_path")
        draft_path = prompt_data.get("draft_path")
        if final_path:
            console.print(f"[bold cyan]📁 Skill saved to:[/bold cyan] {final_path}")
        elif draft_path:
            console.print(f"[bold cyan]📝 Draft saved to:[/bold cyan] {draft_path}")
            job_id = prompt_data.get("job_id")
            if job_id:
                console.print(
                    f"[dim]Promote when ready:[/dim] `uv run skill-fleet promote {job_id}`"
                )

        # Show validation status
        validation_score = prompt_data.get("validation_score")
        if validation_passed is not None:
            status_label = "PASS" if validation_passed else "FAIL"
            score_suffix = f" (score: {validation_score})" if validation_score is not None else ""
            style = "green" if validation_passed else "yellow"
            console.print(f"[{style}]Validation: {status_label}{score_suffix}[/{style}]")

        # Display content panel
        if show_content_panel:
            content = _read_skill_content(final_path, draft_path, prompt_data)
            console.print(Panel(Text(content), title="Final Skill Content"))

    elif status == "failed":
        error_msg = prompt_data.get("error", "Unknown error")
        console.print(Text(f"❌ Job failed: {error_msg}", style="red"))

    else:
        console.print(Text(f"Job ended with status: {status}", style="yellow"))


def display_connection_error(console: Console, api_url: str) -> None:
    """
    Display a consistent error message for API connection failures.

    Args:
        console: Rich console for output
        api_url: The API URL that failed to connect

    """
    console.print(f"[red]Could not connect to API server at {api_url}[/red]")
    console.print("[yellow]Make sure the server is running:[/yellow]")
    console.print("  uv run skill-fleet serve")


def _read_skill_content(
    final_path: str | None,
    draft_path: str | None,
    prompt_data: dict,
) -> str:
    """
    Attempt to read skill content from disk or fallback to prompt_data.

    Args:
        final_path: Final skill location
        draft_path: Draft skill location
        prompt_data: Job data containing fallback content

    Returns:
        Skill content string

    """
    for base in (final_path, draft_path):
        if not base:
            continue
        skill_md = Path(str(base)) / "SKILL.md"
        if skill_md.exists():
            return skill_md.read_text(encoding="utf-8")

    return prompt_data.get("skill_content") or "No content generated."
