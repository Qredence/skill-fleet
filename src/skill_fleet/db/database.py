"""
Skills-Fleet Database Connection

Database connection and session management for the skills fleet database.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from skill_fleet.db.models import Base

# Database URL from environment or default
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://neondb_owner:your_password@ep-something.aws.us-east-1.aws.neon.tech/neondb?sslmode=require'
)

# Async database URL (convert postgresql:// to postgresql+asyncpg://)
ASYNC_DATABASE_URL = os.getenv(
    'ASYNC_DATABASE_URL',
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
)

# Synchronous engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv('SQL_ECHO', 'false').lower() == 'true',
)

# Synchronous session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Async engine
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv('SQL_ECHO', 'false').lower() == 'true',
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection.

    Usage:
        @app.get("/skills")
        def read_skills(db: Session = Depends(get_db)):
            return db.query(Skill).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Usage:
        with get_db_context() as db:
            skills = db.query(Skill).all()
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


async def get_async_db() -> Generator[AsyncSession, None, None]:
    """
    Get an async database session for dependency injection.

    Usage:
        @app.get("/skills")
        async def read_skills(db: AsyncSession = Depends(get_async_db)):
            result = await db.execute(select(Skill))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_db_context_manager() -> Generator[Session, None, None]:
    """
    Alias for get_db_context() for backward compatibility.
    """
    with get_db_context() as db:
        yield db


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=engine)


async def init_async_db() -> None:
    """
    Initialize the async database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_async_db() -> None:
    """
    Drop all async database tables.

    WARNING: This will delete all data!
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def close_db() -> None:
    """Close the database connection."""
    engine.dispose()


async def close_async_db() -> None:
    """Close the async database connection."""
    await async_engine.dispose()
