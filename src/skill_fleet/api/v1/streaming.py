"""
Streaming endpoints for skill creation with real-time progress.

Provides Server-Sent Events (SSE) endpoints for live workflow progress,
including thoughts, reasoning, and intermediate results.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from skill_fleet.api.services.event_registry import get_event_registry
from skill_fleet.api.services.job_manager import get_job_manager
from skill_fleet.core.workflows.skill_creation.generation import GenerationWorkflow
from skill_fleet.core.workflows.skill_creation.understanding import UnderstandingWorkflow
from skill_fleet.core.workflows.skill_creation.validation import ValidationWorkflow
from skill_fleet.core.workflows.streaming import (
    StreamingWorkflowManager,
    WorkflowEvent,
    WorkflowEventType,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuration constants
STATUS_POLL_INTERVAL = 0.5  # seconds
HITL_CHECK_INTERVAL = 1.0  # seconds
MAX_CONSECUTIVE_TIMEOUTS = 10
HEARTBEAT_INTERVAL = 15.0  # seconds - emit heartbeat to keep connection alive


# Job status constants
class JobStatus:
    """Job status constants."""

    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PENDING_USER_INPUT = "pending_user_input"
    PENDING_HITL = "pending_hitl"
    PENDING_REVIEW = "pending_review"


# pending_review is a terminal state for streaming purposes: the workflow is finished,
# but the result needs human attention (e.g., failed validation). Clients should stop
# streaming and show the final prompt/result.
TERMINAL_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
    JobStatus.PENDING_REVIEW,
}
HITL_STATUSES = {JobStatus.PENDING_USER_INPUT, JobStatus.PENDING_HITL}


class StreamCreateRequest(BaseModel):
    """Request for streaming skill creation."""

    task_description: str
    user_id: str = "default"
    enable_hitl: bool = True
    quality_threshold: float = 0.75


async def _format_sse_event(event: WorkflowEvent) -> str:
    """Format workflow event as SSE with monotonic sequence for stale detection."""
    data = {
        "type": event.event_type.value,
        "phase": event.phase,
        "message": event.message,
        "data": event.data,
        "timestamp": event.timestamp,
        "sequence": event.sequence,  # Monotonic counter for detecting gaps
    }
    return f"data: {json.dumps(data)}\n\n"


async def _handle_hitl_event(event: WorkflowEvent) -> str | None:
    """
    Check if event requires HITL and return formatted pause message.

    Returns formatted SSE message if HITL required, None otherwise.
    """
    if event.event_type == WorkflowEventType.HITL_REQUIRED:
        return (
            f"data: {json.dumps({'type': 'hitl_pause', 'message': 'Waiting for user input'})}\n\n"
        )
    return None


async def _execute_skill_creation_stream(
    task_description: str,
    user_id: str,
    enable_hitl: bool,
    quality_threshold: float,
    request: Request,
) -> StreamingResponse:
    """Execute skill creation with streaming events."""

    async def event_generator() -> AsyncGenerator[str, None]:
        manager = StreamingWorkflowManager()

        try:
            # Phase 1: Understanding
            understanding_workflow = UnderstandingWorkflow()
            understanding_result = None

            async for event in understanding_workflow.execute_streaming(
                task_description=task_description,
                user_context={"user_id": user_id},
                manager=manager,
            ):
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected during understanding phase")
                    return

                yield await _format_sse_event(event)

                # Check for HITL suspension
                hitl_response = await _handle_hitl_event(event)
                if hitl_response:
                    yield hitl_response
                    return

                # Capture completion result efficiently
                if event.event_type == WorkflowEventType.COMPLETED:
                    understanding_result = event.data.get("result", {})
                    break

            if (
                understanding_result is None
                or understanding_result.get("status") != JobStatus.COMPLETED
            ):
                yield f"data: {json.dumps({'type': 'error', 'message': 'Understanding phase failed'})}\n\n"
                return

            # Phase 2: Generation
            generation_workflow = GenerationWorkflow()
            generation_result = None

            async for event in generation_workflow.execute_streaming(
                plan=understanding_result.get("plan", {}),
                understanding=understanding_result,
                enable_hitl_preview=enable_hitl,
                quality_threshold=quality_threshold,
                manager=manager,
            ):
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected during generation phase")
                    return

                yield await _format_sse_event(event)

                hitl_response = await _handle_hitl_event(event)
                if hitl_response:
                    yield hitl_response
                    return

                if event.event_type == WorkflowEventType.COMPLETED:
                    generation_result = event.data.get("result", {})
                    break

            if generation_result is None or generation_result.get("status") != JobStatus.COMPLETED:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Generation phase failed'})}\n\n"
                return

            # Phase 3: Validation
            validation_workflow = ValidationWorkflow()

            async for event in validation_workflow.execute_streaming(
                skill_content=generation_result.get("skill_content", ""),
                plan=understanding_result.get("plan", {}),
                taxonomy_path=understanding_result.get("taxonomy", {}).get("recommended_path", ""),
                enable_hitl_review=enable_hitl,
                quality_threshold=quality_threshold,
                manager=manager,
            ):
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info("Client disconnected during validation phase")
                    return

                yield await _format_sse_event(event)

                hitl_response = await _handle_hitl_event(event)
                if hitl_response:
                    yield hitl_response
                    return

                if event.event_type == WorkflowEventType.COMPLETED:
                    break

            yield f"data: {json.dumps({'type': 'complete', 'message': 'Skill creation completed'})}\n\n"

        except Exception:
            # Log detailed error information on the server, including the stack trace,
            # but do not expose internal details to the client.
            logger.exception("Streaming error")
            yield f"data: {json.dumps({'type': 'error', 'message': 'An internal error occurred during streaming.'})}\n\n"

        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/stream")
async def create_skill_streaming(
    request: StreamCreateRequest,
    http_request: Request,  # noqa: B008
):
    r"""
    Create a skill with real-time streaming progress.

    Returns a Server-Sent Events stream with:
    - Phase transitions (Understanding, Generation, Validation)
    - Module execution status
    - Reasoning/thoughts from AI
    - Progress updates
    - HITL suspension points
    - Final result

    Example:
        curl -X POST http://localhost:8000/api/v1/skills/stream \\
            -H "Content-Type: application/json" \\
            -d '{"task_description": "Build a React app"}'

    """
    return await _execute_skill_creation_stream(
        task_description=request.task_description,
        user_id=request.user_id,
        enable_hitl=request.enable_hitl,
        quality_threshold=request.quality_threshold,
        request=http_request,
    )


@router.get("/{job_id}/stream")
async def get_job_stream(
    job_id: str,
    request: Request,  # noqa: B008
):
    """
    Get real-time stream for an existing job.

    Streams workflow events (reasoning, progress, phase transitions) for a job in progress.
    Falls back to status polling if no event queue is registered.
    """
    job_manager = get_job_manager()
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    event_registry = get_event_registry()
    event_queue = await event_registry.get(job_id)

    async def event_stream() -> AsyncGenerator[str, None]:
        """Stream workflow events from the registered queue."""
        last_status = None
        timeout_count = 0
        timeout_warning_issued = False
        last_heartbeat = time.time()

        try:
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from job {job_id} stream")
                    break

                # Emit heartbeat to keep connection alive
                current_time = time.time()
                if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_time, 'sequence': -1})}\n\n"
                    last_heartbeat = current_time

                # Check if job is still active
                job = await job_manager.get_job(job_id)
                if not job:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found', 'sequence': -1})}\n\n"
                    break

                status = job.status

                # Emit status update if changed
                if status != last_status:
                    yield f"data: {json.dumps({'type': 'status', 'status': status, 'message': f'Job status: {status}', 'sequence': -1})}\n\n"
                    last_status = status
                    # Reset heartbeat on status change to avoid redundant heartbeats
                    last_heartbeat = current_time

                # Terminal states
                if status in TERMINAL_STATUSES:
                    yield f"data: {json.dumps({'type': 'complete', 'status': status})}\n\n"
                    break

                # HITL pause states - emit status and wait
                if status in HITL_STATUSES:
                    yield f"data: {json.dumps({'type': 'hitl_pause', 'status': status, 'message': f'Waiting for user: {status}'})}\n\n"
                    await asyncio.sleep(HITL_CHECK_INTERVAL)
                    continue

                # Try to get event from queue with timeout
                if event_queue:
                    try:
                        event = await asyncio.wait_for(
                            event_queue.get(), timeout=STATUS_POLL_INTERVAL
                        )
                        timeout_count = 0  # Reset timeout counter on successful event
                        timeout_warning_issued = False  # Reset warning flag
                        yield await _format_sse_event(event)

                        # Check for completion/error events
                        if event.event_type in {
                            WorkflowEventType.COMPLETED,
                            WorkflowEventType.ERROR,
                        }:
                            break
                        if event.event_type == WorkflowEventType.HITL_REQUIRED:
                            yield f"data: {json.dumps({'type': 'hitl_pause', 'message': 'HITL required', 'sequence': event.sequence})}\n\n"
                            await asyncio.sleep(HITL_CHECK_INTERVAL)

                    except TimeoutError:
                        timeout_count += 1
                        # Fall back to status polling if too many timeouts
                        if timeout_count >= MAX_CONSECUTIVE_TIMEOUTS and not timeout_warning_issued:
                            logger.warning(
                                f"Job {job_id}: No events for {MAX_CONSECUTIVE_TIMEOUTS * STATUS_POLL_INTERVAL}s, falling back to status"
                            )
                            timeout_warning_issued = True
                        await asyncio.sleep(STATUS_POLL_INTERVAL)
                else:
                    # No event queue registered, fall back to status polling
                    await asyncio.sleep(STATUS_POLL_INTERVAL)

        except Exception as e:
            logger.error(f"Streaming error for job {job_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
