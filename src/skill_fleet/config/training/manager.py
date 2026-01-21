"""
Training Data Manager for DSPy optimization.

Handles metadata, quality scoring, and filtering of training examples used
for optimizing skill creation prompts.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ExampleMetadata(BaseModel):
    """Metadata for a training example."""

    example_id: str = Field(..., description="Unique ID for the example")
    task_description: str = Field(..., description="Original user task")
    category: str = Field(..., description="Skill category (e.g., technical, domain)")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    quality_score: float = Field(0.0, description="Automated quality score (0-1)")
    human_rating: float | None = Field(None, description="Human rating (0-1)")
    success_rate: float = Field(0.0, description="Pass rate in optimization runs")
    usage_count: int = Field(0, description="Number of times used in optimization")
    last_used: str | None = Field(None, description="Timestamp of last usage")
    tags: list[str] = Field(default_factory=list)


@dataclass
class TrainingDataConfig:
    """Configuration for training data selection."""

    min_quality_score: float = 0.7
    max_examples: int = 50
    category_weights: dict[str, float] = field(default_factory=dict)
    diversity_bonus: float = 0.1


class TrainingDataManager:
    """
    Manages the lifecycle, quality, and selection of training examples for DSPy.
    """

    def __init__(self, data_root: Path | str = "config/training"):
        self.data_root = Path(data_root)
        self.metadata_file = self.data_root / "example_metadata.json"
        self.trainset_file = self.data_root / "trainset.json"
        self._metadata: dict[str, ExampleMetadata] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load metadata from disk."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text())
                self._metadata = {k: ExampleMetadata(**v) for k, v in data.items()}
                logger.info(f"Loaded {len(self._metadata)} training example metadata records")
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
                self._metadata = {}
        else:
            logger.warning(f"Metadata file not found at {self.metadata_file}, initializing empty")
            self._metadata = {}

    def save_metadata(self) -> None:
        """Save metadata to disk."""
        try:
            # Ensure directory exists
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

            data = {k: v.model_dump() for k, v in self._metadata.items()}
            self.metadata_file.write_text(json.dumps(data, indent=2))
            logger.info("Saved training metadata")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def get_trainset(self, config: TrainingDataConfig | None = None) -> list[dict[str, Any]]:
        """
        Get a filtered list of training examples based on configuration.

        Args:
            config: Selection configuration. If None, uses defaults.

        Returns:
            List of example dictionaries (compatible with DSPy)

        """
        if config is None:
            config = TrainingDataConfig()

        # Load raw examples
        if not self.trainset_file.exists():
            logger.warning("Trainset file not found")
            return []

        try:
            raw_examples = json.loads(self.trainset_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load trainset: {e}")
            return []

        # Filter and sort
        scored_examples = []
        for ex in raw_examples:
            # Assume examples have 'task_description' or similar ID field
            # If not, generate a hash/ID
            ex_id = self._get_example_id(ex)
            meta = self._metadata.get(ex_id)

            score = 0.0
            if meta:
                # Weighted score based on quality and success
                score = (meta.quality_score * 0.6) + (meta.success_rate * 0.4)

                # Apply category boost
                if meta.category in config.category_weights:
                    score *= config.category_weights[meta.category]

                if score < config.min_quality_score:
                    continue
            else:
                # New/unknown example - give it a chance (neutral score)
                score = 0.5

            scored_examples.append((score, ex))

        # Sort by score descending
        scored_examples.sort(key=lambda x: x[0], reverse=True)

        # Select top N
        selected = [x[1] for x in scored_examples[: config.max_examples]]

        # Update usage stats
        self._update_usage_stats(selected)

        return selected

    def _get_example_id(self, example: dict) -> str:
        """Generate a consistent ID for an example."""
        # Simple heuristic: hash of the input task
        # In a real system, examples should store their ID
        if "id" in example:
            return example["id"]

        # Fallback for DSPy Examples which might be just input/output
        # Assuming 'task_description' or 'user_intent' is the input key
        content = example.get("task_description") or example.get("user_intent") or str(example)
        import hashlib

        return hashlib.md5(content.encode()).hexdigest()

    def _update_usage_stats(self, examples: list[dict]) -> None:
        """Update last_used timestamp and usage count."""
        now = datetime.now(UTC).isoformat()
        changed = False

        for ex in examples:
            ex_id = self._get_example_id(ex)
            if ex_id in self._metadata:
                self._metadata[ex_id].usage_count += 1
                self._metadata[ex_id].last_used = now
                changed = True
            else:
                # Auto-register new metadata if missing
                self._metadata[ex_id] = ExampleMetadata(
                    example_id=ex_id,
                    task_description=ex.get("task_description", "Unknown task"),
                    category="unknown",
                    created_at=now,
                    last_used=now,
                    usage_count=1,
                )
                changed = True

        if changed:
            self.save_metadata()

    def update_scores(self, results: list[dict[str, Any]]) -> None:
        """
        Update example scores based on optimization run results.

        Args:
            results: List of dicts with 'example_id', 'score' (0-1), 'passed' (bool)

        """
        changed = False
        for res in results:
            ex_id = res.get("example_id")
            if not ex_id or ex_id not in self._metadata:
                continue

            meta = self._metadata[ex_id]

            # Update quality score (moving average)
            new_score = res.get("score", 0.0)
            meta.quality_score = (meta.quality_score * 0.8) + (new_score * 0.2)

            # Update success rate
            passed = 1.0 if res.get("passed") else 0.0
            # Simple moving average for success rate too
            meta.success_rate = (meta.success_rate * 0.9) + (passed * 0.1)

            changed = True

        if changed:
            self.save_metadata()

    def score_examples(self) -> None:
        """
        Run static analysis to score all examples (placeholder).
        In a real implementation, this would use a 'judge' LM to rate examples.
        """
        # Placeholder logic
        for meta in self._metadata.values():
            if meta.quality_score == 0.0:
                meta.quality_score = 0.5  # Reset to neutral
        self.save_metadata()
