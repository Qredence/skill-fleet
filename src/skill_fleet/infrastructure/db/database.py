"""
Skills-Fleet Database Connection.

Database connection and session management for the skills fleet database.
"""

import os
from collections.abc import AsyncGenerator
from collections.abc import Generator as SyncGenerator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import CheckConstraint, Engine, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


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


@dataclass
class _DatabaseState:
    """Holds database engine and session factory instances."""

    engine: Engine
    session_factory: sessionmaker
    async_engine: AsyncEngine
    async_session_factory: async_sessionmaker
    database_url: str
    async_database_url: str
    is_sqlite: bool


# Module-level state holder (initialized by init_database)
_state: _DatabaseState | None = None


def init_database(
    database_url: str | None = None,
    env: str | None = None,
) -> _DatabaseState:
    """
    Initialize database engines and session factories.

    Must be called before any database operations. Safe to call multiple times
    (will recreate engines).

    Args:
        database_url: Database URL. If None, reads from DATABASE_URL env var.
        env: Environment name. If None, reads from SKILL_FLEET_ENV env var.

    Returns:
        The initialized database state.

    Raises:
        ValueError: If database_url is None and DATABASE_URL env var is not set
                   in production environment.

    """
    global _state

    # Read environment
    raw_database_url = database_url or os.getenv("DATABASE_URL")
    _env = env or os.getenv("SKILL_FLEET_ENV", "production")

    if not raw_database_url:
        if _env in ("development", "test", "testing"):
            # Use SQLite for development/testing if no DATABASE_URL is provided
            raw_database_url = "sqlite:///./skill_fleet_dev.db"
        else:
            raise ValueError(
                "DATABASE_URL environment variable is required in production. "
                "Set it to a PostgreSQL connection string, e.g.: "
                "postgresql://user:pass@host/dbname?sslmode=require"
            )

    # Use psycopg (v3) for sync engine when driver isn't specified
    sync_database_url = _with_postgres_driver(raw_database_url, "psycopg")

    # Async database URL (derive from raw unless explicitly set)
    async_database_url = os.getenv("ASYNC_DATABASE_URL")
    if not async_database_url:
        if raw_database_url.startswith("sqlite"):
            # SQLite async uses aiosqlite driver
            async_database_url = raw_database_url.replace("sqlite:", "sqlite+aiosqlite:")
        else:
            async_database_url = _with_postgres_driver(raw_database_url, "asyncpg", override=True)

    # Check if we're using SQLite (different engine configuration)
    is_sqlite = sync_database_url.startswith("sqlite")

    # Configure connection args
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    if not is_sqlite:
        connect_args.update(
            {
                "connect_timeout": 10,
                "options": "-c idle_in_transaction_session_timeout=60000",  # 60s timeout
            }
        )

    # Create synchronous engine
    engine = create_engine(
        sync_database_url,
        pool_pre_ping=bool(not is_sqlite),
        pool_size=20 if not is_sqlite else 0,
        max_overflow=30 if not is_sqlite else 0,
        pool_recycle=300 if not is_sqlite else -1,
        pool_timeout=30,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        connect_args=connect_args,
    )

    # Create synchronous session factory
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    # Create async engine
    async_engine = create_async_engine(
        async_database_url,
        pool_pre_ping=bool(not is_sqlite),
        pool_size=10 if not is_sqlite else 0,
        max_overflow=20 if not is_sqlite else 0,
        pool_recycle=300 if not is_sqlite else -1,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )

    # Create async session factory
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    _state = _DatabaseState(
        engine=engine,
        session_factory=session_factory,
        async_engine=async_engine,
        async_session_factory=async_session_factory,
        database_url=sync_database_url,
        async_database_url=async_database_url,
        is_sqlite=is_sqlite,
    )

    return _state


def get_database_state() -> _DatabaseState:
    """
    Get the current database state.

    Returns:
        The initialized database state.

    Raises:
        RuntimeError: If init_database() has not been called yet.

    """
    if _state is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() before using database operations."
        )
    return _state


def get_db() -> SyncGenerator[Session, None, None]:
    """
    Get a database session for dependency injection.

    Usage:
        @app.get("/skills")
        def read_skills(db: Session = Depends(get_db)):
            return db.query(Skill).all()
    """
    state = get_database_state()
    db = state.session_factory()
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
    state = get_database_state()
    db = state.session_factory()
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
    state = get_database_state()
    async with state.async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    state = get_database_state()

    if state.is_sqlite:
        for table in Base.metadata.tables.values():
            regex_constraints = [
                constraint
                for constraint in table.constraints
                if isinstance(constraint, CheckConstraint) and "~" in str(constraint.sqltext)
            ]
            for constraint in regex_constraints:
                table.constraints.remove(constraint)

    # Ensure uuid-ossp extension exists (Postgres only)
    if not state.is_sqlite:
        with state.engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            conn.commit()

    Base.metadata.create_all(bind=state.engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    """
    state = get_database_state()

    # Drop dependent views/materialized views first
    with state.engine.connect() as conn:
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

    Base.metadata.drop_all(bind=state.engine)


async def init_async_db() -> None:
    """
    Initialize the async database by creating all tables.

    This should only be used for development. In production,
    use Alembic migrations instead.
    """
    state = get_database_state()
    async with state.async_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(Base.metadata.create_all)


async def drop_async_db() -> None:
    """
    Drop all async database tables.

    WARNING: This will delete all data!
    """
    state = get_database_state()
    async with state.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def close_db() -> None:
    """Close the database connection."""
    if _state is not None:
        _state.engine.dispose()


async def close_async_db() -> None:
    """Close the async database connection."""
    if _state is not None:
        await _state.async_engine.dispose()
