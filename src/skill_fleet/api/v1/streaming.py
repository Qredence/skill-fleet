"""
Streaming endpoints for skill creation with real-time progress.

Provides Server-Sent Events (SSE) endpoints for live workflow progress,
including thoughts, reasoning, and intermediate results.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
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
from skill_fleet.infrastructure.db.database import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


class StreamCreateRequest(BaseModel):
    """Request for streaming skill creation."""

    task_description: str
    user_id: str = "default"
    enable_hitl: bool = True
    quality_threshold: float = 0.75


async def _format_sse_event(event: WorkflowEvent) -> str:
    """Format workflow event as SSE."""
    data = {
        "type": event.event_type.value,
        "phase": event.phase,
        "message": event.message,
        "data": event.data,
        "timestamp": event.timestamp,
    }
    return f"data: {json.dumps(data)}\n\n"


async def _execute_skill_creation_stream(
    task_description: str,
    user_id: str,
    enable_hitl: bool,
    quality_threshold: float,
) -> StreamingResponse:
    """Execute skill creation with streaming events."""

    async def event_generator():
        manager = StreamingWorkflowManager()

        try:
            # Phase 1: Understanding
            understanding_workflow = UnderstandingWorkflow()
            understanding_events = []

            async for event in understanding_workflow.execute_streaming(
                task_description=task_description,
                user_context={"user_id": user_id},
                manager=manager,
            ):
                yield await _format_sse_event(event)
                understanding_events.append(event)

                # Check for HITL suspension
                if event.event_type == WorkflowEventType.HITL_REQUIRED:
                    yield f"data: {json.dumps({'type': 'hitl_pause', 'message': 'Waiting for user input'})}\n\n"
                    return

                # Check for completion
                if event.event_type == WorkflowEventType.COMPLETED:
                    break

            # Get understanding result
            understanding_result = {}
            for event in reversed(understanding_events):
                if event.event_type == WorkflowEventType.COMPLETED:
                    understanding_result = event.data.get("result", {})
                    break

            if understanding_result.get("status") != "completed":
                yield f"data: {json.dumps({'type': 'error', 'message': 'Understanding phase failed'})}\n\n"
                return

            # Phase 2: Generation
            generation_workflow = GenerationWorkflow()
            generation_events = []

            async for event in generation_workflow.execute_streaming(
                plan=understanding_result.get("plan", {}),
                understanding=understanding_result,
                enable_hitl_preview=enable_hitl,
                quality_threshold=quality_threshold,
                manager=manager,
            ):
                yield await _format_sse_event(event)
                generation_events.append(event)

                if event.event_type == WorkflowEventType.HITL_REQUIRED:
                    yield f"data: {json.dumps({'type': 'hitl_pause', 'message': 'Waiting for user input'})}\n\n"
                    return

                if event.event_type == WorkflowEventType.COMPLETED:
                    break

            # Get generation result
            generation_result = {}
            for event in reversed(generation_events):
                if event.event_type == WorkflowEventType.COMPLETED:
                    generation_result = event.data.get("result", {})
                    break

            if generation_result.get("status") != "completed":
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
                yield await _format_sse_event(event)

                if event.event_type == WorkflowEventType.HITL_REQUIRED:
                    yield f"data: {json.dumps({'type': 'hitl_pause', 'message': 'Waiting for user input'})}\n\n"
                    return

                if event.event_type == WorkflowEventType.COMPLETED:
                    break

            yield f"data: {json.dumps({'type': 'complete', 'message': 'Skill creation completed'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

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
    db: Session = Depends(get_db),  # noqa: B008
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
    )


@router.get("/{job_id}/stream")
async def get_job_stream(
    job_id: str,
    db: Session = Depends(get_db),  # noqa: B008
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

    async def event_stream():
        """Stream workflow events from the registered queue."""
        last_status = None
        timeout_count = 0
        max_timeout = 10  # Max consecutive timeouts before falling back to status polling

        try:
            while True:
                # Check if job is still active
                job = await job_manager.get_job(job_id)
                if not job:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
                    break

                status = job.status

                # Emit status update if changed
                if status != last_status:
                    yield f"data: {json.dumps({'type': 'status', 'status': status, 'message': f'Job status: {status}'})}\n\n"
                    last_status = status

                # Terminal states
                if status in {"completed", "failed", "cancelled"}:
                    yield f"data: {json.dumps({'type': 'complete', 'status': status})}\n\n"
                    break

                # HITL pause states - emit status and wait
                if status in {"pending_user_input", "pending_hitl", "pending_review"}:
                    yield f"data: {json.dumps({'type': 'hitl_pause', 'status': status, 'message': f'Waiting for user: {status}'})}\n\n"
                    await asyncio.sleep(1.0)
                    continue

                # Try to get event from queue with timeout
                if event_queue:
                    try:
                        event = await asyncio.wait_for(event_queue.get(), timeout=0.5)
                        timeout_count = 0  # Reset timeout counter on successful event
                        yield await _format_sse_event(event)

                        # Check for completion/error events
                        if event.event_type in {
                            WorkflowEventType.COMPLETED,
                            WorkflowEventType.ERROR,
                        }:
                            break
                        if event.event_type == WorkflowEventType.HITL_REQUIRED:
                            yield f"data: {json.dumps({'type': 'hitl_pause', 'message': 'HITL required'})}\n\n"
                            await asyncio.sleep(1.0)

                    except TimeoutError:
                        timeout_count += 1
                        # Fall back to status polling if too many timeouts
                        if timeout_count >= max_timeout:
                            logger.warning(
                                f"Job {job_id}: No events for {max_timeout * 0.5}s, falling back to status"
                            )
                            await asyncio.sleep(0.5)
                else:
                    # No event queue registered, fall back to status polling
                    await asyncio.sleep(0.5)

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
