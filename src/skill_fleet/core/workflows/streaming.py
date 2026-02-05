"""
Streaming workflow manager for real-time skill creation progress.

Provides event-based progress reporting with reasoning, thoughts, and
intermediate results for each phase of the skill creation workflow.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from skill_fleet.common.serialization import normalize_dict_output

logger = logging.getLogger(__name__)

# Global sequence counter for monotonic event ordering
_event_sequence: int = 0
_sequence_lock: asyncio.Lock | None = None


async def _get_next_sequence() -> int:
    """Get next monotonic sequence number."""
    global _event_sequence, _sequence_lock
    if _sequence_lock is None:
        _sequence_lock = asyncio.Lock()
    async with _sequence_lock:
        _event_sequence += 1
        return _event_sequence


class WorkflowEventType(Enum):
    """Types of workflow events."""

    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    MODULE_START = "module_start"
    MODULE_END = "module_end"
    REASONING = "reasoning"
    PROGRESS = "progress"
    TOKEN_STREAM = "token_stream"  # Token-level streaming from LLM
    HITL_REQUIRED = "hitl_required"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class WorkflowEvent:
    """Event emitted during workflow execution."""

    event_type: WorkflowEventType
    phase: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())
    sequence: int = field(default=0)  # Monotonic sequence number (set at creation)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization."""
        return {
            "type": self.event_type.value,
            "phase": self.phase,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }


class StreamingWorkflowManager:
    """
    Manages workflow execution with real-time event streaming.

    Provides detailed progress updates including:
    - Phase transitions (Understanding, Generation, Validation)
    - Module execution status with reasoning
    - HITL suspension points
    - Error handling with context

    Example:
        manager = StreamingWorkflowManager()
        async for event in manager.execute_skill_creation(task="Build a React app"):
            print(f"{event.phase}: {event.message}")
            if event.event_type == WorkflowEventType.REASONING:
                print(f"  Reasoning: {event.data.get('reasoning')}")

    """

    def __init__(self, event_queue: asyncio.Queue[WorkflowEvent] | None = None):
        """
        Initialize workflow manager.

        Args:
            event_queue: Optional external event queue to use (for registry integration).
                        If not provided, creates a new internal queue.

        """
        self.event_queue: asyncio.Queue[WorkflowEvent] = event_queue or asyncio.Queue()
        self._current_phase: str = ""
        self._completed_phases: list[str] = []
        self._lock = asyncio.Lock()

    async def emit(
        self,
        event_type: WorkflowEventType,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Emit a workflow event."""
        sequence = await _get_next_sequence()
        event = WorkflowEvent(
            event_type=event_type,
            phase=self._current_phase,
            message=message,
            data=data or {},
            sequence=sequence,
        )
        await self.event_queue.put(event)
        # Sanitize message for logging to avoid log injection (e.g., forged new log lines)
        safe_message = str(message).replace("\r", " ").replace("\n", " ")
        logger.debug(f"Emitted: {event_type.value} - {safe_message}")

    async def set_phase(self, phase: str) -> None:
        """Set current workflow phase and emit event."""
        async with self._lock:
            if self._current_phase:
                await self.emit(WorkflowEventType.PHASE_END, f"Completed {self._current_phase}")
                self._completed_phases.append(self._current_phase)

            self._current_phase = phase
        await self.emit(WorkflowEventType.PHASE_START, f"Starting {phase}")
        logger.info(f"Workflow phase: {phase}")

    async def execute_module(
        self,
        name: str,
        module_func: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        """Execute a module with event tracking."""
        await self.emit(WorkflowEventType.MODULE_START, f"Running {name}", {"module": name})

        try:
            # Check if module supports streaming
            if hasattr(module_func, "astream"):
                result = await self._execute_streaming_module(name, module_func, **kwargs)
            else:
                result = await module_func(**kwargs)

            # Extract reasoning if available
            reasoning = None
            if hasattr(result, "reasoning"):
                reasoning = result.reasoning
            elif isinstance(result, dict) and "reasoning" in result:
                reasoning = result["reasoning"]

            if reasoning:
                await self.emit(
                    WorkflowEventType.REASONING,
                    f"{name} reasoning",
                    {"module": name, "reasoning": str(reasoning)[:500]},  # Truncate for safety
                )

            await self.emit(
                WorkflowEventType.MODULE_END,
                f"Completed {name}",
                {"module": name, "success": True},
            )

            return self._normalize_result(result)

        except Exception as e:
            await self.emit(
                WorkflowEventType.ERROR,
                f"Error in {name}: {str(e)}",
                {"module": name, "error": str(e)},
            )
            raise

    async def execute_module_streaming(
        self,
        name: str,
        streaming_func: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        """
        Execute a module with token-level streaming support.

        This method handles modules that yield streaming tokens,
        emitting TOKEN_STREAM events for each chunk.

        Args:
            name: Module name for logging
            streaming_func: Async generator function (e.g., module.aforward_streaming)
            **kwargs: Arguments to pass to the module

        Returns:
            Final result from the module

        """
        await self.emit(
            WorkflowEventType.MODULE_START, f"Running {name} (streaming)", {"module": name}
        )

        try:
            final_result = None

            async for event in streaming_func(**kwargs):
                if event.get("type") == "token":
                    # Emit token-level streaming event
                    await self.emit(
                        WorkflowEventType.TOKEN_STREAM,
                        event.get("content", ""),
                        {
                            "module": name,
                            "field": event.get("field", "unknown"),
                            "chunk": event.get("content", ""),
                        },
                    )
                elif event.get("type") == "prediction":
                    final_result = event.get("data", {})
                elif event.get("type") == "message":
                    await self.emit(
                        WorkflowEventType.PROGRESS,
                        event.get("content", ""),
                        {"module": name},
                    )

            await self.emit(
                WorkflowEventType.MODULE_END,
                f"Completed {name}",
                {"module": name, "success": True, "streaming": True},
            )

            return final_result or {}

        except Exception as e:
            await self.emit(
                WorkflowEventType.ERROR,
                f"Error in {name}: {str(e)}",
                {"module": name, "error": str(e)},
            )
            raise

    async def _execute_streaming_module(
        self,
        name: str,
        module_func: Callable[..., Any],
        **kwargs: Any,
    ) -> Any:
        """Execute a streaming module and capture intermediate reasoning."""
        # This would integrate with dspy.streaming
        # For now, just call the function
        return await module_func(**kwargs)

    def _normalize_result(self, result: Any) -> dict[str, Any] | Any:
        """
        Normalize module output to dict when possible.

        Most workflows and unit tests expect dict semantics (especially `.get(...)`). DSPy often
        returns objects like `dspy.Prediction` which are typically dict-convertible but may not be
        dict-typed. This helper keeps workflow contracts stable while allowing modules to return
        rich objects.
        """
        if isinstance(result, dict):
            return result

        try:
            return normalize_dict_output(result, remove_none=False)
        except Exception:
            pass  # nosec B110

        # Best-effort fallbacks.
        if hasattr(result, "__dict__") and isinstance(getattr(result, "__dict__", None), dict):
            data = {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
            if data:
                return data

        return {"value": str(result)}

    async def suspend_for_hitl(
        self,
        hitl_type: str,
        data: dict[str, Any],
        context: dict[str, Any],
    ) -> None:
        """Suspend workflow for HITL interaction."""
        await self.emit(
            WorkflowEventType.HITL_REQUIRED,
            f"Waiting for user input: {hitl_type}",
            {
                "hitl_type": hitl_type,
                "data": data,
                "context": context,
            },
        )

    def get_events(self) -> AsyncIterator[WorkflowEvent]:
        """Get event stream iterator."""
        return self._event_generator()

    async def _event_generator(self) -> AsyncIterator[WorkflowEvent]:
        """Generate events from queue."""
        while True:
            event = await self.event_queue.get()
            yield event

            # Stop if workflow is complete or errored
            if event.event_type in (WorkflowEventType.COMPLETED, WorkflowEventType.ERROR):
                break

    async def complete(self, result: dict[str, Any]) -> None:
        """Mark workflow as completed."""
        await self.emit(
            WorkflowEventType.COMPLETED,
            "Skill creation completed",
            {"result": result, "phases_completed": self._completed_phases},
        )


class WorkflowProgressTracker:
    """
    Tracks and formats workflow progress for display.

    Example:
        tracker = WorkflowProgressTracker()
        async for event in workflow_events:
            display_text = tracker.format_event(event)
            print(display_text)

    """

    def __init__(self):
        self.current_phase: str = ""
        self.module_stack: list[str] = []
        self.reasoning_buffer: list[str] = []

    def format_event(self, event: WorkflowEvent) -> str | None:
        """
        Format event for display.

        Returns:
            Formatted string for display, or None if event should be skipped.

        """
        if event.event_type == WorkflowEventType.PHASE_START:
            self.current_phase = event.phase
            return f"\n[bold cyan]▶ {event.phase}[/bold cyan]"

        elif event.event_type == WorkflowEventType.PHASE_END:
            return f"[dim]✓ {event.phase} completed[/dim]"

        elif event.event_type == WorkflowEventType.MODULE_START:
            self.module_stack.append(event.data.get("module", "unknown"))
            return f"  [dim]Running {event.message}...[/dim]"

        elif event.event_type == WorkflowEventType.MODULE_END:
            if self.module_stack:
                self.module_stack.pop()
            return None  # Don't show completion, just update state

        elif event.event_type == WorkflowEventType.REASONING:
            reasoning = event.data.get("reasoning", "")
            if reasoning:
                self.reasoning_buffer.append(reasoning)
                # Show truncated reasoning
                lines = reasoning.split("\n")[:3]  # First 3 lines
                preview = "\n".join(lines)
                if len(reasoning) > 200:
                    preview = preview[:200] + "..."
                return f"    [dim italic]💭 {preview}[/dim italic]"
            return None

        elif event.event_type == WorkflowEventType.PROGRESS:
            progress = event.data.get("progress", 0)
            return f"  [dim]Progress: {progress}%[/dim]"

        elif event.event_type == WorkflowEventType.TOKEN_STREAM:
            # Return token chunk for real-time display
            chunk = event.data.get("chunk", "")
            return chunk  # Raw chunk for streaming display

        elif event.event_type == WorkflowEventType.HITL_REQUIRED:
            return f"\n[bold yellow]⏸ {event.message}[/bold yellow]"

        elif event.event_type == WorkflowEventType.ERROR:
            return f"\n[bold red]✗ Error: {event.message}[/bold red]"

        elif event.event_type == WorkflowEventType.COMPLETED:
            return "\n[bold green]✨ Skill creation completed![/bold green]"

        return None


# Global workflow manager instance
_workflow_manager: StreamingWorkflowManager | None = None


def get_workflow_manager() -> StreamingWorkflowManager:
    """Get global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = StreamingWorkflowManager()
    return _workflow_manager
