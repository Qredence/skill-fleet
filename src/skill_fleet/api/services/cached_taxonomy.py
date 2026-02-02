"""
Cached taxonomy service wrapper for performance optimization.

This module provides cached versions of frequently accessed taxonomy operations,
improving API response times for read-heavy operations.

Cache Configuration:
- TTL: 5 minutes (300 seconds) for most data
- Invalidate on skill creation/update
- Pattern-based invalidation support

Usage:
    >>> from skill_fleet.api.services.cached_taxonomy import cached_taxonomy_service
    >>>
    >>> # Get global taxonomy (cached)
    >>> taxonomy = cached_taxonomy_service.get_global_taxonomy()
    >>>
    >>> # Get user taxonomy (cached)
    >>> user_taxonomy = cached_taxonomy_service.get_user_taxonomy(user_id)
    >>>
    >>> # Invalidate taxonomy caches
    >>> cached_taxonomy_service.invalidate_taxonomy()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from skill_fleet.api.cache import (
    cache_key,
    get_cache,
    invalidate_pattern,
)

if TYPE_CHECKING:
    from skill_fleet.taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: Any) -> str:
    """
    Sanitize a value for safe inclusion in log messages.

    Removes newline and carriage return characters to mitigate log injection.
    """
    text = str(value)
    return text.replace("\r", "").replace("\n", "")


class CachedTaxonomyService:
    """
    Cached wrapper for TaxonomyManager operations.

    Provides caching for expensive taxonomy operations like global taxonomy
    retrieval, user taxonomy lookups, and branch finding.
    """

    def __init__(self, taxonomy_manager: TaxonomyManager):
        """
        Initialize the cached taxonomy service.

        Args:
            taxonomy_manager: The underlying TaxonomyManager instance

        """
        self.taxonomy_manager = taxonomy_manager

    async def get_global_taxonomy(self) -> dict[str, Any]:
        """
        Get the global taxonomy structure with caching.

        Returns:
            Dictionary with taxonomy structure, domains, and metadata

        """
        cache_key_val = cache_key("taxonomy", "global")

        # Try cache first
        cached = await get_cache().get(cache_key_val)
        if cached is not None:
            logger.debug("Cache hit: global taxonomy")
            return cached

        # Get from taxonomy manager
        logger.debug("Cache miss: global taxonomy")
        taxonomy_meta = self.taxonomy_manager.meta

        result = {
            "structure": taxonomy_meta.get("taxonomy", {}),
            "domains": taxonomy_meta.get("domains", []),
            "categories": list(taxonomy_meta.get("taxonomy", {}).keys()),
            "total_skills": len(self.taxonomy_manager.metadata_cache),
            "last_updated": taxonomy_meta.get("last_updated"),
        }

        # Cache for 5 minutes
        await get_cache().set(cache_key_val, result, ttl=300)

        return result

    async def get_user_taxonomy(self, user_id: str) -> dict[str, Any]:
        """
        Get user-specific taxonomy with caching.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with mounted skills and adapted taxonomy

        """
        cache_key_val = cache_key("taxonomy", "user", user_id)

        # Try cache first
        cached = await get_cache().get(cache_key_val)
        if cached is not None:
            safe_user_id = _sanitize_for_log(user_id)
            logger.debug(f"Cache hit: user taxonomy for {safe_user_id}")
            return cached

        # Get from taxonomy manager
        safe_user_id = _sanitize_for_log(user_id)
        logger.debug(f"Cache miss: user taxonomy for {safe_user_id}")
        mounted_skills = self.taxonomy_manager.get_mounted_skills(user_id)
        taxonomy_meta = self.taxonomy_manager.meta
        global_taxonomy = taxonomy_meta.get("taxonomy", {})

        result = {
            "global_structure": global_taxonomy,
            "mounted_skills": mounted_skills,
            "user_id": user_id,
        }

        # Identify adapted categories
        adapted_categories = []
        for skill_path in mounted_skills:
            parts = skill_path.split("/")
            if len(parts) > 0:
                domain = parts[0]
                if domain not in adapted_categories:
                    adapted_categories.append(domain)

        result["adapted_categories"] = adapted_categories

        # Cache for 2 minutes (user-specific data changes more frequently)
        await get_cache().set(cache_key_val, result, ttl=120)

        return result

    async def get_relevant_branches(self, task_description: str) -> dict[str, dict[str, str]]:
        """
        Get relevant taxonomy branches for a task with caching.

        Args:
            task_description: Task description to match against

        Returns:
            Dictionary of relevant taxonomy branches

        """
        # Create a cache key based on task description hash
        from skill_fleet.api.cache import hash_key

        key_hash = hash_key(task_description)
        cache_key_val = cache_key("taxonomy", "branches", key_hash)

        # Try cache first
        cached = await get_cache().get(cache_key_val)
        if cached is not None:
            logger.debug("Cache hit: relevant branches for task")
            return cached

        # Get from taxonomy manager
        logger.debug("Cache miss: relevant branches for task")
        result = self.taxonomy_manager.get_relevant_branches(task_description)

        # Cache for 10 minutes (task descriptions often repeat)
        await get_cache().set(cache_key_val, result, ttl=600)

        return result

    async def get_skill_metadata_cached(self, skill_id: str) -> dict[str, Any] | None:
        """
        Get skill metadata with caching.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill metadata dict or None if not found

        """
        cache_key_val = cache_key("skill", "metadata", skill_id)

        # Try cache first
        cached = await get_cache().get(cache_key_val)
        if cached is not None:
            logger.debug(f"Cache hit: skill metadata for {skill_id}")
            return cached

        # Get from taxonomy manager
        logger.debug(f"Cache miss: skill metadata for {skill_id}")
        meta = self.taxonomy_manager.get_skill_metadata(skill_id)
        if meta is None:
            return None

        from ...taxonomy.metadata import SkillMetadata

        if isinstance(meta, SkillMetadata):
            result = {
                "skill_id": meta.skill_id,
                "name": meta.name,
                "description": meta.description,
                "version": meta.version,
                "type": meta.type,
                "path": str(meta.path) if meta.path else None,
                "weight": meta.weight,
                "load_priority": meta.load_priority,
                "dependencies": meta.dependencies,
                "capabilities": meta.capabilities,
                "always_loaded": meta.always_loaded,
            }
        else:
            result = {
                "skill_id": meta.get("skill_id") if meta else None,
                "name": meta.get("name") if meta else None,
                "description": meta.get("description") if meta else None,
                "version": meta.get("version") if meta else None,
                "type": meta.get("type") if meta else None,
            }

        # Cache for 5 minutes
        await get_cache().set(cache_key_val, result, ttl=300)

        return result

    async def invalidate_taxonomy(self) -> int:
        """
        Invalidate all taxonomy-related cache entries.

        Returns:
            Number of cache entries invalidated

        """
        count = await invalidate_pattern("taxonomy:*")
        logger.info(f"Invalidated {count} taxonomy cache entries")
        return count

    async def invalidate_skill(self, skill_id: str) -> int:
        """
        Invalidate cache entries for a specific skill.

        Args:
            skill_id: Skill identifier

        Returns:
            Number of cache entries invalidated

        """
        # Invalidate skill metadata
        count = await invalidate_pattern(f"skill:*:{skill_id}*")

        # Also invalidate any user taxonomies that might reference this skill
        count += await invalidate_pattern("taxonomy:user:*")

        logger.info(f"Invalidated {count} cache entries for skill {skill_id}")
        return count

    async def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics

        """
        return await get_cache().get_stats()


# Global instance getter
_cached_service: CachedTaxonomyService | None = None


def get_cached_taxonomy_service(taxonomy_manager: TaxonomyManager) -> CachedTaxonomyService:
    """
    Get or create the cached taxonomy service.

    Args:
        taxonomy_manager: The underlying TaxonomyManager

    Returns:
        CachedTaxonomyService instance

    """
    global _cached_service
    if _cached_service is None or _cached_service.taxonomy_manager is not taxonomy_manager:
        _cached_service = CachedTaxonomyService(taxonomy_manager)
    return _cached_service


__all__ = [
    "CachedTaxonomyService",
    "get_cached_taxonomy_service",
]
