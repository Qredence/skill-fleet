"""
In-memory registry for workflow event queues.

Maps active job_id -> event queue for real-time streaming to SSE endpoints.
Event queues are created when workflows start and cleaned up when they complete.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from skill_fleet.core.workflows.streaming import WorkflowEvent

logger = logging.getLogger(__name__)


class EventQueueRegistry:
    """
    Global registry for workflow event queues.

    Enables SSE endpoints to subscribe to workflow events by job_id
    without tight coupling to workflow instances.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._queues: dict[str, asyncio.Queue[WorkflowEvent]] = {}
        self._lock = asyncio.Lock()

    async def register(self, job_id: str) -> asyncio.Queue[WorkflowEvent]:
        """
        Register a new event queue for a job.

        Args:
            job_id: Job identifier

        Returns:
            Event queue for the job

        """
        async with self._lock:
            if job_id in self._queues:
                logger.warning(f"Event queue already exists for job {job_id}, reusing")
                return self._queues[job_id]

            queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
            self._queues[job_id] = queue
            logger.info(f"Registered event queue for job {job_id}")
            return queue

    async def get(self, job_id: str) -> asyncio.Queue[WorkflowEvent] | None:
        """
        Get event queue for a job.

        Args:
            job_id: Job identifier

        Returns:
            Event queue if found, None otherwise

        """
        async with self._lock:
            return self._queues.get(job_id)

    async def unregister(self, job_id: str) -> bool:
        """
        Unregister event queue for a job.

        Args:
            job_id: Job identifier

        Returns:
            True if unregistered, False if not found

        """
        async with self._lock:
            if job_id in self._queues:
                del self._queues[job_id]
                logger.info(f"Unregistered event queue for job {job_id}")
                return True
            return False

    async def cleanup_expired(self, max_age_seconds: int = 3600, job_manager: Any = None) -> int:
        """
        Clean up event queues for completed or expired jobs.

        Args:
            max_age_seconds: Maximum age for inactive queues
            job_manager: JobManager instance for status checks

        Returns:
            Number of queues cleaned up

        """
        # This is a placeholder for future background cleanup task
        # For now, we rely on manual unregister calls after workflow completion
        return 0


# Global registry instance
_event_registry: EventQueueRegistry | None = None


def get_event_registry() -> EventQueueRegistry:
    """
    Get the global event registry instance.

    Returns:
        EventQueueRegistry instance

    """
    global _event_registry
    if _event_registry is None:
        _event_registry = EventQueueRegistry()
        logger.info("Created EventQueueRegistry")
    return _event_registry
