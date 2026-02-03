"""
Streaming runner for real-time skill creation progress.

Displays live updates including:
- Phase transitions
- Module execution status
- AI reasoning/thoughts
- Progress indicators
- HITL suspension points with interactive handlers

Supports hybrid mode: streaming for progress/reasoning, polling for HITL responses.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from .hitl.handlers import get_handler
from .ui.prompts import PromptUI, get_default_ui

if TYPE_CHECKING:
    from skill_fleet.cli.client import SkillFleetClient

logger = logging.getLogger(__name__)


class StreamingJobRunner:
    """
    Runs skill creation with real-time streaming display.

    Example:
        runner = StreamingJobRunner(console, client)
        result = await runner.run_streaming("Build a React app")
    """

    def __init__(
        self,
        console: Console,
        client: SkillFleetClient,
        show_thinking: bool = True,
        ui: PromptUI | None = None,
        force_plain_text: bool = False,
    ) -> None:
        """
        Initialize streaming job runner.

        Args:
            console: Rich console for output
            client: API client for streaming requests
            show_thinking: Whether to display AI reasoning
            ui: PromptUI for HITL interactions (uses default if None)
            force_plain_text: Disable arrow-key dialogs for HITL

        """
        self.console = console
        self.client = client
        self.show_thinking = show_thinking
        self.ui = ui or get_default_ui(force_plain_text=force_plain_text)
        self.current_phase = ""
        self.current_module = ""
        self.reasoning_buffer: list[str] = []
        self.progress_items: list[dict[str, Any]] = []
        self._job_id: str | None = None
        self._hitl_event: dict[str, Any] | None = None

    async def run_streaming(
        self,
        task_description: str,
        user_id: str = "default",
        quality_threshold: float = 0.75,
    ) -> dict[str, Any]:
        """
        Run skill creation with streaming display.

        Args:
            task_description: Task description
            user_id: User identifier
            quality_threshold: Minimum quality threshold

        Returns:
            Final result dict
        """
        self.console.print(
            Panel.fit(
                f"[bold cyan]Creating Skill: {task_description[:50]}...[/bold cyan]\n"
                f"[dim]Real-time streaming with live AI reasoning[/dim]",
                border_style="cyan",
            )
        )

        # Create live display for progress
        with Live(self._create_progress_display(), refresh_per_second=4) as live:
            final_result = {}

            try:
                async for event in self.client.create_skill_streaming(
                    task=task_description,
                    user_id=user_id,
                    quality_threshold=quality_threshold,
                ):
                    event_type = event.get("type", "")

                    if event_type == "phase_start":
                        self.current_phase = event.get("phase", "")
                        self._add_progress_item(
                            "phase",
                            f"Starting {self.current_phase}",
                            "cyan",
                        )

                    elif event_type == "phase_end":
                        self._add_progress_item(
                            "complete",
                            f"Completed {event.get('phase', '')}",
                            "green",
                        )

                    elif event_type == "module_start":
                        self.current_module = event.get("data", {}).get("module", "")
                        self._add_progress_item(
                            "module",
                            f"Running {self.current_module}",
                            "dim",
                        )

                    elif event_type == "module_end":
                        module = event.get("data", {}).get("module", "")
                        self._add_progress_item(
                            "success",
                            f"Completed {module}",
                            "green",
                        )

                    elif event_type == "reasoning":
                        if self.show_thinking:
                            reasoning = event.get("data", {}).get("reasoning", "")
                            if reasoning:
                                self.reasoning_buffer.append(reasoning)
                                # Keep only last 5 reasoning items for better context
                                self.reasoning_buffer = self.reasoning_buffer[-5:]

                    elif event_type == "progress":
                        message = event.get("message", "")
                        data = event.get("data", {})
                        self._add_progress_item(
                            "info",
                            message,
                            "blue",
                            details=data,
                        )

                    elif event_type in ("hitl_required", "hitl_pause"):
                        hitl_type = event.get("data", {}).get("hitl_type", "input")
                        self._add_progress_item(
                            "warning",
                            f"Awaiting user input: {hitl_type}",
                            "yellow",
                        )
                        self._hitl_event = event
                        live.stop()
                        break

                    elif event_type == "completed":
                        final_result = event.get("data", {}).get("result", {})
                        self._add_progress_item(
                            "success",
                            "Skill creation completed!",
                            "green bold",
                        )
                        live.stop()
                        break

                    elif event_type == "error":
                        error_msg = event.get("message", "Unknown error")
                        self._add_progress_item(
                            "error",
                            f"Error: {error_msg}",
                            "red bold",
                        )
                        live.stop()
                        raise RuntimeError(error_msg)

                    # Update the live display
                    live.update(self._create_progress_display())

            except Exception as e:
                self.console.print(f"[red]Streaming error: {e}[/red]")
                raise

        # Display final summary
        self._display_summary(final_result)

        return final_result

    async def run_hybrid(
        self,
        task_description: str,
        user_id: str = "default",
        quality_threshold: float = 0.75,
        poll_interval: float = 0.1,
    ) -> dict[str, Any]:
        """
        Run skill creation with hybrid streaming + HITL polling.

        Streams progress and reasoning in real-time, switches to polling
        when HITL interaction is needed, then handles user input.

        Args:
            task_description: Task description
            user_id: User identifier
            quality_threshold: Minimum quality threshold
            poll_interval: Polling interval for HITL responses (seconds)

        Returns:
            Final result dict
        """
        self.console.print(
            Panel.fit(
                f"[bold cyan]Creating Skill: {task_description[:60]}...[/bold cyan]\n"
                f"[dim]Real-time streaming with live AI reasoning[/dim]",
                border_style="cyan",
            )
        )

        # First create the job via non-streaming endpoint to get job_id
        try:
            job_response = await self.client.create_skill(task_description, user_id)
            self._job_id = job_response.get("job_id")
            if not self._job_id:
                self.console.print(f"[red]Failed to create job: {job_response}[/red]")
                return {"status": "failed", "error": "No job_id returned"}
            self.console.print(f"[dim]Job started: {self._job_id}[/dim]")
        except Exception as e:
            self.console.print(f"[red]Failed to create job: {e}[/red]")
            return {"status": "failed", "error": str(e)}

        # Main hybrid loop
        while True:
            # Stream phase: display progress until HITL needed or completion
            stream_result = await self._stream_until_hitl_or_done()

            if stream_result.get("status") in ("completed", "failed", "cancelled"):
                return stream_result

            if stream_result.get("status") == "hitl_required":
                # Handle HITL interaction via polling
                hitl_result = await self._handle_hitl_interaction(poll_interval)
                if hitl_result.get("action") == "cancel":
                    return {"status": "cancelled"}
                # After HITL response, continue streaming loop
                continue

            # Unknown status, poll for more info
            await asyncio.sleep(poll_interval)

    async def _stream_until_hitl_or_done(self, timeout_seconds: float = 300.0) -> dict[str, Any]:
        """
        Stream events via SSE until HITL required or job completes.

        Uses Server-Sent Events for efficient real-time updates instead of polling.
        Falls back to polling only if SSE connection fails.

        Args:
            timeout_seconds: Maximum time to wait (default 5 minutes for LLM operations)

        Returns:
            Status dict with 'status' key indicating state
        """
        if not self._job_id:
            return {"status": "failed", "error": "No job_id"}

        with Live(
            self._create_progress_display(), refresh_per_second=4, console=self.console
        ) as live:
            try:
                # Try SSE streaming first (efficient)
                sse_result = await self._stream_via_sse(live, timeout_seconds)
                if sse_result is not None:
                    live.stop()
                    return sse_result

                # SSE stream ended without terminal state - fall back to single poll
                prompt_data = await self.client.get_hitl_prompt(self._job_id)
                status = prompt_data.get("status")

                if status in ("completed", "failed", "cancelled"):
                    live.stop()
                    return prompt_data

                if status in ("pending_hitl", "pending_user_input"):
                    self._hitl_event = prompt_data
                    live.stop()
                    return {"status": "hitl_required", "prompt_data": prompt_data}

                # Still running - this shouldn't happen often with SSE
                live.stop()
                return {"status": "running"}

            except Exception as e:
                logger.error(f"Stream error: {e}")
                live.stop()
                return {"status": "failed", "error": str(e)}

    async def _stream_via_sse(self, live: Live, timeout_seconds: float) -> dict[str, Any] | None:
        """
        Consume SSE stream and update live display.

        Args:
            live: Rich Live display to update
            timeout_seconds: Maximum time to wait

        Returns:
            Terminal state dict if reached, None if stream ended without terminal state
        """
        job_id = self._job_id
        if not job_id:
            return {"status": "failed", "error": "No job_id"}

        try:
            async with asyncio.timeout(timeout_seconds):
                async for event in self.client.stream_job_events(job_id):
                    event_type = event.get("type", "")

                    if event_type == "status":
                        status = event.get("status", "")
                        if status in ("completed", "failed", "cancelled"):
                            # Fetch full result via polling
                            return await self.client.get_hitl_prompt(job_id)
                        if status in ("pending_hitl", "pending_user_input"):
                            # HITL needed - return to handle interaction
                            return {"status": "hitl_required"}

                    elif event_type == "phase_start":
                        phase = event.get("phase", "") or event.get("data", {}).get("phase", "")
                        if phase and phase != self.current_phase:
                            if self.current_phase:
                                self._add_progress_item(
                                    "complete", f"Completed {self.current_phase}", "green"
                                )
                            self.current_phase = phase
                            self._add_progress_item("phase", f"Starting {phase}", "cyan")

                    elif event_type == "phase_end":
                        phase = event.get("phase", "") or event.get("data", {}).get("phase", "")
                        self._add_progress_item("complete", f"Completed {phase}", "green")

                    elif event_type == "module_start":
                        module = event.get("data", {}).get("module", "")
                        if module:
                            self.current_module = module
                            self._add_progress_item("module", f"Running {module}", "dim")

                    elif event_type == "module_end":
                        module = event.get("data", {}).get("module", "")
                        if module:
                            self._add_progress_item("success", f"Completed {module}", "green")
                            self.current_module = ""

                    elif event_type == "reasoning":
                        if self.show_thinking:
                            reasoning = event.get("data", {}).get("reasoning", "")
                            if reasoning:
                                self.reasoning_buffer.append(reasoning)
                                self.reasoning_buffer = self.reasoning_buffer[-5:]

                    elif event_type == "progress":
                        message = event.get("message", "") or event.get("data", {}).get(
                            "message", ""
                        )
                        if message:
                            if (
                                not self.progress_items
                                or self.progress_items[-1].get("message") != message
                            ):
                                self._add_progress_item("info", message, "dim")

                    elif event_type in ("hitl_required", "hitl_pause"):
                        # HITL needed - return to handle interaction
                        return {"status": "hitl_required"}

                    elif event_type in ("complete", "completed"):
                        # Workflow done - fetch full result
                        return await self.client.get_hitl_prompt(job_id)

                    elif event_type == "error":
                        error_msg = event.get("message", "Unknown error")
                        return {"status": "failed", "error": error_msg}

                    # Update display after each event
                    live.update(self._create_progress_display())

        except TimeoutError:
            return {
                "status": "failed",
                "error": f"Workflow timeout after {timeout_seconds}s. The backend may still be processing.",
            }
        except Exception as e:
            logger.debug(f"SSE stream error (may be normal): {e}")

        # Stream ended without terminal state
        return None

    async def _handle_hitl_interaction(self, poll_interval: float = 0.1) -> dict[str, Any]:
        """
        Handle HITL interaction using registered handlers.

        Args:
            poll_interval: Polling interval for waiting

        Returns:
            Dict with 'action' key indicating user choice
        """
        if not self._job_id:
            return {"action": "error", "error": "No job_id"}

        try:
            prompt_data = await self.client.get_hitl_prompt(self._job_id)
            interaction_type = prompt_data.get("type", "")

            # Use existing handler registry
            handler = get_handler(interaction_type, self.console, self.ui)
            if handler:
                await handler.handle(self._job_id, prompt_data, self.client)
                self._add_progress_item(
                    "success", f"Completed {interaction_type} interaction", "green"
                )
                return {"action": "proceed"}

            # Unknown type - show raw and allow proceed/cancel
            self.console.print(
                Panel(
                    f"Unknown interaction: {interaction_type}\nData: {prompt_data}",
                    title="[yellow]⚠️ Unknown HITL[/yellow]",
                    border_style="yellow",
                )
            )
            action = await self.ui.choose_one(
                "Action",
                [("proceed", "Proceed"), ("cancel", "Cancel")],
                default_id="proceed",
            )
            await self.client.post_hitl_response(self._job_id, {"action": action})
            return {"action": action}

        except Exception as e:
            logger.error(f"HITL handling error: {e}")
            return {"action": "error", "error": str(e)}

    def _add_progress_item(
        self,
        icon_type: str,
        message: str,
        style: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Add a progress item to the buffer.

        Args:
            icon_type: Type of icon to display
            message: Progress message text
            style: Rich style for the message
            details: Optional additional data

        """
        icons = {
            "phase": "▶",
            "complete": "✓",
            "module": "⚙",
            "success": "✓",
            "info": "ℹ",
            "warning": "⚠",
            "error": "✗",
        }

        self.progress_items.append(
            {
                "icon": icons.get(icon_type, "•"),
                "message": message,
                "style": style,
                "details": details or {},
            }
        )

        # Keep only last 20 items
        self.progress_items = self.progress_items[-20:]

    def _create_progress_display(self) -> Table:
        """
        Create the live progress display.

        Returns:
            Rich Table with current progress state

        """
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Content", ratio=1)

        # Current phase header
        if self.current_phase:
            table.add_row(Text(f"Phase: {self.current_phase}", style="bold cyan"))

        # Current module
        if self.current_module:
            table.add_row(Text(f"  Module: {self.current_module}", style="dim"))

        # Reasoning section
        if self.show_thinking and self.reasoning_buffer:
            table.add_row("")
            table.add_row(Text("💭 AI Reasoning:", style="italic dim"))
            for reasoning in self.reasoning_buffer:
                # Truncate long reasoning
                preview = reasoning[:150] + "..." if len(reasoning) > 150 else reasoning
                table.add_row(Text(f"  {preview}", style="dim italic"))

        # Progress history
        if self.progress_items:
            table.add_row("")
            table.add_row(Text("Recent Activity:", style="bold"))
            for item in self.progress_items[-10:]:  # Show last 10
                icon = item["icon"]
                message = item["message"]
                style = item["style"]
                table.add_row(Text(f"{icon} {message}", style=style))

        # Spinner for active work
        if not any(item["icon"] in ["✓", "✗"] for item in self.progress_items[-3:]):
            table.add_row("")
            table.add_row(Spinner("dots", text="Processing..."))

        return table

    def _display_summary(self, result: dict[str, Any]) -> None:
        """
        Display final result summary.

        Args:
            result: Job result dictionary

        """
        if not result:
            return

        status = result.get("status", "unknown")

        if status == "completed":
            self.console.print("\n[bold green]✨ Skill Creation Completed![/bold green]")

            # Show validation info if available
            validation_report = result.get("validation_report", {})
            if validation_report:
                score = validation_report.get("score", 0.0)
                passed = validation_report.get("passed", False)
                status_label = "PASS" if passed else "FAIL"
                status_color = "green" if passed else "yellow"
                self.console.print(
                    f"[{status_color}]Validation: {status_label} (score: {score:.2f})[/{status_color}]"
                )

        elif status == "pending_user_input":
            self.console.print("\n[bold yellow]⏸ Waiting for User Input[/bold yellow]")
            hitl_type = result.get("hitl_type", "")
            self.console.print(f"[dim]Type: {hitl_type}[/dim]")

        else:
            self.console.print(f"\n[bold yellow]Status: {status}[/bold yellow]")


async def run_streaming_job(
    console: Console,
    client: SkillFleetClient,
    task_description: str,
    user_id: str = "default",
    show_thinking: bool = True,
) -> dict[str, Any]:
    """
    Convenience function to run streaming job.

    Example:
        result = await run_streaming_job(
            console=console,
            client=client,
            task_description="Build a React app",
        )
    """
    runner = StreamingJobRunner(
        console=console,
        client=client,
        show_thinking=show_thinking,
    )

    return await runner.run_streaming(
        task_description=task_description,
        user_id=user_id,
    )


async def run_hybrid_job(
    console: Console,
    client: SkillFleetClient,
    task_description: str,
    user_id: str = "default",
    show_thinking: bool = True,
    force_plain_text: bool = False,
    poll_interval: float = 0.1,
) -> dict[str, Any]:
    """
    Run skill creation with hybrid streaming + HITL polling.

    Combines real-time progress display with interactive HITL handling.

    Args:
        console: Rich console for output
        client: API client
        task_description: Task description
        user_id: User identifier
        show_thinking: Whether to show AI reasoning
        force_plain_text: Disable arrow-key dialogs
        poll_interval: Polling interval for HITL (seconds)

    Returns:
        Final result dict

    Example:
        result = await run_hybrid_job(
            console=console,
            client=client,
            task_description="Build a memory graph skill",
            show_thinking=True,
        )
    """
    runner = StreamingJobRunner(
        console=console,
        client=client,
        show_thinking=show_thinking,
        force_plain_text=force_plain_text,
    )

    return await runner.run_hybrid(
        task_description=task_description,
        user_id=user_id,
        poll_interval=poll_interval,
    )
