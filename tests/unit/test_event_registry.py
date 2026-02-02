"""
Test event registry for real-time job streaming.
"""

from __future__ import annotations

import asyncio

import pytest

from skill_fleet.api.services.event_registry import EventQueueRegistry
from skill_fleet.core.workflows.streaming import WorkflowEvent, WorkflowEventType


@pytest.mark.asyncio
async def test_registry_register_and_get():
    """Test registering and retrieving event queues."""
    registry = EventQueueRegistry()

    # Register queue for job
    queue = await registry.register("job-123")
    assert queue is not None

    # Retrieve same queue
    retrieved = await registry.get("job-123")
    assert retrieved is queue

    # Non-existent job
    missing = await registry.get("job-999")
    assert missing is None


@pytest.mark.asyncio
async def test_registry_unregister():
    """Test unregistering event queues."""
    registry = EventQueueRegistry()

    await registry.register("job-123")
    assert await registry.get("job-123") is not None

    # Unregister
    result = await registry.unregister("job-123")
    assert result is True

    # Should be gone
    assert await registry.get("job-123") is None

    # Unregister again should return False
    result = await registry.unregister("job-123")
    assert result is False


@pytest.mark.asyncio
async def test_event_queue_flow():
    """Test producing and consuming events through registered queue."""
    registry = EventQueueRegistry()

    # Register queue
    queue = await registry.register("job-123")

    # Producer: emit events
    event1 = WorkflowEvent(
        event_type=WorkflowEventType.PHASE_START,
        phase="understanding",
        message="Starting understanding phase",
    )
    event2 = WorkflowEvent(
        event_type=WorkflowEventType.REASONING,
        phase="understanding",
        message="Analyzing requirements",
        data={"reasoning": "User wants to build a React app"},
    )

    await queue.put(event1)
    await queue.put(event2)

    # Consumer: retrieve events
    retrieved1 = await queue.get()
    assert retrieved1.event_type == WorkflowEventType.PHASE_START
    assert retrieved1.phase == "understanding"

    retrieved2 = await queue.get()
    assert retrieved2.event_type == WorkflowEventType.REASONING
    assert retrieved2.data["reasoning"] == "User wants to build a React app"


@pytest.mark.asyncio
async def test_multiple_jobs():
    """Test registry with multiple concurrent jobs."""
    registry = EventQueueRegistry()

    # Register multiple jobs
    queue1 = await registry.register("job-1")
    queue2 = await registry.register("job-2")
    queue3 = await registry.register("job-3")

    assert queue1 is not queue2
    assert queue2 is not queue3

    # Each queue should be independent
    await queue1.put(WorkflowEvent(WorkflowEventType.PHASE_START, "job1", "Job 1 event"))
    await queue2.put(WorkflowEvent(WorkflowEventType.PHASE_START, "job2", "Job 2 event"))

    # Queue 1 should have 1 event
    event1 = await asyncio.wait_for(queue1.get(), timeout=0.1)
    assert event1.message == "Job 1 event"

    # Queue 2 should have 1 event
    event2 = await asyncio.wait_for(queue2.get(), timeout=0.1)
    assert event2.message == "Job 2 event"

    # Queue 3 should be empty
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(queue3.get(), timeout=0.1)


@pytest.mark.asyncio
async def test_registry_reuse_warning():
    """Test that registering same job twice returns existing queue."""
    registry = EventQueueRegistry()

    queue1 = await registry.register("job-123")
    queue2 = await registry.register("job-123")

    # Should be the same queue
    assert queue1 is queue2
