"""
Shared HITL job runner for CLI commands.

The Skill Fleet API uses a background job + HITL (Human-in-the-Loop) prompt model:
- CLI starts a job via `/api/v1/skills/`
- API exposes the current prompt via `/api/v1/hitl/{job_id}/prompt`
- CLI responds via `/api/v1/hitl/{job_id}/response`

This module centralizes the polling + interaction handling so `create` and `chat`
commands stay consistent.
"""

from __future__ import annotations

import asyncio
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.status import Status

from ..ui.prompts import PromptUI, get_default_ui
from ..utils.constants import HITL_POLL_INTERVAL

# Import handler registry for new interaction types
from .handlers import get_handler


async def run_hitl_job(
    *,
    console: Console,
    client: Any,
    job_id: str,
    auto_approve: bool = False,
    ui: PromptUI | None = None,
    show_thinking: bool = True,
    force_plain_text: bool = False,
    poll_interval: float = HITL_POLL_INTERVAL,
) -> dict[str, Any]:
    """
    Poll and satisfy HITL prompts until the job reaches a terminal state.

    Returns the final prompt payload from the API (status + result fields).
    """
    ui = ui or get_default_ui(force_plain_text=force_plain_text)

    spinner: Status | None = None
    current_interval = float(poll_interval)

    while True:
        prompt_data = await client.get_hitl_prompt(job_id)
        status = prompt_data.get("status")

        if status in {"completed", "failed", "cancelled"}:
            if spinner is not None:
                spinner.stop()
            return prompt_data

        if status not in {"pending_hitl", "pending_user_input"}:
            # Build progress message from API response
            current_phase = prompt_data.get("current_phase", "")
            progress_message = prompt_data.get("progress_message", "")

            if progress_message:
                phase_label = f"[cyan]{current_phase}[/cyan]: " if current_phase else ""
                message = f"[dim]{phase_label}{progress_message}[/dim]"
            else:
                message = f"[dim]Workflow running… ({status})[/dim]"

            if spinner is None:
                spinner = console.status(message, spinner="dots")
                spinner.start()
            else:
                spinner.update(message)
            await asyncio.sleep(current_interval)
            # Only increase interval for slow polling mode
            if poll_interval >= 1.0:
                current_interval = min(max(poll_interval, 0.5) * 5.0, current_interval * 1.25)
            continue

        if spinner is not None:
            spinner.stop()
            spinner = None
        current_interval = float(poll_interval)

        interaction_type = prompt_data.get("type")

        if auto_approve:
            if interaction_type == "clarify":
                await client.post_hitl_response(job_id, {"answers": {"response": ""}})
            else:
                await client.post_hitl_response(job_id, {"action": "proceed"})
            continue

        # All interaction types now use the handler registry
        handler = get_handler(interaction_type, console, ui)
        if handler:
            await handler.handle(job_id, prompt_data, client)
            continue

        # Unknown HITL type - show raw data and allow generic response
        console.print(
            Panel(
                f"Unknown interaction type: {interaction_type}\nData: {prompt_data}",
                title="[bold yellow]⚠️ Unknown HITL[/bold yellow]",
                border_style="yellow",
            )
        )
        action = await ui.choose_one(
            "Action",
            [("proceed", "Proceed"), ("cancel", "Cancel")],
            default_id="proceed",
        )
        await client.post_hitl_response(job_id, {"action": action})
