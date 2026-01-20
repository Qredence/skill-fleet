"""FastAPI lifespan management for job persistence.

Handles:
1. Initialization of JobManager with database backing at startup
2. Background cleanup task to remove expired jobs from memory cache
3. Graceful shutdown
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager for startup/shutdown.

    Startup (before yield):
    - Initialize database and create tables
    - Initialize JobManager with database repository
    - Resume any pending jobs from database
    - Start background cleanup task for expired jobs

    Shutdown (after yield):
    - Cancel cleanup task
    - Close database connections
    """
    # =========================================================================
    # STARTUP
    # =========================================================================

    from .job_manager import initialize_job_manager, get_job_manager
    from ..db.database import init_db, SessionLocal
    from ..db.repositories import JobRepository

    try:
        # Initialize database tables
        logger.info("Initializing database...")
        init_db()
        logger.info("✅ Database tables created/verified")

        # Create a session and initialize JobManager with DB repo
        db_session = SessionLocal()
        job_repo = JobRepository(db_session)
        
        # Initialize JobManager with database backing
        job_manager = initialize_job_manager(job_repo)
        logger.info("✅ JobManager initialized with database persistence")

        # Resume any pending jobs from database
        pending_jobs = job_repo.get_by_status('pending')
        running_jobs = job_repo.get_by_status('running')
        pending_hitl_jobs = job_repo.get_by_status('pending_hitl')
        
        total_resumed = len(pending_jobs) + len(running_jobs) + len(pending_hitl_jobs)
        if total_resumed > 0:
            logger.info(f"📋 Resuming {total_resumed} jobs from database")
            logger.info(f"   - {len(pending_jobs)} pending")
            logger.info(f"   - {len(running_jobs)} running")
            logger.info(f"   - {len(pending_hitl_jobs)} waiting for human input")

    except Exception as e:
        logger.error(f"❌ Failed to initialize database/JobManager: {e}")
        raise

    # Start background cleanup task
    cleanup_task = asyncio.create_task(_cleanup_expired_jobs())
    logger.info("✅ Background cleanup task started (runs every 5 minutes)")

    try:
        yield  # App runs here
    finally:
        # =====================================================================
        # SHUTDOWN
        # =====================================================================

        # Cancel cleanup task
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass

        logger.info("✅ Cleanup task stopped")


async def _cleanup_expired_jobs() -> None:
    """Background task: Periodically clean up expired jobs from memory cache.

    Runs every 5 minutes. Removes jobs from memory that are older than the
    TTL (default: 60 minutes). These jobs remain in the database for durability.
    """
    from .job_manager import get_job_manager

    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            manager = get_job_manager()
            cleaned = manager.cleanup_expired()

            if cleaned > 0:
                logger.info(f"🧹 Cleaned {cleaned} expired job(s) from memory cache")

        except asyncio.CancelledError:
            logger.debug("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Error in cleanup task: {e}", exc_info=True)
            # Continue on errors - cleanup is non-critical
