"""
Taxonomy management for hierarchical skills.

The taxonomy is stored on disk under a configurable `skills_root` directory.
This manager provides:
- Metadata loading for always-loaded skills (core, essential MCP, memory blocks)
- Minimal branch selection for task keyword routing
- Dependency validation and circular dependency detection
- Skill registration (writes metadata + content, updates taxonomy stats)
- agentskills.io compliance (YAML frontmatter, XML discovery)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from ..analytics.engine import UsageTracker
from ..common.security import resolve_path_within_root, sanitize_taxonomy_path
from .discovery import (
    ensure_all_skills_loaded,
    generate_available_skills_xml,
    get_skill_for_prompt,
)
from .models import TaxonomyIndex
from .path_resolver import get_parent_skills, resolve_skill_location
from .skill_loader import (
    load_skill_dir_metadata,
    load_skill_file,
    parse_skill_frontmatter,
)
from .skill_registration import (
    register_skill,
)

if TYPE_CHECKING:
    from .metadata import SkillMetadata

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaxonomyPath:
    """
    Value object representing a taxonomy path.

    Provides validation and safe string representation.
    """

    path: str

    def __post_init__(self) -> None:
        """
        Validate and sanitize the taxonomy path after initialization.

        Raises:
            ValueError: If the path is empty or contains invalid characters.

        """
        # Validate path format
        if not self.path:
            raise ValueError("Taxonomy path cannot be empty")

        # Sanitize to prevent traversal attacks
        safe = sanitize_taxonomy_path(self.path)
        if not safe:
            raise ValueError(f"Invalid taxonomy path: {self.path}")

        # Update with safe value (frozen dataclass workaround)
        object.__setattr__(self, "path", safe)

    def __str__(self) -> str:
        """
        Return the string representation of the taxonomy path.

        Returns:
            The taxonomy path as a string.

        """
        return self.path

    def parent(self) -> TaxonomyPath | None:
        """Get the parent taxonomy path, or None if at root."""
        parts = self.path.split("/")
        if len(parts) <= 1:
            return None
        return TaxonomyPath("/".join(parts[:-1]))

    def child(self, segment: str) -> TaxonomyPath:
        """Create a child taxonomy path."""
        return TaxonomyPath(f"{self.path}/{segment}")

    def depth(self) -> int:
        """Return the depth of this path in the taxonomy tree."""
        return len(self.path.split("/"))


class TaxonomyManager:
    """Manages a hierarchical skill taxonomy stored on disk."""

    _ALWAYS_LOADED_DIRS = ("_core", "mcp_capabilities", "memory_blocks")

    def __init__(self, skills_root: Path) -> None:
        """
        Initialize the taxonomy manager.

        Args:
            skills_root: Path to the root directory containing skills.

        """
        # Treat skills_root as configuration input; resolve it once for consistent
        # containment checks and to avoid ambiguous relative path behavior.
        self.skills_root = Path(skills_root).resolve()
        self.meta_path = self.skills_root / "taxonomy_meta.json"
        self.index_path = self.skills_root / "taxonomy_index.json"
        self.metadata_cache: dict[str, SkillMetadata] = {}
        self.meta: dict[str, Any] = {}
        self.index: TaxonomyIndex = TaxonomyIndex()

        self.usage_tracker = UsageTracker(
            self.skills_root / "_analytics",
            trusted_root=self.skills_root,
        )

        self.load_taxonomy_meta()
        self.load_index()
        self._load_always_loaded_skills()

    def track_usage(
        self,
        skill_id: str,
        user_id: str,
        success: bool = True,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Track skill usage and update taxonomy stats."""
        self.usage_tracker.track_usage(skill_id, user_id, success, task_id, metadata)

        # Update high-level stats in taxonomy_meta.json
        usage_stats = self.meta.setdefault("usage_stats", {})
        skill_stats = usage_stats.setdefault(skill_id, {"count": 0, "successes": 0})
        skill_stats["count"] += 1
        if success:
            skill_stats["successes"] += 1

        self.meta_path.write_text(json.dumps(self.meta, indent=2) + "\n", encoding="utf-8")

    def load_taxonomy_meta(self) -> dict[str, Any]:
        """Load taxonomy metadata from disk."""
        if not self.meta_path.exists():
            raise FileNotFoundError(f"Taxonomy metadata not found: {self.meta_path}")

        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return self.meta

    def load_index(self) -> TaxonomyIndex:
        """Load the taxonomy index from disk."""
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                self.index = TaxonomyIndex(**data)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.error(f"Failed to load or parse taxonomy index: {e}")
                self.index = TaxonomyIndex()
        else:
            self.index = TaxonomyIndex()
        return self.index

    def resolve_skill_location(self, skill_identifier: str) -> str:
        """
        Resolve a skill identifier (ID, path, or alias) to its canonical storage path.

        This implements the polyfill strategy:
        1. Check Index (canonical ID or alias).
        2. Fallback to Filesystem (legacy support).
        """
        return resolve_skill_location(skill_identifier, self.skills_root, self.index)

    def _load_always_loaded_skills(self) -> None:
        """Load always-loaded skill files into the metadata cache."""
        for relative_dir in self._ALWAYS_LOADED_DIRS:
            skills_dir = resolve_path_within_root(self.skills_root, relative_dir)
            if not skills_dir.exists():
                continue

            for skill_file in skills_dir.glob("*.json"):
                self._load_skill_file(skill_file)

    def _load_skill_file(self, skill_file: Path) -> SkillMetadata:
        """Load a skill definition stored as a single JSON file."""
        metadata = load_skill_file(skill_file)
        self.metadata_cache[metadata.skill_id] = metadata
        return metadata

    def _load_skill_dir_metadata(self, skill_dir: Path) -> SkillMetadata:
        """
        Load a skill definition stored as a directory containing `metadata.json`.

        Also attempts to parse YAML frontmatter from SKILL.md for agentskills.io
        compliant skills.
        """
        metadata = load_skill_dir_metadata(skill_dir)
        self.metadata_cache[metadata.skill_id] = metadata
        return metadata

    def parse_skill_frontmatter(self, skill_md_path: Path) -> dict[str, Any]:
        """
        Parse YAML frontmatter from a SKILL.md file.

        Returns:
            Dict with frontmatter fields (name, description, metadata, etc.)
            Empty dict if no valid frontmatter found.

        """
        return parse_skill_frontmatter(skill_md_path)

    def skill_exists(self, taxonomy_path: str) -> bool:
        """Check if a skill exists at the given taxonomy path."""
        try:
            self.resolve_skill_location(taxonomy_path)
            return True
        except FileNotFoundError:
            return False

    def get_skill_metadata(self, skill_id: str) -> SkillMetadata | None:
        """Retrieve cached skill metadata by `skill_id`."""
        return self.metadata_cache.get(skill_id)

    def get_mounted_skills(self, user_id: str) -> list[str]:
        """
        Get currently mounted skills for a user.

        Note: user-specific mounting is not implemented in Phase 1; returns only
        always-loaded skills.
        """
        _ = user_id
        return [skill_id for skill_id, meta in self.metadata_cache.items() if meta.always_loaded]

    def get_relevant_branches(self, task_description: str) -> dict[str, dict[str, str]]:
        """
        Get relevant taxonomy branches for a task.

        Returns a subset of taxonomy structure based on simple keyword matching.
        """
        branches: dict[str, dict[str, str]] = {}
        keywords = task_description.lower().split()

        if any(k in keywords for k in ["code", "program", "develop", "script"]):
            branches["technical_skills/programming"] = self._get_branch_structure(
                "technical_skills/programming"
            )

        if any(k in keywords for k in ["data", "analyze", "statistics"]):
            branches["domain_knowledge"] = self._get_branch_structure("domain_knowledge")

        if any(k in keywords for k in ["debug", "fix", "error"]):
            branches["task_focus_areas"] = self._get_branch_structure("task_focus_areas")

        return branches

    def _get_branch_structure(self, branch_path: str) -> dict[str, str]:
        """Get directory structure of a taxonomy branch."""
        safe_branch_path = sanitize_taxonomy_path(branch_path)
        if safe_branch_path is None:
            return {}

        full_path = resolve_path_within_root(self.skills_root, safe_branch_path)
        if not full_path.exists():
            return {}

        structure: dict[str, str] = {}
        for item in full_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                structure[item.name] = "available"
        return structure

    def get_parent_skills(self, taxonomy_path: str) -> list[dict[str, Any]]:
        """Get parent and sibling skills for context."""
        return get_parent_skills(taxonomy_path, self.skills_root)

    def register_skill(
        self,
        path: str,
        metadata: dict[str, Any],
        content: str,
        evolution: dict[str, Any],
        extra_files: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> bool:
        """
        Register a new skill in the taxonomy.

        Creates an agentskills.io compliant skill with YAML frontmatter in SKILL.md
        and extended metadata in metadata.json.
        """
        try:
            skill_metadata = register_skill(
                skills_root=self.skills_root,
                path=path,
                metadata=metadata,
                content=content,
                evolution=evolution,
                extra_files=extra_files,
                overwrite=overwrite,
            )
            # Update cache
            self.metadata_cache[skill_metadata.skill_id] = skill_metadata
            # Update taxonomy stats
            self._update_taxonomy_stats(metadata)
            return True
        except ValueError:
            return False

    # ========================================================================
    # agentskills.io Discoverability
    # ========================================================================

    def generate_available_skills_xml(self, user_id: str | None = None) -> str:
        """
        Generate <available_skills> XML for agent context injection.

        This XML format follows the agentskills.io integration standard
        for injecting skill metadata into agent system prompts.

        Args:
            user_id: Optional user ID to filter skills (not yet implemented)

        Returns:
            XML string following agentskills.io format

        """
        # Load all skills from disk if cache is incomplete
        ensure_all_skills_loaded(
            self.skills_root, self.metadata_cache, self._load_skill_dir_metadata
        )
        return generate_available_skills_xml(self.metadata_cache, self.skills_root, user_id)

    def get_skill_for_prompt(self, skill_id: str) -> str | None:
        """
        Get the full SKILL.md content for loading into an agent's context.

        This is the 'activation' step in the agentskills.io integration flow.

        Args:
            skill_id: The skill identifier

        Returns:
            Full SKILL.md content or None if not found

        """
        meta = self.get_skill_metadata(skill_id) or self._try_load_skill_by_id(skill_id)
        if meta is None:
            return None
        return get_skill_for_prompt(skill_id, self.metadata_cache)

    def _update_taxonomy_stats(self, metadata: dict[str, Any]) -> None:
        """Update taxonomy statistics and persist taxonomy_meta.json."""
        stats = self.meta.setdefault("statistics", {})
        by_type = stats.setdefault("by_type", {})
        by_weight = stats.setdefault("by_weight", {})
        by_priority = stats.setdefault("by_priority", {})

        self.meta["total_skills"] = int(self.meta.get("total_skills", 0)) + 1
        self.meta["generation_count"] = int(self.meta.get("generation_count", 0)) + 1
        self.meta["last_updated"] = datetime.now(tz=UTC).isoformat()

        skill_type = str(metadata.get("type", "unknown"))
        by_type[skill_type] = int(by_type.get(skill_type, 0)) + 1

        skill_weight = str(metadata.get("weight", "unknown"))
        by_weight[skill_weight] = int(by_weight.get(skill_weight, 0)) + 1

        skill_priority = str(metadata.get("load_priority", "unknown"))
        by_priority[skill_priority] = int(by_priority.get(skill_priority, 0)) + 1

        self.meta_path.write_text(json.dumps(self.meta, indent=2) + "\n", encoding="utf-8")

    def validate_dependencies(self, dependencies: list[str]) -> tuple[bool, list[str]]:
        """Validate that all dependencies can be resolved."""
        missing: list[str] = []
        for dep_id in dependencies:
            if dep_id in self.metadata_cache:
                continue

            if self._try_load_skill_by_id(dep_id) is None:
                missing.append(dep_id)

        return len(missing) == 0, missing

    def _try_load_skill_by_id(self, skill_id: str) -> SkillMetadata | None:
        """Try to load skill metadata from disk, caching it on success."""
        try:
            canonical_path = self.resolve_skill_location(skill_id)
        except FileNotFoundError:
            return None

        # Directory-form skill
        skill_dir = resolve_path_within_root(self.skills_root, canonical_path)
        if (skill_dir / "metadata.json").exists():
            return self._load_skill_dir_metadata(skill_dir)

        # Single-file skill
        skill_file = resolve_path_within_root(self.skills_root, f"{canonical_path}.json")
        if skill_file.exists():
            return self._load_skill_file(skill_file)

        return None

    def detect_circular_dependencies(
        self,
        skill_id: str,
        dependencies: list[str],
        visited: set[str] | None = None,
    ) -> tuple[bool, list[str] | None]:
        """Detect circular dependency chains."""
        if visited is None:
            visited = set()

        if skill_id in visited:
            return True, [*visited, skill_id]

        visited.add(skill_id)

        for dep_id in dependencies:
            dep_meta = self.get_skill_metadata(dep_id) or self._try_load_skill_by_id(dep_id)
            if dep_meta is None:
                continue

            has_cycle, cycle_path = self.detect_circular_dependencies(
                dep_id,
                dep_meta.dependencies,
                visited.copy(),
            )
            if has_cycle:
                return True, cycle_path

        return False, None
