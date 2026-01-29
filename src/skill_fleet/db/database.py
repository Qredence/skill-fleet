"""
Skills-Fleet Database Connection.

Database connection and session management for the skills fleet database.
"""

import os
from collections.abc import AsyncGenerator
from collections.abc import Generator as SyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from skill_fleet.db.models import Base


def _with_postgres_driver(url: str, driver: str, *, override: bool = False) -> str:
    """Ensure Postgres URLs include a DBAPI driver when appropriate."""
    if url.startswith("postgresql+"):
        if not override:
            return url
        _, rest = url.split("://", 1)
        return f"postgresql+{driver}://{rest}"
    if url.startswith("postgresql://"):
        return f"postgresql+{driver}://{url[len('postgresql://') :]}"
    if url.startswith("postgres://"):
        return f"postgresql+{driver}://{url[len('postgres://') :]}"
    return url


# Database URL from environment or default
RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:your_password@ep-something.aws.us-east-1.aws.neon.tech/neondb?sslmode=require",
)

# Use psycopg (v3) for sync engine when driver isn't specified.
DATABASE_URL = _with_postgres_driver(RAW_DATABASE_URL, "psycopg")

# Async database URL (derive from DATABASE_URL unless explicitly set).
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = _with_postgres_driver(RAW_DATABASE_URL, "asyncpg", override=True)

# Synchronous engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
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
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def get_db() -> SyncGenerator[Session, None, None]:
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
def get_db_context() -> SyncGenerator[Session, None, None]:
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


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
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
def get_db_context_manager() -> SyncGenerator[Session, None, None]:
    """Alias for get_db_context() for backward compatibility."""
    with get_db_context() as db:
        yield db


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    # Ensure uuid-ossp extension exists
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()

    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    """
    # Drop dependent views/materialized views first
    with engine.connect() as conn:
        conn.execute(text("DROP MATERIALIZED VIEW IF EXISTS skill_statistics CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS popular_skills_view CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS skills_attention_view CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS active_skills_view CASCADE"))
        conn.execute(text("DROP VIEW IF EXISTS draft_skills_view CASCADE"))

        # Manually drop all known tables in dependency order with CASCADE
        tables_to_drop = [
            "optimization_jobs",
            "usage_events",
            "skill_test_coverage",
            "validation_checks",
            "validation_reports",
            "tdd_workflow_state",
            "deep_understanding_state",
            "hitl_interactions",
            "jobs",
            "skill_allowed_tools",
            "skill_files",
            "tag_stats",
            "skill_tags",
            "skill_keywords",
            "skill_references",
            "dependency_closure",
            "skill_dependencies",
            "capabilities",
            "facet_definitions",
            "skill_facets",
            "skill_aliases",
            "skill_categories",
            "taxonomy_closure",
            "taxonomy_categories",
            "skills",
        ]

        for table in tables_to_drop:
            conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        # Drop types
        types_to_drop = [
            "skill_status_enum",
            "skill_type_enum",
            "skill_weight_enum",
            "load_priority_enum",
            "skill_style_enum",
            "dependency_type_enum",
            "job_status_enum",
            "hitl_type_enum",
            "validation_status_enum",
            "severity_enum",
            "file_type_enum",
        ]

        for type_name in types_to_drop:
            conn.execute(text(f"DROP TYPE IF EXISTS {type_name} CASCADE"))

        conn.commit()

    Base.metadata.drop_all(bind=engine)


async def init_async_db() -> None:
    """
    Initialize the async database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    async with async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
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
