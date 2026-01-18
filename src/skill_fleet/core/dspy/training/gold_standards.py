"""Gold-standard training data management for DSPy optimization.

This module provides utilities for loading, managing, and creating training
examples from high-quality skills. These examples are used by DSPy optimizers
(MIPROv2, BootstrapFewShot) to improve skill generation quality.

Gold-standard skills are identified by:
1. Manual curation (config/training/gold_skills.json)
2. Quality score threshold (>= 0.8)
3. External excellent examples (Anthropics, Obra/Superpowers)

Usage:
    from skill_fleet.core.dspy.training import GoldStandardLoader

    loader = GoldStandardLoader()

    # Load training set
    trainset = loader.load_trainset()

    # Load test set (for evaluation)
    testset = loader.load_testset()

    # Add new gold-standard skill
    loader.add_gold_skill(skill_path, task_description)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import dspy
import yaml

from ....common.paths import default_config_path, find_repo_root
from ..metrics import assess_skill_quality

logger = logging.getLogger(__name__)


@dataclass
class GoldSkillEntry:
    """Entry for a gold-standard skill."""

    skill_id: str
    task_description: str
    skill_path: str | None = None
    skill_content: str | None = None
    quality_score: float = 0.0
    source: str = "local"  # local, anthropics, obra, manual
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "skill_id": self.skill_id,
            "task_description": self.task_description,
            "skill_path": self.skill_path,
            "quality_score": self.quality_score,
            "source": self.source,
            "metadata": self.metadata,
        }

    def to_dspy_example(self) -> dspy.Example:
        """Convert to DSPy Example for training/evaluation."""
        return dspy.Example(
            task_description=self.task_description,
            skill_content=self.skill_content or "",
            quality_score=self.quality_score,
            skill_id=self.skill_id,
        ).with_inputs("task_description")


class GoldStandardLoader:
    """Loader for gold-standard training examples.

    This class manages the loading and creation of training examples
    from high-quality skills for DSPy optimization.
    """

    def __init__(
        self,
        config_path: Path | None = None,
        gold_skills_path: Path | None = None,
    ):
        """Initialize the loader.

        Args:
            config_path: Path to config.yaml (default: auto-detect)
            gold_skills_path: Path to gold_skills.json (default: from config)
        """
        self.config_path = config_path or default_config_path()
        self.config = self._load_config()

        # Determine gold skills path
        if gold_skills_path:
            self.gold_skills_path = gold_skills_path
        else:
            training_config = self.config.get("optimization", {}).get("training", {})
            relative_path = training_config.get(
                "gold_skills_path", "config/training/gold_skills.json"
            )
            repo_root = find_repo_root(self.config_path)
            if repo_root:
                candidate = repo_root / relative_path
                if candidate.exists():
                    self.gold_skills_path = candidate
                else:
                    self.gold_skills_path = Path(relative_path)
            else:
                # When running from an installed wheel, `config_path` typically lives at
                # `.../site-packages/skill_fleet/config/config.yaml`. Interpret repo-style
                # "config/..." paths relative to that packaged config directory.
                config_root = self.config_path.parent
                rel = str(relative_path)
                if rel.startswith("config/"):
                    rel = rel.removeprefix("config/")
                self.gold_skills_path = config_root / rel

        self.repo_root = find_repo_root(self.config_path)
        self._gold_skills: list[GoldSkillEntry] = []

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_gold_skills_file(self) -> list[dict[str, Any]]:
        """Load gold skills from JSON file."""
        if self.gold_skills_path.exists():
            with open(self.gold_skills_path) as f:
                data = json.load(f)
                return data.get("skills", []) if isinstance(data, dict) else data
        return []

    def _save_gold_skills_file(self, skills: list[dict[str, Any]]) -> None:
        """Save gold skills to JSON file."""
        self.gold_skills_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.gold_skills_path, "w") as f:
            json.dump({"skills": skills, "version": "1.0"}, f, indent=2)

    def load_gold_skills(self, min_quality: float = 0.0) -> list[GoldSkillEntry]:
        """Load all gold-standard skills.

        Args:
            min_quality: Minimum quality score filter

        Returns:
            List of GoldSkillEntry objects
        """
        if self._gold_skills:
            return [s for s in self._gold_skills if s.quality_score >= min_quality]

        entries: list[GoldSkillEntry] = []

        # Load from gold_skills.json
        for skill_data in self._load_gold_skills_file():
            entry = self._create_entry_from_data(skill_data)
            if entry and entry.quality_score >= min_quality:
                entries.append(entry)

        # Auto-discover high-quality local skills
        if self.repo_root:
            skills_dir = self.repo_root / "skills"
            if skills_dir.exists():
                discovered = self._discover_high_quality_skills(skills_dir, min_quality)
                # Avoid duplicates
                existing_ids = {e.skill_id for e in entries}
                for entry in discovered:
                    if entry.skill_id not in existing_ids:
                        entries.append(entry)

        self._gold_skills = entries
        logger.info(f"Loaded {len(entries)} gold-standard skills")
        return entries

    def _create_entry_from_data(self, data: dict[str, Any]) -> GoldSkillEntry | None:
        """Create GoldSkillEntry from JSON data."""
        skill_id = data.get("skill_id", "")
        task_description = data.get("task_description", "")

        if not skill_id or not task_description:
            return None

        # Load skill content if path provided
        skill_content = data.get("skill_content")
        skill_path = data.get("skill_path")

        if not skill_content and skill_path and self.repo_root:
            full_path = self.repo_root / skill_path
            if full_path.exists():
                skill_content = full_path.read_text(encoding="utf-8")

        # Calculate quality score if not provided
        quality_score = data.get("quality_score", 0.0)
        if skill_content and quality_score == 0.0:
            scores = assess_skill_quality(skill_content)
            quality_score = scores.overall_score

        return GoldSkillEntry(
            skill_id=skill_id,
            task_description=task_description,
            skill_path=skill_path,
            skill_content=skill_content,
            quality_score=quality_score,
            source=data.get("source", "manual"),
            metadata=data.get("metadata", {}),
        )

    def _discover_high_quality_skills(
        self,
        skills_dir: Path,
        min_quality: float = 0.8,
    ) -> list[GoldSkillEntry]:
        """Auto-discover high-quality skills from directory.

        Args:
            skills_dir: Path to skills directory
            min_quality: Minimum quality score threshold

        Returns:
            List of discovered high-quality skills
        """
        entries: list[GoldSkillEntry] = []

        # Exclude drafts for auto-discovery
        skill_files = [f for f in skills_dir.glob("**/SKILL.md") if "_drafts" not in str(f)]

        for skill_file in skill_files:
            try:
                content = skill_file.read_text(encoding="utf-8")
                scores = assess_skill_quality(content)

                if scores.overall_score >= min_quality:
                    # Generate task description from skill name/description
                    skill_name = skill_file.parent.name
                    task_desc = (
                        f"Create a skill for {skill_name.replace('-', ' ').replace('_', ' ')}"
                    )

                    entry = GoldSkillEntry(
                        skill_id=str(skill_file.parent.relative_to(skills_dir)),
                        task_description=task_desc,
                        skill_path=str(skill_file.relative_to(self.repo_root))
                        if self.repo_root
                        else str(skill_file),
                        skill_content=content,
                        quality_score=scores.overall_score,
                        source="local",
                        metadata={"auto_discovered": True},
                    )
                    entries.append(entry)
                    logger.debug(
                        f"Discovered high-quality skill: {skill_name} ({scores.overall_score:.2f})"
                    )

            except Exception as e:
                logger.warning(f"Error processing {skill_file}: {e}")

        return entries

    def load_trainset(
        self,
        min_quality: float = 0.8,
        max_examples: int | None = None,
    ) -> list[dspy.Example]:
        """Load training set for DSPy optimization.

        Args:
            min_quality: Minimum quality score for training examples
            max_examples: Maximum number of examples to return

        Returns:
            List of DSPy Examples for training
        """
        gold_skills = self.load_gold_skills(min_quality=min_quality)

        # Sort by quality score (highest first)
        gold_skills.sort(key=lambda x: x.quality_score, reverse=True)

        if max_examples:
            gold_skills = gold_skills[:max_examples]

        return [skill.to_dspy_example() for skill in gold_skills]

    def load_testset(
        self,
        min_quality: float = 0.6,
        max_examples: int | None = None,
        exclude_trainset: bool = True,
    ) -> list[dspy.Example]:
        """Load test set for evaluation.

        Args:
            min_quality: Minimum quality score for test examples
            max_examples: Maximum number of examples
            exclude_trainset: Whether to exclude high-quality training examples

        Returns:
            List of DSPy Examples for testing
        """
        gold_skills = self.load_gold_skills(min_quality=min_quality)

        if exclude_trainset:
            # Use lower-quality skills for testing
            gold_skills = [s for s in gold_skills if s.quality_score < 0.8]

        if max_examples:
            gold_skills = gold_skills[:max_examples]

        return [skill.to_dspy_example() for skill in gold_skills]

    def add_gold_skill(
        self,
        skill_path: Path | str,
        task_description: str,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
    ) -> GoldSkillEntry | None:
        """Add a new gold-standard skill.

        Args:
            skill_path: Path to SKILL.md file
            task_description: Description of the task this skill addresses
            source: Source of the skill (manual, local, etc.)
            metadata: Additional metadata

        Returns:
            Created GoldSkillEntry or None if failed
        """
        skill_path = Path(skill_path)
        if not skill_path.exists():
            logger.error(f"Skill file not found: {skill_path}")
            return None

        try:
            content = skill_path.read_text(encoding="utf-8")
            scores = assess_skill_quality(content)

            # Determine skill_id
            if self.repo_root and skill_path.is_relative_to(self.repo_root):
                skill_id = str(skill_path.parent.relative_to(self.repo_root / "skills"))
            else:
                skill_id = skill_path.parent.name

            entry = GoldSkillEntry(
                skill_id=skill_id,
                task_description=task_description,
                skill_path=str(skill_path),
                skill_content=content,
                quality_score=scores.overall_score,
                source=source,
                metadata=metadata or {},
            )

            # Update gold_skills.json
            existing_skills = self._load_gold_skills_file()
            existing_skills.append(entry.to_dict())
            self._save_gold_skills_file(existing_skills)

            # Update cache
            self._gold_skills.append(entry)

            logger.info(f"Added gold skill: {skill_id} (score: {scores.overall_score:.2f})")
            return entry

        except Exception as e:
            logger.error(f"Error adding gold skill {skill_path}: {e}")
            return None

    def create_synthetic_examples(
        self,
        topics: list[str],
        count_per_topic: int = 1,
    ) -> list[dspy.Example]:
        """Create synthetic training examples from topic descriptions.

        This is useful for bootstrapping when few gold-standard skills exist.

        Args:
            topics: List of skill topics to create examples for
            count_per_topic: Number of examples per topic

        Returns:
            List of synthetic DSPy Examples
        """
        examples: list[dspy.Example] = []

        for topic in topics:
            for i in range(count_per_topic):
                task_desc = f"Create a comprehensive skill for {topic}"
                if i > 0:
                    task_desc += f" (variation {i + 1})"

                example = dspy.Example(
                    task_description=task_desc,
                    skill_content="",  # Will be generated
                    quality_score=0.0,
                    skill_id=f"synthetic/{topic.lower().replace(' ', '-')}/{i}",
                ).with_inputs("task_description")

                examples.append(example)

        return examples


def load_trainset(min_quality: float = 0.8) -> list[dspy.Example]:
    """Convenience function to load training set.

    Args:
        min_quality: Minimum quality score threshold

    Returns:
        List of DSPy Examples for training
    """
    loader = GoldStandardLoader()
    return loader.load_trainset(min_quality=min_quality)


def load_testset(min_quality: float = 0.6) -> list[dspy.Example]:
    """Convenience function to load test set.

    Args:
        min_quality: Minimum quality score threshold

    Returns:
        List of DSPy Examples for testing
    """
    loader = GoldStandardLoader()
    return loader.load_testset(min_quality=min_quality)


__all__ = [
    "GoldSkillEntry",
    "GoldStandardLoader",
    "load_testset",
    "load_trainset",
]
