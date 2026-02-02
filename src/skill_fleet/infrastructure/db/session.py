"""
Database session management.

Provides context managers for handling database sessions, particularly
short-lived transactional sessions to avoid idle-in-transaction timeouts
during long-running operations.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session

from .database import SessionLocal


@contextmanager
def transactional_session() -> Generator[Session, None, None]:
    """
    Context manager for short-lived database transactions.

    Ensures that a session is created, used, committed (or rolled back on error),
    and closed promptly. Use this for all database operations within workflows
    to prevent holding connections open during long LLM calls.

    Usage:
        with transactional_session() as db:
            job = JobRepository(db).get_by_id(job_id)
            job.status = "processing"
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
