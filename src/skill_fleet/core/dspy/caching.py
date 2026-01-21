"""Caching strategies for DSPy modules.

Implements multi-level caching for performance optimization.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from pathlib import Path
from typing import Any

import dspy

logger = logging.getLogger(__name__)


class CachedModule(dspy.Module):
    """Wrapper for caching DSPy module results.

    Caches based on input hash for deterministic modules.
    Useful for expensive operations (optimization, validation).

    Example:
        expensive_module = dspy.ChainOfThought("complex_task -> output")
        cached = CachedModule(expensive_module, cache_dir=".cache")

        # First call: executes module
        result1 = cached(task="test")

        # Second call with same input: returns cached result
        result2 = cached(task="test")  # Instant!
    """

    def __init__(
        self,
        module: dspy.Module,
        cache_dir: str | Path = ".dspy_cache/modules",
        ttl_seconds: int | None = None,
        use_memory: bool = True,
    ) -> None:
        """Initialize cached module.

        Args:
            module: DSPy module to cache
            cache_dir: Directory for disk cache
            ttl_seconds: Time-to-live for cache entries (None = forever)
            use_memory: Whether to use in-memory cache (faster)
        """
        super().__init__()
        self.module = module
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.use_memory = use_memory

        # In-memory cache
        self._memory_cache: dict[str, dspy.Prediction] = {}

        # Statistics
        self.hits = 0
        self.misses = 0

    def _compute_cache_key(self, **kwargs) -> str:
        """Compute cache key from inputs.

        Args:
            **kwargs: Module inputs

        Returns:
            Cache key hash
        """
        # Sort keys for deterministic hashing
        sorted_items = sorted(kwargs.items())
        key_str = json.dumps(sorted_items, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key.

        Args:
            cache_key: Cache key hash

        Returns:
            Path to cache file
        """
        # Use first 2 chars for sharding (prevents too many files in one dir)
        shard_dir = self.cache_dir / cache_key[:2]
        shard_dir.mkdir(exist_ok=True)
        return shard_dir / f"{cache_key}.pkl"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache entry is still valid.

        Args:
            cache_path: Path to cache file

        Returns:
            True if valid, False if expired or missing
        """
        if not cache_path.exists():
            return False

        if self.ttl_seconds is None:
            return True

        import time

        age_seconds = time.time() - cache_path.stat().st_mtime
        return age_seconds < self.ttl_seconds

    def forward(self, **kwargs: Any) -> dspy.Prediction:
        """Execute module with caching.

        Args:
            **kwargs: Module inputs

        Returns:
            Cached or freshly computed result
        """
        cache_key = self._compute_cache_key(**kwargs)

        # Check memory cache first
        if self.use_memory and cache_key in self._memory_cache:
            self.hits += 1
            logger.debug(f"Memory cache hit (key={cache_key[:8]}...)")
            return self._memory_cache[cache_key]

        # Check disk cache
        cache_path = self._get_cache_path(cache_key)
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    result = pickle.load(f)

                self.hits += 1
                logger.debug(f"Disk cache hit (key={cache_key[:8]}...)")

                # Populate memory cache
                if self.use_memory:
                    self._memory_cache[cache_key] = result

                return result

            except Exception as e:
                logger.warning(f"Cache read failed: {e}, recomputing")

        # Cache miss - execute module
        self.misses += 1
        logger.debug(f"Cache miss (key={cache_key[:8]}...)")

        result = self.module(**kwargs)

        # Save to disk cache
        try:
            with open(cache_path, "wb") as f:
                pickle.dump(result, f)
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

        # Save to memory cache
        if self.use_memory:
            self._memory_cache[cache_key] = result

        return result

    def clear_cache(self) -> int:
        """Clear all caches.

        Returns:
            Number of cache files deleted
        """
        count = 0

        # Clear memory cache
        self._memory_cache.clear()

        # Clear disk cache
        for cache_file in self.cache_dir.glob("**/*.pkl"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache stats
        """
        total = self.hits + self.misses
        hit_rate = float(self.hits) / float(total) if total > 0 else 0.0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self._memory_cache),
        }
