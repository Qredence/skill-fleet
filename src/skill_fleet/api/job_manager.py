"""
Job lifecycle management with dual-layer persistence (memory + database).

This module provides the JobManager facade that coordinates job state
across both in-memory cache (hot, fast) and database (durable, multi-instance).

Architecture:
    Memory Layer    -> Fast cache for in-flight jobs (<1 hour old)
    Database Layer  -> Source of truth for all job history
    JobManager      -> Coordinates between both layers
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from sqlalchemy.orm import Session

    from ..db.repositories import JobRepository

from .schemas import DeepUnderstandingState, JobState, TDDWorkflowState


def _sanitize_for_log(value: Any) -> str:
    """Remove newline characters from values before logging to prevent log injection."""
    text = str(value)
    return text.replace("\r", "").replace("\n", "")


def _sanitize_for_log(value: str) -> str:
    """
    Make a string safe for single-line log messages by removing line breaks.

    This helps prevent log injection via user-controlled values that may
    contain newline characters.
    """
    if value is None:
        return ""
    # Replace CR and LF characters with spaces to preserve readability
    return value.replace("\r", " ").replace("\n", " ")


logger = logging.getLogger(__name__)

# Valid job status values for validation
VALID_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}


class JobMemoryStore:
    """
    Hot cache for in-flight jobs.

    Stores recently created/active jobs in memory for fast access.
    Automatically expires entries older than TTL.
    """

    def __init__(self, ttl_minutes: int = 60):
        """
        Initialize memory store.

        Args:
            ttl_minutes: Time-to-live for cached jobs (default: 60 minutes)

        """
        self.ttl_minutes = ttl_minutes
        self.store: dict[str, tuple[JobState, datetime]] = {}

    def set(self, job_id: str, job: JobState) -> None:
        """
        Store job in memory with timestamp.

        Args:
            job_id: Job identifier
            job: JobState instance

        """
        self.store[job_id] = (job, datetime.now(UTC))

    def get(self, job_id: str) -> JobState | None:
        """
        Get job from memory if not expired.

        Args:
            job_id: Job identifier

        Returns:
            JobState if found and not expired, None otherwise

        """
        if job_id not in self.store:
            return None

        job, created_at = self.store[job_id]
        age = datetime.now(UTC) - created_at

        if age > timedelta(minutes=self.ttl_minutes):
            # Expired: remove from memory
            del self.store[job_id]
            logger.debug(f"Job {job_id} expired from memory cache (age: {age})")
            return None

        return job

    def delete(self, job_id: str) -> bool:
        """
        Remove job from memory.

        Args:
            job_id: Job identifier

        Returns:
            True if job was deleted, False if not found

        """
        if job_id in self.store:
            del self.store[job_id]
            return True
        return False

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Should be called periodically by background task.

        Returns:
            Number of jobs removed

        """
        expired_ids = [
            job_id
            for job_id, (_, created_at) in self.store.items()
            if datetime.now(UTC) - created_at > timedelta(minutes=self.ttl_minutes)
        ]

        for job_id in expired_ids:
            del self.store[job_id]

        return len(expired_ids)

    def clear(self) -> int:
        """
        Clear all entries from memory.

        Returns:
            Number of jobs cleared

        """
        count = len(self.store)
        self.store.clear()
        return count


class JobManager:
    """
    Manage job lifecycle across memory and database layers.

    Provides unified interface for:
    - Creating new jobs
    - Retrieving jobs (memory first, DB fallback)
    - Updating job state
    - Persisting to database
    """

    def __init__(self, memory_store: JobMemoryStore | None = None, db_session_factory=None):
        """
        Initialize job manager.

        Args:
            memory_store: Optional JobMemoryStore instance
            db_session_factory: Optional SQLAlchemy session factory for async DB operations

        """
        self.memory = memory_store or JobMemoryStore(ttl_minutes=60)
        self.db_repo: JobRepository | None = None
        self.db_session_factory = db_session_factory

    def set_db_repo(self, db_repo: JobRepository) -> None:
        """
        Set database repository (call at API startup).

        Args:
            db_repo: JobRepository instance

        """
        self.db_repo = db_repo
        logger.info("JobManager database repository configured")

    def set_db_session_factory(
        self, factory: async_sessionmaker[Any] | Callable[[], Session] | None
    ) -> None:
        """
        Set database session factory for async operations.

        Args:
            factory: SQLAlchemy AsyncSessionLocal or SessionLocal factory

        """
        self.db_session_factory = factory
        logger.debug("JobManager database session factory configured")

    def get_job(self, job_id: str) -> JobState | None:
        """
        Retrieve job from memory (fast), fall back to DB (durable).

        Implements two-tier lookup:
        1. Check memory cache first (fastest)
        2. Fall back to database (durable)
        3. Warm memory cache on DB hit

        Args:
            job_id: Job identifier

        Returns:
            JobState if found, None otherwise

        """
        safe_job_id = _sanitize_for_log(job_id)
        # Try memory first (hot cache, no I/O)
        job = self.memory.get(job_id)
        if job:
            logger.debug(f"Job {safe_job_id} retrieved from memory cache")
            return job

        # Fall back to database
        if self.db_repo:
            try:
                db_job = self.db_repo.get_by_id(UUID(job_id))
                if db_job:
                    # Reconstruct JobState from DB model
                    job_state = self._db_to_memory(db_job)
                    # Double-check not already added by another thread/routine
                    if not self.memory.get(job_id):
                        self.memory.set(job_id, job_state)
                    logger.info(f"Job {safe_job_id} loaded from database and cached")
                    return job_state
            except ValueError as e:
                logger.warning(f"Invalid UUID for job {safe_job_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading job {safe_job_id} from database: {e}")

        logger.warning(f"Job {safe_job_id} not found in memory or database")
        return None

    def create_job(self, job_state: JobState) -> None:
        """
        Create a new job (memory + DB).

        Stores job in both layers:
        - Memory: immediate, for fast access
        - Database: for durability and multi-instance access

        Args:
            job_state: JobState instance

        """
        # Store in memory immediately (fast)
        self.memory.set(job_state.job_id, job_state)
        safe_job_id = _sanitize_for_log(job_state.job_id)
        logger.debug(f"Job {safe_job_id} stored in memory")

        # Persist to DB
        if self.db_repo:
            try:
                self._save_job_to_db(job_state)
                logger.info(f"Job {safe_job_id} created (memory + database)")
            except Exception as e:
                logger.error(f"Failed to create job {safe_job_id} in database: {e}")
                # Continue - memory store is still usable
        else:
            logger.warning(f"Job {safe_job_id} created (memory only, no database backing)")

    def update_job(self, job_id: str, updates: dict[str, Any]) -> JobState | None:
        """
        Update job in both layers.

        Updates both memory cache and database:
        - Memory: for immediate visibility
        - Database: for persistence

        safe_job_id = _sanitize_for_log(job_id)

        Args:
            job_id: Job identifier
            updates: Dictionary of fields to update

        Returns:
            Updated JobState if successful, None otherwise

        """
        # Try to get from memory first
        job = self.memory.get(job_id)

        # If not in memory, try database
        if not job:
            job = self.get_job(job_id)

        if not job:
            logger.error(f"Cannot update: job {safe_job_id} not found")
            return None

        # Apply updates
        for key, value in updates.items():
            if hasattr(job, key):
                setattr(job, key, value)

        # Update memory first (always succeeds)
        self.memory.set(job_id, job)
        logger.debug(f"Job {safe_job_id} updated in memory")

        # Attempt DB update with explicit failure handling
        if self.db_repo:
            try:
                self._save_job_to_db(job)
                logger.debug(f"Job {safe_job_id} updated in database")
            except ValueError as e:
                logger.error(f"Validation failed updating job {safe_job_id}: {e}")
                # Consider rolling back memory update or marking as dirty
            except Exception as e:
                logger.error(f"Database error updating job {safe_job_id}: {e}")
                # Memory update succeeded but DB failed - log discrepancy

        return job

    def save_job(self, job: JobState) -> bool:
        """
        Explicit save to database (for completed/important jobs).

        Args:
            job: JobState to save

        Returns:
            True if save succeeded, False otherwise

        """
        safe_job_id = _sanitize_for_log(job.job_id)
        self.memory.set(job.job_id, job)

        if self.db_repo:
            try:
                self._save_job_to_db(job)
                logger.info(f"Job {safe_job_id} explicitly saved to database")
                return True
            except Exception as e:
                logger.error(f"Failed to save job {safe_job_id}: {e}")
                return False

        return True

    def delete_job(self, job_id: str) -> bool:
        """
        Delete job from memory (database deletion TBD).

        Args:
            job_id: Job identifier

        Returns:
            True if deleted from memory, False otherwise

        """
        return self.memory.delete(job_id)

    def cleanup_expired(self) -> int:
        """
        Clean up expired memory entries.

        Should be called periodically by background task.

        Returns:
            Number of jobs cleaned up

        """
        return self.memory.cleanup_expired()

    # Private methods

    def _save_job_to_db(self, job: JobState) -> None:
        """
        Internal: Save JobState to database.

        Serializes JobState fields and performs upsert to database.

        Args:
            job: JobState to save

        Raises:
            ValueError: If job status is invalid
            Exception: If database operation fails

        """
        if not self.db_repo:
            return

        # Validate status before saving
        if job.status not in VALID_STATUSES:
            raise ValueError(f"Invalid job status: {job.status}. Must be one of {VALID_STATUSES}")

        try:
            # Build job data for database
            job_data = {
                "job_id": UUID(job.job_id),
                "status": job.status,
                "task_description": getattr(job, "task_description", ""),
                "progress_percent": getattr(job, "progress_percent", 0.0),
                "result": self._serialize_json(job.result),
                "error": job.error,
                "error_stack": getattr(job, "error_stack", None),
                "progress_message": getattr(job, "progress_message", None),
                "current_phase": getattr(job, "current_phase", None),
                "updated_at": job.updated_at or datetime.now(UTC),
                "started_at": getattr(job, "started_at", None),
                "completed_at": getattr(job, "completed_at", None),
            }

            # Filter out None values for optional fields
            job_data = {
                k: v for k, v in job_data.items() if v is not None or k in ["error", "error_stack"]
            }

            # Try to fetch existing job
            existing = self.db_repo.get_by_id(UUID(job.job_id))
            if existing:
                self.db_repo.update(db_obj=existing, obj_in=job_data)
                logger.debug(f"Job {job.job_id} updated in database")
            else:
                self.db_repo.create(obj_in=job_data)
                logger.debug(f"Job {job.job_id} created in database")
        except Exception as e:
            logger.error(f"Database upsert failed for job {job.job_id}: {e}")
            raise

    def _serialize_json(self, obj: Any) -> dict | None:
        """
        Serialize an object to JSON-compatible dict.

        Args:
            obj: Object to serialize

        Returns:
            JSON-compatible dict or None

        """
        if obj is None:
            return None
        try:
            # Use Pydantic model_dump for model instances
            if hasattr(obj, "model_dump"):
                return obj.model_dump(mode="json")
            # Fallback to JSON serialization
            return json.loads(json.dumps(obj, default=str))
        except Exception as e:
            logger.warning(f"Failed to serialize object: {e}")
            return {}

    def _db_to_memory(self, db_job: Any) -> JobState:
        """
        Internal: Reconstruct JobState from database model.

        Args:
            db_job: Job database model instance

        Returns:
            JobState instance

        """
        job_id = str(db_job.job_id)
        job_state = JobState(job_id=job_id)

        # Set basic fields (handle all optional attributes safely)
        job_state.status = getattr(db_job, "status", "pending")
        job_state.result = getattr(db_job, "result", None)
        job_state.error = getattr(db_job, "error", None)
        job_state.updated_at = getattr(db_job, "updated_at", None) or datetime.now(UTC)

        # Restore nested state objects if present
        if hasattr(db_job, "deep_understanding_state") and db_job.deep_understanding_state:
            try:
                deep_state = db_job.deep_understanding_state
                job_state.deep_understanding = DeepUnderstandingState(
                    questions_asked=getattr(deep_state, "questions_asked", []),
                    answers=getattr(deep_state, "answers", []),
                    research_performed=getattr(deep_state, "research_performed", []),
                    understanding_summary=getattr(deep_state, "understanding_summary", "") or "",
                    user_problem=getattr(deep_state, "user_problem", "") or "",
                    readiness_score=getattr(deep_state, "readiness_score", 0.0),
                    complete=getattr(deep_state, "complete", False),
                )
            except Exception as e:
                logger.warning(f"Failed to restore deep_understanding for {job_id}: {e}")

        if hasattr(db_job, "tdd_workflow_state") and db_job.tdd_workflow_state:
            try:
                tdd_state = db_job.tdd_workflow_state
                job_state.tdd_workflow = TDDWorkflowState(
                    phase=getattr(tdd_state, "phase", None),
                    baseline_tests_run=getattr(tdd_state, "baseline_tests_run", False),
                    compliance_tests_run=getattr(tdd_state, "compliance_tests_run", False),
                    rationalizations_identified=getattr(
                        tdd_state, "rationalizations_identified", []
                    ),
                )
            except Exception as e:
                logger.warning(f"Failed to restore tdd_workflow for {job_id}: {e}")

        # Reinitialize asyncio objects (not serialized)
        job_state.hitl_event = asyncio.Event()
        job_state.hitl_lock = asyncio.Lock()

        return job_state


# Global instance
_job_manager: JobManager | None = None


def get_job_manager() -> JobManager:
    """
    Get the global job manager instance.

    Returns:
        JobManager instance (creates default if not initialized)

    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
        logger.info("Created default JobManager (no database backing)")
    return _job_manager


def initialize_job_manager(db_repo: JobRepository) -> JobManager:
    """
    Initialize job manager with database repo (call at API startup).

    Args:
        db_repo: JobRepository instance for database access

    Returns:
        Initialized JobManager instance

    """
    global _job_manager
    _job_manager = JobManager()
    _job_manager.set_db_repo(db_repo)
    logger.info("JobManager initialized with database persistence")
    return _job_manager
