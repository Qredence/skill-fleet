"""Taxonomy management for hierarchical skills.

The taxonomy is stored on disk under a configurable `skills_root` directory.
This manager provides:
- Metadata loading for always-loaded skills (core, essential MCP, memory blocks)
- Minimal branch selection for task keyword routing
- Dependency validation and circular dependency detection
- Skill registration (writes metadata + content, updates taxonomy stats)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    """Lightweight representation of a skill's metadata."""

    skill_id: str
    version: str
    type: str
    weight: str
    load_priority: str
    dependencies: list[str]
    capabilities: list[str]
    path: Path
    always_loaded: bool = False


class TaxonomyManager:
    """Manages a hierarchical skill taxonomy stored on disk."""

    _ALWAYS_LOADED_DIRS = ("_core", "mcp_capabilities", "memory_blocks")

    def __init__(self, skills_root: Path) -> None:
        self.skills_root = Path(skills_root)
        self.meta_path = self.skills_root / "taxonomy_meta.json"
        self.metadata_cache: dict[str, SkillMetadata] = {}
        self.meta: dict[str, Any] = {}

        self.load_taxonomy_meta()
        self._load_always_loaded_skills()

    def load_taxonomy_meta(self) -> dict[str, Any]:
        """Load taxonomy metadata from disk."""
        if not self.meta_path.exists():
            raise FileNotFoundError(f"Taxonomy metadata not found: {self.meta_path}")

        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        return self.meta

    def _load_always_loaded_skills(self) -> None:
        """Load always-loaded skill files into the metadata cache."""
        for relative_dir in self._ALWAYS_LOADED_DIRS:
            skills_dir = self.skills_root / relative_dir
            if not skills_dir.exists():
                continue

            for skill_file in skills_dir.glob("*.json"):
                self._load_skill_file(skill_file)

    def _load_skill_file(self, skill_file: Path) -> SkillMetadata:
        """Load a skill definition stored as a single JSON file."""
        skill_data = json.loads(skill_file.read_text(encoding="utf-8"))
        skill_id = skill_data["skill_id"]

        metadata = SkillMetadata(
            skill_id=skill_id,
            version=skill_data["version"],
            type=skill_data["type"],
            weight=skill_data["weight"],
            load_priority=skill_data["load_priority"],
            dependencies=list(skill_data.get("dependencies", [])),
            capabilities=list(skill_data.get("capabilities", [])),
            path=skill_file,
            always_loaded=bool(skill_data.get("always_loaded", False)),
        )
        self.metadata_cache[skill_id] = metadata
        return metadata

    def _load_skill_dir_metadata(self, skill_dir: Path) -> SkillMetadata:
        """Load a skill definition stored as a directory containing `metadata.json`."""
        metadata_path = skill_dir / "metadata.json"
        skill_data = json.loads(metadata_path.read_text(encoding="utf-8"))
        skill_id = skill_data["skill_id"]

        metadata = SkillMetadata(
            skill_id=skill_id,
            version=skill_data["version"],
            type=skill_data["type"],
            weight=skill_data["weight"],
            load_priority=skill_data["load_priority"],
            dependencies=list(skill_data.get("dependencies", [])),
            capabilities=list(skill_data.get("capabilities", [])),
            path=metadata_path,
            always_loaded=bool(skill_data.get("always_loaded", False)),
        )
        self.metadata_cache[skill_id] = metadata
        return metadata

    def skill_exists(self, taxonomy_path: str) -> bool:
        """Check if a skill exists at the given taxonomy path."""
        skill_dir = self.skills_root / taxonomy_path
        if (skill_dir / "metadata.json").exists():
            return True

        # Support single-file JSON skills (e.g., under `_core/`)
        skill_file = self.skills_root / f"{taxonomy_path}.json"
        return skill_file.exists()

    def get_skill_metadata(self, skill_id: str) -> SkillMetadata | None:
        """Retrieve cached skill metadata by `skill_id`."""
        return self.metadata_cache.get(skill_id)

    def get_mounted_skills(self, user_id: str) -> list[str]:
        """Get currently mounted skills for a user.

        Note: user-specific mounting is not implemented in Phase 1; returns only
        always-loaded skills.
        """
        _ = user_id
        return [skill_id for skill_id, meta in self.metadata_cache.items() if meta.always_loaded]

    def get_relevant_branches(self, task_description: str) -> dict[str, dict[str, str]]:
        """Get relevant taxonomy branches for a task.

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
        full_path = self.skills_root / branch_path
        if not full_path.exists():
            return {}

        structure: dict[str, str] = {}
        for item in full_path.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                structure[item.name] = "available"
        return structure

    def get_parent_skills(self, taxonomy_path: str) -> list[dict[str, Any]]:
        """Get parent and sibling skills for context."""
        path_parts = taxonomy_path.split("/")
        parent_skills: list[dict[str, Any]] = []

        # Walk up the tree, searching for metadata.json or single-file JSON skills.
        for i in range(len(path_parts) - 1, 0, -1):
            parent_path = "/".join(path_parts[:i])
            parent_dir = self.skills_root / parent_path
            parent_meta_path = parent_dir / "metadata.json"
            parent_file_path = self.skills_root / f"{parent_path}.json"

            if parent_meta_path.exists():
                parent_skills.append(
                    {"path": parent_path, "metadata": json.loads(parent_meta_path.read_text())}
                )
            elif parent_file_path.exists():
                parent_skills.append(
                    {"path": parent_path, "metadata": json.loads(parent_file_path.read_text())}
                )

        return parent_skills

    def register_skill(
        self,
        path: str,
        metadata: dict[str, Any],
        content: str,
        evolution: dict[str, Any],
    ) -> bool:
        """Register a new skill in the taxonomy."""
        skill_dir = self.skills_root / path
        skill_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(tz=UTC).isoformat()

        # Write metadata
        metadata_path = skill_dir / "metadata.json"
        metadata.setdefault("skill_id", path)
        metadata["created_at"] = metadata.get("created_at", now)
        metadata["last_modified"] = now
        metadata["evolution"] = evolution

        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

        # Write main content
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

        # Create subdirectories
        (skill_dir / "capabilities").mkdir(exist_ok=True)
        (skill_dir / "examples").mkdir(exist_ok=True)
        (skill_dir / "tests").mkdir(exist_ok=True)
        (skill_dir / "resources").mkdir(exist_ok=True)

        # Update cache
        skill_id = metadata["skill_id"]
        self.metadata_cache[skill_id] = SkillMetadata(
            skill_id=skill_id,
            version=metadata["version"],
            type=metadata["type"],
            weight=metadata["weight"],
            load_priority=metadata["load_priority"],
            dependencies=list(metadata.get("dependencies", [])),
            capabilities=list(metadata.get("capabilities", [])),
            path=metadata_path,
            always_loaded=bool(metadata.get("always_loaded", False)),
        )

        # Update taxonomy meta
        self._update_taxonomy_stats(metadata)

        return True

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
        # Directory-form skill
        skill_dir = self.skills_root / skill_id
        if (skill_dir / "metadata.json").exists():
            return self._load_skill_dir_metadata(skill_dir)

        # Single-file skill
        skill_file = self.skills_root / f"{skill_id}.json"
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
