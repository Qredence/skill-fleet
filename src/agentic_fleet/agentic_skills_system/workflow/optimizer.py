"""Workflow caching and optimization helpers."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path
from typing import Any


class WorkflowOptimizer:
    """Caches workflow step outputs to speed up repeated runs."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hit_rate = {"hits": 0, "misses": 0}

    def cache_key(self, step: str, inputs: dict[str, Any]) -> str:
        payload = json.dumps(inputs, sort_keys=True, default=str)
        digest = hashlib.md5(f"{step}::{payload}".encode()).hexdigest()
        return digest

    def get_cached(self, step: str, inputs: dict[str, Any]) -> Any | None:
        key = self.cache_key(step, inputs)
        cache_file = self.cache_dir / f"{key}.pkl"
        if not cache_file.exists():
            self.hit_rate["misses"] += 1
            return None
        try:
            with cache_file.open("rb") as handle:
                self.hit_rate["hits"] += 1
                return pickle.load(handle)
        except Exception:
            self.hit_rate["misses"] += 1
            return None

    def cache_result(self, step: str, inputs: dict[str, Any], result: Any) -> None:
        key = self.cache_key(step, inputs)
        cache_file = self.cache_dir / f"{key}.pkl"
        try:
            with cache_file.open("wb") as handle:
                pickle.dump(result, handle)
        except Exception:
            # Ignore cache failures; they should not break the workflow.
            return

    def clear_cache(self) -> None:
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()

    def get_cache_stats(self) -> dict[str, Any]:
        total = self.hit_rate["hits"] + self.hit_rate["misses"]
        hit_rate = self.hit_rate["hits"] / total if total else 0
        return {
            "hits": self.hit_rate["hits"],
            "misses": self.hit_rate["misses"],
            "hit_rate": hit_rate,
            "cache_size": len(list(self.cache_dir.glob("*.pkl"))),
        }
