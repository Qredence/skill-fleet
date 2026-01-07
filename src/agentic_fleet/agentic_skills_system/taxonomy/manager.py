"""Taxonomy management for hierarchical skills.

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
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from ..analytics.engine import UsageTracker

# ============================================================================
# agentskills.io Naming Utilities
# ============================================================================


def skill_id_to_name(skill_id: str) -> str:
    """Convert path-style skill_id to kebab-case name per agentskills.io spec.

    Examples:
        'technical_skills/programming/languages/python/decorators' -> 'python-decorators'
        '_core/reasoning' -> 'core-reasoning'
        'mcp_capabilities/tool_integration' -> 'tool-integration'

    The name is derived from the last 1-2 path segments to keep it concise.
    """
    # Remove leading underscores from path segments
    parts = [p.lstrip("_") for p in skill_id.split("/")]

    # Take last 1-2 meaningful segments
    if len(parts) >= 2:
        # Use last two segments for context (e.g., 'python/decorators' -> 'python-decorators')
        name_parts = parts[-2:]
    else:
        name_parts = parts[-1:]

    # Convert underscores to hyphens and join
    name = "-".join(p.replace("_", "-") for p in name_parts)

    # Ensure lowercase and valid characters only
    name = re.sub(r"[^a-z0-9-]", "", name.lower())

    # Remove consecutive hyphens and trim
    name = re.sub(r"-+", "-", name).strip("-")

    # Truncate to 64 chars max per spec
    return name[:64]


def name_to_skill_id(name: str, taxonomy_path: str) -> str:
    """Convert kebab-case name back to skill_id given taxonomy context.

    The taxonomy_path is the canonical source of truth for the full ID.
    """
    return taxonomy_path


def validate_skill_name(name: str) -> tuple[bool, str | None]:
    """Validate skill name per agentskills.io spec.

    Requirements:
    - 1-64 characters
    - Lowercase letters, numbers, and hyphens only
    - Must not start or end with hyphen
    - No consecutive hyphens

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Name cannot be empty"

    if len(name) > 64:
        return False, f"Name exceeds 64 characters (got {len(name)})"

    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        return False, "Name must be lowercase alphanumeric with single hyphens between segments"

    return True, None


# ============================================================================
# Skill Metadata
# ============================================================================


@dataclass(frozen=True, slots=True)
class SkillMetadata:
    """Lightweight representation of a skill's metadata.

    Combines agentskills.io required fields (name, description) with
    extended fields for the hierarchical taxonomy system.
    """

    skill_id: str
    version: str
    type: str
    weight: str
    load_priority: str
    dependencies: list[str]
    capabilities: list[str]
    path: Path
    always_loaded: bool = False
    # agentskills.io fields
    name: str = ""
    description: str = ""


class TaxonomyManager:
    """Manages a hierarchical skill taxonomy stored on disk."""

    _ALWAYS_LOADED_DIRS = ("_core", "mcp_capabilities", "memory_blocks")

    def __init__(self, skills_root: Path) -> None:
        self.skills_root = Path(skills_root)
        self.meta_path = self.skills_root / "taxonomy_meta.json"
        self.metadata_cache: dict[str, SkillMetadata] = {}
        self.meta: dict[str, Any] = {}

        self.usage_tracker = UsageTracker(self.skills_root / "_analytics")

        self.load_taxonomy_meta()
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

        # Generate name from skill_id if not present
        name = skill_data.get("name") or skill_id_to_name(skill_id)
        description = skill_data.get("description", "")

        metadata = SkillMetadata(
            skill_id=skill_id,
            version=skill_data.get("version", "1.0.0"),
            type=skill_data.get("type", "technical"),
            weight=skill_data.get("weight", "medium"),
            load_priority=skill_data.get("load_priority", "normal"),
            dependencies=list(skill_data.get("dependencies", [])),
            capabilities=list(skill_data.get("capabilities", [])),
            path=skill_file,
            always_loaded=bool(skill_data.get("always_loaded", False)),
            name=name,
            description=description,
        )
        self.metadata_cache[skill_id] = metadata
        return metadata

    def _load_skill_dir_metadata(self, skill_dir: Path) -> SkillMetadata:
        """Load a skill definition stored as a directory containing `metadata.json`.

        Also attempts to parse YAML frontmatter from SKILL.md for agentskills.io
        compliant skills.
        """
        metadata_path = skill_dir / "metadata.json"
        skill_data = json.loads(metadata_path.read_text(encoding="utf-8"))
        skill_id = skill_data["skill_id"]

        # Try to get name/description from SKILL.md frontmatter first
        skill_md_path = skill_dir / "SKILL.md"
        frontmatter = {}
        if skill_md_path.exists():
            frontmatter = self.parse_skill_frontmatter(skill_md_path)

        # Use frontmatter values, fall back to metadata.json, then generate
        name = frontmatter.get("name") or skill_data.get("name") or skill_id_to_name(skill_id)
        description = frontmatter.get("description") or skill_data.get("description", "")

        metadata = SkillMetadata(
            skill_id=skill_id,
            version=skill_data.get("version", "1.0.0"),
            type=skill_data.get("type", "technical"),
            weight=skill_data.get("weight", "medium"),
            load_priority=skill_data.get("load_priority", "normal"),
            dependencies=list(skill_data.get("dependencies", [])),
            capabilities=list(skill_data.get("capabilities", [])),
            path=metadata_path,
            always_loaded=bool(skill_data.get("always_loaded", False)),
            name=name,
            description=description,
        )
        self.metadata_cache[skill_id] = metadata
        return metadata

    def parse_skill_frontmatter(self, skill_md_path: Path) -> dict[str, Any]:
        """Parse YAML frontmatter from a SKILL.md file.

        Returns:
            Dict with frontmatter fields (name, description, metadata, etc.)
            Empty dict if no valid frontmatter found.
        """
        try:
            content = skill_md_path.read_text(encoding="utf-8")

            # Check for YAML frontmatter (starts with ---)
            if not content.startswith("---"):
                return {}

            # Find the closing ---
            end_marker = content.find("---", 3)
            if end_marker == -1:
                return {}

            yaml_content = content[3:end_marker].strip()
            frontmatter = yaml.safe_load(yaml_content) or {}

            return frontmatter

        except Exception:
            return {}

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
        extra_files: dict[str, Any] | None = None,
    ) -> bool:
        """Register a new skill in the taxonomy.

        Creates an agentskills.io compliant skill with YAML frontmatter in SKILL.md
        and extended metadata in metadata.json.
        """
        skill_dir = self.skills_root / path
        skill_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(tz=UTC).isoformat()

        # Ensure skill_id is set
        metadata.setdefault("skill_id", path)
        skill_id = metadata["skill_id"]

        # Generate agentskills.io compliant name
        name = metadata.get("name") or skill_id_to_name(skill_id)
        metadata["name"] = name

        # Ensure description exists
        description = metadata.get("description", "")
        if not description:
            # Try to extract from content if it looks like markdown
            first_para = content.split("\n\n")[0] if content else ""
            # Strip markdown headers
            description = re.sub(r"^#.*\n?", "", first_para).strip()[:1024]
            metadata["description"] = description

        metadata["created_at"] = metadata.get("created_at", now)
        metadata["last_modified"] = now
        metadata["evolution"] = evolution

        # Write extended metadata to metadata.json
        metadata_path = skill_dir / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

        # Generate SKILL.md with agentskills.io compliant YAML frontmatter
        skill_md_content = self._generate_skill_md_with_frontmatter(
            name=name,
            description=description,
            metadata=metadata,
            content=content,
        )
        (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

        # Create subdirectories
        (skill_dir / "capabilities").mkdir(exist_ok=True)
        (skill_dir / "examples").mkdir(exist_ok=True)
        (skill_dir / "tests").mkdir(exist_ok=True)
        (skill_dir / "resources").mkdir(exist_ok=True)

        # Populate extra files if provided
        if extra_files:
            self._write_extra_files(skill_dir, extra_files)

        # Update cache
        self.metadata_cache[skill_id] = SkillMetadata(
            skill_id=skill_id,
            version=metadata.get("version", "1.0.0"),
            type=metadata.get("type", "technical"),
            weight=metadata.get("weight", "medium"),
            load_priority=metadata.get("load_priority", "normal"),
            dependencies=list(metadata.get("dependencies", [])),
            capabilities=list(metadata.get("capabilities", [])),
            path=metadata_path,
            always_loaded=bool(metadata.get("always_loaded", False)),
            name=name,
            description=description,
        )

        # Update taxonomy meta
        self._update_taxonomy_stats(metadata)

        return True

    def _generate_skill_md_with_frontmatter(
        self,
        name: str,
        description: str,
        metadata: dict[str, Any],
        content: str,
    ) -> str:
        """Generate SKILL.md content with agentskills.io compliant YAML frontmatter.

        Args:
            name: Kebab-case skill name
            description: Skill description (1-1024 chars)
            metadata: Extended metadata dict
            content: Original markdown content (may or may not have frontmatter)

        Returns:
            Complete SKILL.md content with proper frontmatter
        """
        # Strip existing frontmatter from content if present
        body_content = content
        if content.startswith("---"):
            end_marker = content.find("---", 3)
            if end_marker != -1:
                body_content = content[end_marker + 3 :].lstrip("\n")

        # Build frontmatter
        frontmatter = {
            "name": name,
            "description": description[:1024],  # Enforce max length
        }

        # Add optional extended metadata
        extended_meta = {}
        if metadata.get("skill_id"):
            extended_meta["skill_id"] = metadata["skill_id"]
        if metadata.get("version"):
            extended_meta["version"] = metadata["version"]
        if metadata.get("type"):
            extended_meta["type"] = metadata["type"]
        if metadata.get("weight"):
            extended_meta["weight"] = metadata["weight"]

        if extended_meta:
            frontmatter["metadata"] = extended_meta

        # Generate YAML frontmatter
        yaml_content = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

        return f"---\n{yaml_content}---\n\n{body_content}"

    # ========================================================================
    # agentskills.io Discoverability
    # ========================================================================

    def generate_available_skills_xml(self, user_id: str | None = None) -> str:
        """Generate <available_skills> XML for agent context injection.

        This XML format follows the agentskills.io integration standard
        for injecting skill metadata into agent system prompts.

        Args:
            user_id: Optional user ID to filter skills (not yet implemented)

        Returns:
            XML string following agentskills.io format
        """
        xml_parts = ["<available_skills>"]

        # Load all skills from disk if cache is incomplete
        self._ensure_all_skills_loaded()

        for skill_id, meta in sorted(self.metadata_cache.items()):
            # Get the SKILL.md path
            if meta.path.name == "metadata.json":
                skill_md_location = meta.path.parent / "SKILL.md"
            else:
                # Single-file skill (JSON), no SKILL.md
                skill_md_location = meta.path

            # Escape XML special characters
            name = self._xml_escape(meta.name or skill_id_to_name(skill_id))
            description = self._xml_escape(meta.description or "")
            location = self._xml_escape(str(skill_md_location))

            xml_parts.append(f"""  <skill>
    <name>{name}</name>
    <description>{description}</description>
    <location>{location}</location>
  </skill>""")

        xml_parts.append("</available_skills>")
        return "\n".join(xml_parts)

    def _ensure_all_skills_loaded(self) -> None:
        """Load all skills from disk into the metadata cache."""
        for skill_dir in self.skills_root.rglob("metadata.json"):
            skill_id = str(skill_dir.parent.relative_to(self.skills_root))
            if skill_id not in self.metadata_cache:
                try:
                    self._load_skill_dir_metadata(skill_dir.parent)
                except Exception:
                    pass  # Skip invalid skills

    def _xml_escape(self, text: str) -> str:
        """Escape special XML characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def get_skill_for_prompt(self, skill_id: str) -> str | None:
        """Get the full SKILL.md content for loading into an agent's context.

        This is the 'activation' step in the agentskills.io integration flow.

        Args:
            skill_id: The skill identifier

        Returns:
            Full SKILL.md content or None if not found
        """
        meta = self.get_skill_metadata(skill_id) or self._try_load_skill_by_id(skill_id)
        if meta is None:
            return None

        # Determine SKILL.md path
        if meta.path.name == "metadata.json":
            skill_md_path = meta.path.parent / "SKILL.md"
        else:
            # Single-file JSON skill
            return None

        if not skill_md_path.exists():
            return None

        return skill_md_path.read_text(encoding="utf-8")

    def _write_extra_files(self, skill_dir: Path, extra_files: dict[str, Any]) -> None:
        """Populate skill subdirectories with additional content."""
        # Handle capability implementations
        if "capability_implementations" in extra_files:
            caps = extra_files["capability_implementations"]
            if isinstance(caps, str) and caps.strip().startswith(("{", "[")):
                try:
                    caps = json.loads(caps)
                except json.JSONDecodeError:
                    pass

            if isinstance(caps, dict):
                for cap_id, cap_content in caps.items():
                    filename = f"{cap_id.replace('/', '_')}.md"
                    (skill_dir / "capabilities" / filename).write_text(
                        str(cap_content), encoding="utf-8"
                    )
            else:
                (skill_dir / "capabilities" / "implementations.md").write_text(
                    str(caps), encoding="utf-8"
                )

        # Handle usage examples
        if "usage_examples" in extra_files:
            examples = extra_files["usage_examples"]
            if isinstance(examples, str) and examples.strip().startswith(("{", "[")):
                try:
                    examples = json.loads(examples)
                except json.JSONDecodeError:
                    pass

            if isinstance(examples, list):
                for i, example in enumerate(examples):
                    if isinstance(example, dict):
                        content = example.get("code") or example.get("content")
                        if content:
                            ext = ".py" if "code" in example else ".md"
                            filename = example.get("filename", f"example_{i + 1}{ext}")
                        else:
                            filename = example.get("filename", f"example_{i + 1}.json")
                            content = json.dumps(example, indent=2)
                    else:
                        filename = f"example_{i + 1}.md"
                        content = str(example)
                    (skill_dir / "examples" / filename).write_text(content, encoding="utf-8")
            else:
                (skill_dir / "examples" / "examples.md").write_text(str(examples), encoding="utf-8")

        # Handle tests
        if "integration_tests" in extra_files:
            tests = extra_files["integration_tests"]
            if isinstance(tests, str) and tests.strip().startswith(("{", "[")):
                try:
                    tests = json.loads(tests)
                except json.JSONDecodeError:
                    pass

            if isinstance(tests, list):
                for i, test in enumerate(tests):
                    if isinstance(test, dict):
                        content = test.get("code") or test.get("content")
                        if content:
                            ext = ".py" if "code" in test else ".md"
                            filename = test.get("filename", f"test_{i + 1}{ext}")
                        else:
                            filename = test.get("filename", f"test_{i + 1}.json")
                            content = json.dumps(test, indent=2)
                    else:
                        filename = f"test_{i + 1}.py"
                        content = str(test)
                    (skill_dir / "tests" / filename).write_text(content, encoding="utf-8")
            else:
                (skill_dir / "tests" / "test_skill.py").write_text(str(tests), encoding="utf-8")

        # Handle best practices
        if "best_practices" in extra_files and extra_files["best_practices"]:
            bp = extra_files["best_practices"]
            if isinstance(bp, str) and bp.strip().startswith("["):
                try:
                    bp_list = json.loads(bp)
                    content = "## Best Practices\n\n" + "\n".join([f"- {item}" for item in bp_list])
                except (json.JSONDecodeError, TypeError):
                    content = str(bp)
            else:
                content = str(bp)
            (skill_dir / "best_practices.md").write_text(content, encoding="utf-8")

        # Handle integration guide
        if "integration_guide" in extra_files and extra_files["integration_guide"]:
            guide = extra_files["integration_guide"]
            (skill_dir / "integration.md").write_text(str(guide), encoding="utf-8")

        # Handle resources
        if "resource_requirements" in extra_files and extra_files["resource_requirements"]:
            res = extra_files["resource_requirements"]
            filename = (
                "requirements.json"
                if isinstance(res, (dict, list))
                or (isinstance(res, str) and res.strip().startswith(("{", "[")))
                else "requirements.md"
            )
            (skill_dir / "resources" / filename).write_text(str(res), encoding="utf-8")

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
