"""
Caching layer for API performance optimization.

This module provides a simple in-memory cache with TTL support
that can be extended to use Redis in production environments.

Features:
- In-memory cache with configurable TTL
- Cache key generation with prefix support
- Automatic invalidation
- Thread-safe operations
- Redis-compatible interface for future migration

Usage:
    >>> from skill_fleet.api.cache import cache_manager
    >>>
    >>> # Cache a value
    >>> cache_manager.set("taxonomy:global", taxonomy_data, ttl=300)
    >>>
    >>> # Get a value
    >>> data = cache_manager.get("taxonomy:global")
    >>>
    >>> # Invalidate a cache entry
    >>> cache_manager.invalidate("taxonomy:global")
    >>>
    >>> # Clear all cache
    >>> cache_manager.clear()
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import threading
import time
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheEntry:
    """A cached value with expiration."""

    def __init__(self, value: Any, ttl: int):
        """
        Initialize a cache entry.

        Args:
            value: The cached value
            ttl: Time to live in seconds

        """
        self.value = value
        self.expires_at = time.time() + ttl

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize the in-memory cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)

        """
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0,
        }

    def get(self, key: str) -> Any | None:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired

        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["evictions"] += 1
                return None

            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)

        """
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if key was in cache, False otherwise

        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["invalidations"] += 1
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared

        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        with self._lock:
            return self._stats.copy()

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.

        Returns:
            Number of entries removed

        """
        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]

            return len(expired_keys)


# Global cache instance
_cache = InMemoryCache(default_ttl=300)  # 5 minute default TTL


def cache_key(*parts: str, prefix: str = "skill_fleet") -> str:
    """
    Generate a consistent cache key from parts.

    Args:
        *parts: Key parts to join
        prefix: Optional prefix for the key

    Returns:
        Consistent cache key string

    Examples:
        >>> cache_key("taxonomy", "global")
        'skill_fleet:taxonomy:global'
        >>> cache_key("skill", "python", "async", prefix="custom")
        'custom:skill:python:async'

    """
    key = ":".join(parts)
    if prefix:
        key = f"{prefix}:{key}"
    return key


def hash_key(value: str | dict | BaseModel) -> str:
    """
    Generate a hash key from a value.

    Useful for caching results based on input parameters.

    Args:
        value: Value to hash

    Returns:
        Hash string

    """
    if isinstance(value, BaseModel):
        value = value.model_dump_json()
    elif isinstance(value, dict):
        value = json.dumps(value, sort_keys=True)

    return hashlib.md5(value.encode(), usedforsecurity=False).hexdigest()[:16]


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Cache function results.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Prefix for cache keys

    Examples:
        >>> @cached(ttl=600, key_prefix="taxonomy")
        ... def get_taxonomy_structure():
        ...     # Expensive operation
        ...     return taxonomy_data

    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key from function name and arguments
            func_name = getattr(func, "__name__", "unknown")
            args_str = str(args) + str(sorted(kwargs.items()))
            cache_key_suffix = hash_key(args_str)
            key = cache_key(func_name, cache_key_suffix, prefix=key_prefix)

            # Try to get from cache
            result = _cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit: {key}")
                return result

            # Call function and cache result
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def cache_result(
    key_func: Callable[..., str] | None = None,
    ttl: int = 300,
    prefix: str = "",
):
    """
    Cache function results with custom key generation.

    Args:
        key_func: Optional function to generate cache key
        ttl: Time-to-live in seconds
        prefix: Prefix for cache keys

    Examples:
        >>> def get_key(user_id: str, skill_type: str) -> str:
        ...     return f"user:{user_id}:skill_type:{skill_type}"
        >>>
        >>> @cache_result(key_func=get_key, ttl=600, prefix="skills")
        ... def get_user_skills(user_id: str, skill_type: str):
        ...     return fetch_skills(user_id, skill_type)

    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key
            if key_func:
                key_suffix = key_func(*args, **kwargs)
                key = cache_key(prefix, key_suffix) if prefix else cache_key("custom", key_suffix)
            else:
                func_name = getattr(func, "__name__", "unknown")
                args_str = str(args) + str(sorted(kwargs.items()))
                key_suffix = hash_key(args_str)
                key = (
                    cache_key(func_name, key_suffix) if prefix else cache_key(func_name, key_suffix)
                )

            # Try to get from cache
            result = _cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit: {key}")
                return result

            # Call function and cache result
            logger.debug(f"Cache miss: {key}")
            result = func(*args, **kwargs)
            _cache.set(key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_pattern(pattern: str) -> int:
    """
    Invalidate all cache entries matching a pattern.

    Args:
        pattern: Glob-style pattern to match keys (e.g., "taxonomy:*")

    Returns:
        Number of entries invalidated

    Examples:
        >>> invalidate_pattern("taxonomy:*")  # Invalidate all taxonomy keys
        >>> invalidate_pattern("skill:python:*")  # Invalidate all Python skill caches
        >>> invalidate_pattern("*")  # Clear all cache

    """
    import fnmatch

    with _cache._lock:
        keys_to_delete = [key for key in _cache._cache if fnmatch.fnmatch(key, pattern)]
        for key in keys_to_delete:
            del _cache._cache[key]

        _cache._stats["invalidations"] += len(keys_to_delete)
        return len(keys_to_delete)


# Public API
def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    return _cache


def set_cache(cache: InMemoryCache) -> None:
    """Set a custom cache instance (useful for testing or Redis replacement)."""
    global _cache
    _cache = cache


__all__ = [
    "InMemoryCache",
    "cache_key",
    "hash_key",
    "cached",
    "cache_result",
    "invalidate_pattern",
    "get_cache",
    "set_cache",
]
