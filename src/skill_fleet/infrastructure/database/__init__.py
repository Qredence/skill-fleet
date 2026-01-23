"""
Database layer (migrated from db/).

This package provides database models, connection management,
and repositories for the skills fleet system.

Re-exports from skill_fleet.db during migration period.
"""

from __future__ import annotations

# Re-export from existing db/ during migration
from skill_fleet.db import (
    AsyncSessionLocal,
    JobRepository,
    SessionLocal,
    SkillRepository,
    TaxonomyRepository,
    UsageRepository,
    ValidationRepository,
    async_engine,
    engine,
    get_async_db,
    get_db,
    get_db_context,
    get_job_repository,
    get_skill_repository,
    get_taxonomy_repository,
    get_usage_repository,
    get_validation_repository,
    init_db,
)

__all__ = [
    # Database connection
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db",
    "get_async_db",
    "get_db_context",
    "init_db",
    # Repositories
    "SkillRepository",
    "JobRepository",
    "TaxonomyRepository",
    "ValidationRepository",
    "UsageRepository",
    "get_skill_repository",
    "get_job_repository",
    "get_taxonomy_repository",
    "get_validation_repository",
    "get_usage_repository",
]
