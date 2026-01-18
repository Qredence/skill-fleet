"""FastAPI dependency injection for shared resources.

This module provides centralized dependency functions for FastAPI routes,
ensuring consistent configuration and enabling easier testing through
dependency overrides.

Usage:
    from fastapi import Depends
    from skill_fleet.api.dependencies import get_taxonomy_manager, get_skills_root

    @router.get("/skills")
    async def list_skills(manager: TaxonomyManager = Depends(get_taxonomy_manager)):
        return manager.list_skills()
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from ..common.paths import ensure_skills_root_initialized
from ..taxonomy.manager import TaxonomyManager


def get_skills_root() -> Path:
    """Get the configured skills root directory.

    Reads from SKILL_FLEET_SKILLS_ROOT environment variable,
    defaulting to "skills" in the current working directory.

    Returns:
        Path to the skills root directory
    """
    root = Path(os.environ.get("SKILL_FLEET_SKILLS_ROOT", "skills"))
    return ensure_skills_root_initialized(root)


def get_drafts_root(skills_root: Annotated[Path, Depends(get_skills_root)]) -> Path:
    """Get the drafts root directory.

    Args:
        skills_root: The skills root directory (injected)

    Returns:
        Path to the drafts directory (_drafts under skills root)
    """
    return skills_root / "_drafts"


@lru_cache(maxsize=1)
def _get_cached_taxonomy_manager(skills_root_str: str) -> TaxonomyManager:
    """Create and cache a TaxonomyManager instance.

    Uses string path for hashability with lru_cache.

    Args:
        skills_root_str: String path to skills root

    Returns:
        Cached TaxonomyManager instance
    """
    return TaxonomyManager(Path(skills_root_str))


def get_taxonomy_manager(
    skills_root: Annotated[Path, Depends(get_skills_root)],
) -> TaxonomyManager:
    """Get a TaxonomyManager instance for the configured skills root.

    The manager is cached per skills_root path to avoid repeated
    filesystem scans and metadata loading.

    Args:
        skills_root: The skills root directory (injected)

    Returns:
        TaxonomyManager instance for the skills root
    """
    return _get_cached_taxonomy_manager(str(skills_root.resolve()))


def clear_taxonomy_manager_cache() -> None:
    """Clear the cached TaxonomyManager instances.

    Useful for testing or when the skills directory has been modified
    externally and the cache needs to be refreshed.
    """
    _get_cached_taxonomy_manager.cache_clear()


# Type aliases for cleaner route signatures
SkillsRoot = Annotated[Path, Depends(get_skills_root)]
DraftsRoot = Annotated[Path, Depends(get_drafts_root)]
TaxonomyManagerDep = Annotated[TaxonomyManager, Depends(get_taxonomy_manager)]


__all__ = [
    "get_skills_root",
    "get_drafts_root",
    "get_taxonomy_manager",
    "clear_taxonomy_manager_cache",
    "SkillsRoot",
    "DraftsRoot",
    "TaxonomyManagerDep",
]
