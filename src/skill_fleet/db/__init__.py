"""
Skills-Fleet Database Module.

This module provides database models, connection management,
and repositories for the skills fleet system.
"""

from skill_fleet.db.database import (
    AsyncSessionLocal,
    SessionLocal,
    async_engine,
    engine,
    get_async_db,
    get_db,
    get_db_context,
    init_db,
)
from skill_fleet.db.repositories import (
    JobRepository,
    SkillRepository,
    TaxonomyRepository,
    UsageRepository,
    ValidationRepository,
    get_job_repository,
    get_skill_repository,
    get_taxonomy_repository,
    get_usage_repository,
    get_validation_repository,
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
