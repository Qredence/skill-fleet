"""
FastAPI lifespan management for job persistence.

Handles:
1. Initialization of JobManager with database backing at startup
2. Background cleanup task to remove expired jobs from memory cache
3. Graceful shutdown
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi import FastAPI

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager for startup/shutdown.

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

    import dspy

    from ..infrastructure.db.database import init_database, init_db
    from ..infrastructure.db.repositories import JobRepository
    from ..infrastructure.db.session import transactional_session
    from .config import get_settings
    from .services.job_manager import initialize_job_manager

    settings = get_settings()

    try:
        # Configure DSPy globally for the API
        logger.info("Configuring DSPy LM and caching...")
        try:
            from ..infrastructure.tracing.config import ConfigModelLoader

            loader = ConfigModelLoader()
            lm = loader.get_model_for_task("conversational_agent")
            dspy.configure(lm=lm)

            # Configure DSPy caching from config.yaml for improved performance
            loader.configure_cache()
            logger.info("✅ DSPy configured successfully with caching enabled")

            # Store loader on app state for later use
            app.state.lm_loader = loader
        except ValueError as e:
            logger.error(f"Failed to configure DSPy: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            raise

        # Configure MLflow if enabled
        if settings.mlflow_enabled:
            logger.info("Configuring MLflow DSPy autologging...")
            try:
                from ..infrastructure.monitoring.mlflow_setup import setup_dspy_autologging

                enabled = setup_dspy_autologging(
                    tracking_uri=settings.mlflow_tracking_uri,
                    experiment_name=settings.mlflow_experiment_name,
                )
                if enabled:
                    logger.info(
                        f"✅ MLflow DSPy autologging enabled (experiment: {settings.mlflow_experiment_name})"
                    )
                else:
                    logger.warning(
                        "MLflow DSPy autologging not enabled. See earlier warning logs for details."
                    )
            except Exception as e:
                logger.warning(f"MLflow DSPy autologging setup failed: {e}")

        # Initialize database engines and sessions
        logger.info("Initializing database engines...")
        db_state = init_database()
        app.state.db = db_state
        logger.info("✅ Database engines initialized")

        # Initialize database tables
        logger.info("Creating database tables...")
        init_db()
        logger.info("✅ Database tables created/verified")

        # Initialize JobManager with database backing (no persistent session)
        initialize_job_manager()
        logger.info("✅ JobManager initialized with database persistence")

        # Store JobManager on app state for dependency injection
        from .services.job_manager import get_job_manager

        app.state.job_manager = get_job_manager()
        logger.info("✅ JobManager registered for dependency injection")

        # Resume any pending jobs from database using a short-lived session
        with transactional_session() as db:
            job_repo = JobRepository(db)
            pending_jobs = job_repo.get_by_status("pending")
            running_jobs = job_repo.get_by_status("running")
            pending_hitl_jobs = job_repo.get_by_status("pending_hitl")

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
        try:
            cleanup_task.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup_task
            logger.info("✓ Cleanup task cancelled")
        except Exception as e:
            logger.error(f"✗ Failed to cancel cleanup task: {e}")

        # Close database connections
        try:
            from ..infrastructure.db.database import close_async_db, close_db

            close_db()
            await close_async_db()
            logger.info("✓ Database connections closed")
        except Exception as e:
            logger.error(f"✗ Failed to close database: {e}")

        logger.info("Shutdown complete")


async def _cleanup_expired_jobs() -> None:
    """
    Background task: Periodically clean up expired jobs from memory cache.

    Runs every 5 minutes. Removes jobs from memory that are older than the
    TTL (default: 60 minutes). These jobs remain in the database for durability.
    """
    from .services.job_manager import get_job_manager

    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            manager = get_job_manager()
            cleaned = await manager.cleanup_expired()

            if cleaned > 0:
                logger.info(f"🧹 Cleaned {cleaned} expired job(s) from memory cache")

        except asyncio.CancelledError:
            logger.debug("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Error in cleanup task: {e}", exc_info=True)
            # Continue on errors - cleanup is non-critical
