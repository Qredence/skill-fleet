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
import re
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

from ..ui.prompts import (
    PromptUI,
    choose_many_with_other,
    choose_one_with_other,
    get_default_ui,
)
from ..utils.constants import HITL_POLL_INTERVAL

# Import handler registry for new interaction types
from .handlers import get_handler


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


def _normalize_questions(questions: object) -> list[object]:
    """Normalize HITL `questions` into a list.

    The API may return:
    - a single string
    - a list of dicts/strings
    - None
    """

    def _split_numbered(text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        # If it looks like a numbered list ("1. ...\n2. ..."), split it.
        matches = list(re.finditer(r"(?m)^\s*\d+\.\s+", text))
        if len(matches) <= 1:
            return [text]

        parts: list[str] = []
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            chunk = text[start:end].strip()
            chunk = re.sub(r"^\s*\d+\.\s*", "", chunk)
            if chunk:
                parts.append(chunk)
        return parts

    if questions is None:
        return []
    if isinstance(questions, str):
        return _split_numbered(questions)
    if isinstance(questions, list):
        normalized: list[object] = []
        for q in questions:
            if isinstance(q, str):
                normalized.extend(_split_numbered(q))
            else:
                normalized.append(q)
        return normalized
    return [questions]


def _question_text(question: object) -> str:
    if isinstance(question, str):
        return question
    if isinstance(question, dict):
        return str(question.get("question") or question.get("text") or question)
    return str(question)


def _question_options(question: object) -> tuple[list[tuple[str, str]], bool]:
    """Return (choices, allows_multiple) for a structured question payload."""

    if not isinstance(question, dict):
        return ([], False)

    raw_options = question.get("options")
    if not isinstance(raw_options, list) or not raw_options:
        return ([], False)

    choices: list[tuple[str, str]] = []
    for opt in raw_options:
        if isinstance(opt, dict):
            opt_id = str(opt.get("id") or opt.get("value") or "")
            label = str(opt.get("label") or opt.get("text") or opt_id)
            desc = str(opt.get("description") or "")
            if desc:
                label = f"{label} — {desc}"
            if opt_id:
                choices.append((opt_id, label))
        else:
            choices.append((str(opt), str(opt)))

    allows_multiple = bool(question.get("allows_multiple", False))
    return (choices, allows_multiple)


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
    """Poll and satisfy HITL prompts until the job reaches a terminal state.

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
                spinner = None
            return prompt_data

        if status != "pending_hitl":
            message = f"[dim]Workflow running… ({status})[/dim]"
            if spinner is None:
                spinner = console.status(message, spinner="dots")
                spinner.start()
            else:
                spinner.update(message)
            await asyncio.sleep(current_interval)
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

        # Check if there's a registered handler for this interaction type
        # (new types: deep_understanding, tdd_red, tdd_green, tdd_refactor)
        handler = get_handler(interaction_type, console, ui)
        if handler:
            await handler.handle(job_id, prompt_data, client)
            continue

        # Existing inline handlers for: clarify, confirm, preview, validate
        if interaction_type == "clarify":
            rationale = prompt_data.get("rationale", "")
            if show_thinking and rationale:
                console.print(
                    Panel(
                        Markdown(rationale) if "**" in rationale else rationale,
                        title="[dim]Why I'm asking[/dim]",
                        border_style="dim",
                    )
                )

            questions_list = _normalize_questions(prompt_data.get("questions"))
            if not questions_list:
                rendered = _render_questions(prompt_data.get("questions"))
                console.print(
                    Panel(
                        Markdown(rendered) if rendered else "No questions available.",
                        title="[bold yellow]🤔 Clarification Needed[/bold yellow]",
                        border_style="yellow",
                    )
                )
                answers = await ui.ask_text("Your answers (or /cancel)", default="")
                if answers.strip().lower() in {"/cancel", "/exit", "/quit"}:
                    await client.post_hitl_response(job_id, {"action": "cancel"})
                else:
                    await client.post_hitl_response(job_id, {"answers": {"response": answers}})
                continue

            console.print(
                Panel(
                    "Answer the following question(s) one at a time.",
                    title="[bold yellow]🤔 Clarification Needed[/bold yellow]",
                    border_style="yellow",
                )
            )

            answer_blocks: list[str] = []
            for idx, question in enumerate(questions_list, 1):
                q_text = _question_text(question)
                choices, allows_multiple = _question_options(question)

                # Display question content cleanly (don't cram a full markdown list into the input prompt).
                console.print(
                    Panel(
                        Markdown(q_text)
                        if any(tok in q_text for tok in ("**", "`", "\n"))
                        else q_text,
                        title=f"[bold yellow]Question {idx}/{len(questions_list)}[/bold yellow]",
                        border_style="yellow",
                    )
                )

                if choices:
                    if allows_multiple:
                        selected_ids, free_text = await choose_many_with_other(
                            ui,
                            "Select option(s)",
                            choices,
                        )
                    else:
                        selected_ids, free_text = await choose_one_with_other(
                            ui,
                            "Select one option",
                            choices,
                        )
                    selected_labels = [label for opt_id, label in choices if opt_id in selected_ids]
                    answer = ", ".join(selected_labels)
                    if free_text.strip():
                        answer = f"{answer}\nOther: {free_text}" if answer else free_text
                else:
                    answer = await ui.ask_text("Your answer (or /cancel)", default="")
                    if answer.strip().lower() in {"/cancel", "/exit", "/quit"}:
                        await client.post_hitl_response(job_id, {"action": "cancel"})
                        answer_blocks = []
                        break

                answer_blocks.append(f"Q{idx}: {q_text}\nA{idx}: {answer}")

            if not answer_blocks:
                continue

            combined = "\n\n".join(answer_blocks).strip()
            await client.post_hitl_response(job_id, {"answers": {"response": combined}})
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
            action = await ui.choose_one(
                "Proceed?",
                [("proceed", "Proceed"), ("revise", "Revise"), ("cancel", "Cancel")],
                default_id="proceed",
            )
            payload: dict[str, object] = {"action": action}
            if action == "revise":
                payload["feedback"] = await ui.ask_text("What should change?", default="")
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
            action = await ui.choose_one(
                "Looks good?",
                [("proceed", "Proceed"), ("refine", "Refine"), ("cancel", "Cancel")],
                default_id="proceed",
            )
            payload = {"action": action}
            if action == "refine":
                payload["feedback"] = await ui.ask_text("What should be improved?", default="")
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
            action = await ui.choose_one(
                "Accept?",
                [("proceed", "Proceed"), ("refine", "Refine"), ("cancel", "Cancel")],
                default_id="proceed",
            )
            payload = {"action": action}
            if action == "refine":
                payload["feedback"] = await ui.ask_text("What should be improved?", default="")
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
        action = await ui.choose_one(
            "Action",
            [("proceed", "Proceed"), ("cancel", "Cancel")],
            default_id="proceed",
        )
        await client.post_hitl_response(job_id, {"action": action})
