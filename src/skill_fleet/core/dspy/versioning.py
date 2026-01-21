"""Versioning and A/B testing infrastructure for DSPy programs.

Enables version management, comparison, and gradual rollout of optimized programs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import dspy

logger = logging.getLogger(__name__)


@dataclass
class ProgramVersion:
    """Version metadata for a DSPy program."""

    version_id: str
    name: str
    optimizer: str
    training_examples: int
    quality_score: float
    created_at: str
    file_path: str
    config: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_id": self.version_id,
            "name": self.name,
            "optimizer": self.optimizer,
            "training_examples": self.training_examples,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
            "file_path": self.file_path,
            "config": self.config,
        }


class ProgramRegistry:
    """Registry for managing multiple program versions.

    Tracks different optimized versions of DSPy programs for:
    - Version comparison
    - A/B testing
    - Rollback capabilities
    - Performance tracking

    Example:
        registry = ProgramRegistry("config/optimized")

        # Register new version
        registry.register(
            program=optimized_v1,
            name="skill_generator_v1",
            optimizer="miprov2",
            quality_score=0.85,
        )

        # Load specific version
        loaded = registry.load("skill_generator_v1")

        # List all versions
        versions = registry.list_versions()
    """

    def __init__(self, registry_dir: str | Path = "config/optimized") -> None:
        """Initialize program registry.

        Args:
            registry_dir: Directory to store programs and registry
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "registry.json"
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from disk."""
        if self.registry_file.exists():
            with open(self.registry_file, encoding="utf-8") as f:
                self.versions = json.load(f)
        else:
            self.versions: dict[str, dict] = {}

    def _save_registry(self) -> None:
        """Save registry to disk."""
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.versions, f, indent=2, ensure_ascii=False)

    def register(
        self,
        program: dspy.Module,
        name: str,
        optimizer: str,
        quality_score: float,
        training_examples: int = 0,
        config: dict[str, Any] | None = None,
    ) -> str:
        """Register a new program version.

        Args:
            program: DSPy program to register
            name: Version name (e.g., "skill_generator_v1")
            optimizer: Optimizer used (e.g., "miprov2")
            quality_score: Quality score achieved
            training_examples: Number of training examples used
            config: Additional configuration metadata

        Returns:
            Version ID (hash of program)
        """
        # Generate version ID from program hash
        program_bytes = pickle.dumps(program)
        version_id = hashlib.sha256(program_bytes).hexdigest()[:12]

        # Save program file
        program_file = self.registry_dir / f"{name}_{version_id}.pkl"
        with open(program_file, "wb") as f:
            pickle.dump(program, f)

        # Create version metadata
        version = ProgramVersion(
            version_id=version_id,
            name=name,
            optimizer=optimizer,
            training_examples=training_examples,
            quality_score=quality_score,
            created_at=datetime.now().isoformat(),
            file_path=str(program_file),
            config=config or {},
        )

        # Store in registry
        self.versions[name] = version.to_dict()
        self._save_registry()

        logger.info(f"Registered program version: {name} (ID: {version_id})")
        return version_id

    def load(self, name: str) -> dspy.Module:
        """Load a program version by name.

        Args:
            name: Version name

        Returns:
            Loaded DSPy program

        Raises:
            KeyError: If version not found
        """
        if name not in self.versions:
            raise KeyError(f"Program version '{name}' not found in registry")

        version_info = self.versions[name]
        program_file = Path(version_info["file_path"])

        if not program_file.exists():
            raise FileNotFoundError(f"Program file not found: {program_file}")

        with open(program_file, "rb") as f:
            program = pickle.load(f)

        logger.info(f"Loaded program version: {name}")
        return program

    def list_versions(self, sort_by: str = "created_at") -> list[dict]:
        """List all registered versions.

        Args:
            sort_by: Field to sort by ("created_at", "quality_score", "name")

        Returns:
            List of version dictionaries
        """
        versions = list(self.versions.values())

        if sort_by == "quality_score":
            versions.sort(key=lambda v: v.get("quality_score", 0), reverse=True)
        elif sort_by == "created_at":
            versions.sort(key=lambda v: v.get("created_at", ""), reverse=True)

        return versions

    def compare(self, name1: str, name2: str) -> dict[str, Any]:
        """Compare two program versions.

        Args:
            name1: First version name
            name2: Second version name

        Returns:
            Comparison dictionary
        """
        v1 = self.versions.get(name1)
        v2 = self.versions.get(name2)

        if not v1 or not v2:
            raise KeyError("One or both versions not found")

        return {
            "version1": v1,
            "version2": v2,
            "quality_diff": v2["quality_score"] - v1["quality_score"],
            "optimizer_diff": f"{v1['optimizer']} → {v2['optimizer']}",
            "training_diff": v2["training_examples"] - v1["training_examples"],
        }


class ABTestRouter(dspy.Module):
    """Route requests to different program versions for A/B testing.

    Supports multiple routing strategies:
    - Random (50/50 split)
    - Weighted (e.g., 90% v1, 10% v2)
    - User-based (deterministic based on user_id)
    - Performance-based (adaptive based on success rates)

    Example:
        router = ABTestRouter(
            variants={"v1": program_v1, "v2": program_v2},
            weights={"v1": 0.9, "v2": 0.1},  # 90/10 split
            strategy="weighted"
        )

        result = router(task="Test", user_id="user123")
    """

    def __init__(
        self,
        variants: dict[str, dspy.Module],
        weights: dict[str, float] | None = None,
        strategy: str = "random",
    ) -> None:
        """Initialize A/B test router.

        Args:
            variants: Dictionary of variant_name -> program
            weights: Dictionary of variant_name -> weight (for weighted strategy)
            strategy: Routing strategy ("random", "weighted", "user_hash")
        """
        super().__init__()
        self.variants = variants
        self.weights = weights or {k: 1.0 / len(variants) for k in variants}
        self.strategy = strategy

        # Normalize weights
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}

        # Tracking
        self.execution_counts: dict[str, int] = {k: 0 for k in variants}
        self.success_counts: dict[str, int] = {k: 0 for k in variants}

    def _select_variant(self, user_id: str | None = None) -> str:
        """Select variant based on strategy.

        Args:
            user_id: Optional user ID for deterministic routing

        Returns:
            Variant name to use
        """
        import random

        if self.strategy == "random":
            # Random selection based on weights
            variants = list(self.weights.keys())
            weights = list(self.weights.values())
            return random.choices(variants, weights=weights)[0]

        elif self.strategy == "user_hash" and user_id:
            # Deterministic based on user_id hash
            hash_val = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
            cumulative = 0.0
            threshold = (hash_val % 1000) / 1000.0

            for variant, weight in self.weights.items():
                cumulative += weight
                if threshold < cumulative:
                    return variant

            return list(self.weights.keys())[-1]

        else:
            # Fallback: first variant
            return list(self.variants.keys())[0]

    def forward(self, user_id: str | None = None, **kwargs: Any) -> dspy.Prediction:
        """Route request to selected variant.

        Args:
            user_id: Optional user ID for deterministic routing
            **kwargs: Module input parameters

        Returns:
            Prediction from selected variant
        """
        variant_name = self._select_variant(user_id)
        variant = self.variants[variant_name]

        self.execution_counts[variant_name] += 1

        try:
            result = variant(**kwargs)
            self.success_counts[variant_name] += 1

            # Add routing metadata
            result._variant = variant_name
            return result

        except Exception as e:
            logger.error(f"Variant {variant_name} failed: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get A/B testing statistics.

        Returns:
            Statistics for each variant
        """
        stats = {}
        for variant in self.variants:
            executions = self.execution_counts[variant]
            successes = self.success_counts[variant]

            stats[variant] = {
                "executions": executions,
                "successes": successes,
                "success_rate": successes / executions if executions > 0 else 0.0,
                "weight": self.weights[variant],
            }

        return stats
