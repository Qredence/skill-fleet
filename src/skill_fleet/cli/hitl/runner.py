"""Shared HITL job runner for CLI commands.

The Skill Fleet API uses a background job + HITL (Human-in-the-Loop) prompt model:
- CLI starts a job via `/api/v2/skills/create`
- API exposes the current prompt via `/api/v2/hitl/{job_id}/prompt`
- CLI responds via `/api/v2/hitl/{job_id}/response`

This module centralizes the polling + interaction handling so `create` and `chat`
commands stay consistent.
"""

from __future__ import annotations

import asyncio
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

try:
    from ..utils.constants import HITL_POLL_INTERVAL
except (ImportError, AttributeError):
    # Fallback default if the shared constants module is unavailable.
    # This keeps the HITL runner functional in environments where
    # `skill_fleet.cli.utils.constants` does not define HITL_POLL_INTERVAL.
    HITL_POLL_INTERVAL: float = 2.0


def _render_questions(questions: object) -> str:
    if isinstance(questions, str):
        return questions
    if isinstance(questions, list):
        lines: list[str] = []
        for idx, q in enumerate(questions, 1):
            if isinstance(q, dict):
                text = q.get("question") or q.get("text") or str(q)
            else:
                text = str(q)
            lines.append(f"{idx}. {text}")
        return "\n".join(lines)
    return str(questions or "")


async def run_hitl_job(
    *,
    console: Console,
    client: Any,
    job_id: str,
    auto_approve: bool = False,
    poll_interval: float = HITL_POLL_INTERVAL,
) -> dict[str, Any]:
    """Poll and satisfy HITL prompts until the job reaches a terminal state.

    Returns the final prompt payload from the API (status + result fields).
    """
    while True:
        prompt_data = await client.get_hitl_prompt(job_id)
        status = prompt_data.get("status")

        if status in {"completed", "failed", "cancelled"}:
            return prompt_data

        if status != "pending_hitl":
            await asyncio.sleep(poll_interval)
            continue

        interaction_type = prompt_data.get("type")

        if auto_approve:
            if interaction_type == "clarify":
                await client.post_hitl_response(job_id, {"answers": {"response": ""}})
            else:
                await client.post_hitl_response(job_id, {"action": "proceed"})
            continue

        if interaction_type == "clarify":
            questions = _render_questions(prompt_data.get("questions"))
            rationale = prompt_data.get("rationale", "")
            if rationale:
                console.print(
                    Panel(
                        Markdown(rationale) if "**" in rationale else rationale,
                        title="[dim]Why I'm asking[/dim]",
                        border_style="dim",
                    )
                )
            console.print(
                Panel(
                    Markdown(questions) if questions else "No questions available.",
                    title="[bold yellow]🤔 Clarification Needed[/bold yellow]",
                    border_style="yellow",
                )
            )
            answers = Prompt.ask("[bold green]Your answers[/bold green] (or /cancel)", default="")
            if answers.strip().lower() in {"/cancel", "/exit", "/quit"}:
                await client.post_hitl_response(job_id, {"action": "cancel"})
            else:
                await client.post_hitl_response(job_id, {"answers": {"response": answers}})
            continue

        if interaction_type == "confirm":
            summary = prompt_data.get("summary", "")
            path = prompt_data.get("path", "")
            console.print(
                Panel(
                    Markdown(summary) if summary else "No summary available.",
                    title="[bold cyan]📋 Understanding Summary[/bold cyan]",
                    border_style="cyan",
                )
            )
            if path:
                console.print(f"[dim]Proposed path: {path}[/dim]")
            action = Prompt.ask(
                "Proceed?",
                choices=["proceed", "revise", "cancel"],
                default="proceed",
                show_choices=True,
            )
            payload: dict[str, object] = {"action": action}
            if action == "revise":
                payload["feedback"] = Prompt.ask("What should change?", default="")
            await client.post_hitl_response(job_id, payload)
            continue

        if interaction_type == "preview":
            content = prompt_data.get("content", "")
            highlights = prompt_data.get("highlights", [])
            console.print(
                Panel(
                    Markdown(content) if content else "No preview available.",
                    title="[bold blue]📝 Content Preview[/bold blue]",
                    border_style="blue",
                )
            )
            if highlights:
                console.print("[dim]Highlights:[/dim]")
                for h in highlights:
                    console.print(f"  • {h}")
            action = Prompt.ask(
                "Looks good?",
                choices=["proceed", "refine", "cancel"],
                default="proceed",
                show_choices=True,
            )
            payload = {"action": action}
            if action == "refine":
                payload["feedback"] = Prompt.ask("What should be improved?", default="")
            await client.post_hitl_response(job_id, payload)
            continue

        if interaction_type == "validate":
            report = prompt_data.get("report", "")
            passed = prompt_data.get("passed", False)
            title_style = "green" if passed else "red"
            title_icon = "✅" if passed else "⚠️"
            console.print(
                Panel(
                    Markdown(report) if report else "No report available.",
                    title=f"[bold {title_style}]{title_icon} Validation Report[/bold {title_style}]",
                    border_style=title_style,
                )
            )
            action = Prompt.ask(
                "Accept?",
                choices=["proceed", "refine", "cancel"],
                default="proceed",
                show_choices=True,
            )
            payload = {"action": action}
            if action == "refine":
                payload["feedback"] = Prompt.ask("What should be improved?", default="")
            await client.post_hitl_response(job_id, payload)
            continue

        # Unknown HITL type - show raw data and allow generic response
        console.print(
            Panel(
                f"Unknown interaction type: {interaction_type}\nData: {prompt_data}",
                title="[bold yellow]⚠️ Unknown HITL[/bold yellow]",
                border_style="yellow",
            )
        )
        action = Prompt.ask(
            "Action",
            choices=["proceed", "cancel"],
            default="proceed",
            show_choices=True,
        )
        await client.post_hitl_response(job_id, {"action": action})
