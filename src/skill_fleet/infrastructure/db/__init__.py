"""
Skills-Fleet Database Module.

This module provides database models, connection management,
and repositories for the skills fleet system.
"""

from .database import (
    get_async_db,
    get_database_state,
    get_db,
    get_db_context,
    init_database,
    init_db,
)
from .repositories import (
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
    # Database connection and initialization
    "init_database",
    "get_database_state",
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
