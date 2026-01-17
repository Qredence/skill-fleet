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
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..analytics.engine import UsageTracker
from ..common.security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)
from .models import TaxonomyIndex

logger = logging.getLogger(__name__)

# ============================================================================
# agentskills.io Naming Utilities
# ============================================================================


def skill_id_to_name(skill_id: str) -> str:
    """Convert path-style skill_id to kebab-case name per agentskills.io spec.

    Examples:
        'technical_skills/programming/languages/python/python-decorators' -> 'python-decorators'
        '_core/reasoning' -> 'core-reasoning'
        'mcp_capabilities/tool_integration' -> 'tool-integration'

    The name must match the skill directory name, so it is derived from the
    last path segment only.
    """
    # Remove leading underscores from path segments
    parts = [p.lstrip("_") for p in skill_id.split("/")]

    # Take the last segment (directory name) for spec compliance.
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

    def resolve_skill_location(self, skill_identifier: str) -> str:
        """Resolve a skill identifier (ID, path, or alias) to its canonical storage path.

        This implements the polyfill strategy:
        1. Check Index (canonical ID or alias).
        2. Fallback to Filesystem (legacy support).
        """
        # 1. Check Index direct match
        if skill_identifier in self.index.skills:
            return self.index.skills[skill_identifier].canonical_path

        # 1b. Check Index aliases
        for skill_id, entry in self.index.skills.items():
            if skill_identifier in entry.aliases:
                logger.warning(
                    f"Deprecation Warning: Accessing skill via alias '{skill_identifier}'. "
                    f"Use canonical ID '{skill_id}' instead."
                )
                return entry.canonical_path

        # 2. Filesystem Fallback
        # Check if the identifier looks like a valid path that exists on disk
        safe_path = sanitize_taxonomy_path(skill_identifier)
        if safe_path:
            full_path = resolve_path_within_root(self.skills_root, safe_path)

            # Check directory-style skill
            if full_path.exists() and (full_path / "metadata.json").exists():
                if "_drafts" not in safe_path:
                    logger.warning(
                        f"Legacy Access: Skill '{skill_identifier}' found on disk (dir) but missing from Taxonomy Index."
                    )
                return safe_path

            # Check single-file skill
            json_path = full_path.with_suffix(".json")
            if json_path.exists():
                if "_drafts" not in safe_path:
                    logger.warning(
                        f"Legacy Access: Skill '{skill_identifier}' found on disk (json) but missing from Taxonomy Index."
                    )
                return safe_path

        # Not found
        raise FileNotFoundError(f"Skill '{skill_identifier}' not found in index or filesystem.")

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
            load_priority=skill_data.get("load_priority", "on_demand"),
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
            load_priority=skill_data.get("load_priority", "on_demand"),
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
        try:
            self.resolve_skill_location(taxonomy_path)
            return True
        except FileNotFoundError:
            return False

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
        safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
        if safe_taxonomy_path is None:
            return []

        path_parts = safe_taxonomy_path.split("/")
        parent_skills: list[dict[str, Any]] = []

        # Walk up the tree, searching for metadata.json or single-file JSON skills.
        for i in range(len(path_parts) - 1, 0, -1):
            parent_path = "/".join(path_parts[:i])
            parent_dir = resolve_path_within_root(self.skills_root, parent_path)
            parent_meta_path = parent_dir / "metadata.json"
            parent_file_path = resolve_path_within_root(self.skills_root, f"{parent_path}.json")

            if parent_meta_path.exists():
                parent_skills.append(
                    {
                        "path": parent_path,
                        "metadata": json.loads(parent_meta_path.read_text(encoding="utf-8")),
                    }
                )
            elif parent_file_path.exists():
                parent_skills.append(
                    {
                        "path": parent_path,
                        "metadata": json.loads(parent_file_path.read_text(encoding="utf-8")),
                    }
                )

        return parent_skills

    def register_skill(
        self,
        path: str,
        metadata: dict[str, Any],
        content: str,
        evolution: dict[str, Any],
        extra_files: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> bool:
        """Register a new skill in the taxonomy.

        Creates an agentskills.io compliant skill with YAML frontmatter in SKILL.md
        and extended metadata in metadata.json.
        """
        safe_path = sanitize_taxonomy_path(path)
        if safe_path is None:
            return False

        skill_dir = resolve_path_within_root(self.skills_root, safe_path)
        if (skill_dir / "metadata.json").exists() and not overwrite:
            return False
        skill_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(tz=UTC).isoformat()

        # Ensure skill_id is set
        metadata.setdefault("skill_id", safe_path)
        skill_id = metadata["skill_id"]

        # Ensure metadata.json contains required taxonomy fields (aligns with config/templates).
        metadata.setdefault("version", "1.0.0")
        metadata.setdefault("type", "technical")
        metadata.setdefault("weight", "medium")
        metadata.setdefault("load_priority", "on_demand")

        if not isinstance(metadata.get("dependencies"), list):
            metadata["dependencies"] = []
        if not isinstance(metadata.get("capabilities"), list):
            metadata["capabilities"] = []
        if not isinstance(metadata.get("tags"), list):
            metadata["tags"] = []
        if not metadata.get("category"):
            if "/" in path:
                metadata["category"] = "/".join(path.split("/")[:-1])

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

        # Populate extra files if provided
        # Note: Directories are now created lazily in _write_extra_files()
        # only when there is actual content to write.
        if extra_files:
            self._write_extra_files(skill_dir, extra_files)

        # Update cache
        self.metadata_cache[skill_id] = SkillMetadata(
            skill_id=skill_id,
            version=metadata.get("version", "1.0.0"),
            type=metadata.get("type", "technical"),
            weight=metadata.get("weight", "medium"),
            load_priority=metadata.get("load_priority", "on_demand"),
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
                    # Skip invalid skills - they may have malformed metadata
                    pass

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

    def _create_skill_subdirectories(self, skill_dir: Path, skill_name: str) -> None:
        """Create standard skill subdirectories with README.md files.

        Creates the following structure:
        - capabilities/README.md
        - examples/README.md
        - tests/README.md
        - resources/README.md
        - references/README.md, quick-start.md, common-patterns.md, api-reference.md, troubleshooting.md
        - scripts/README.md
        - assets/README.md
        """
        # Define subdirectories and their README content
        subdirs = {
            "capabilities": f"# Capabilities\n\nCapability implementations for `{skill_name}`.\n\nEach file in this directory documents a specific capability provided by this skill.\n",
            "examples": f"# Examples\n\nUsage examples for `{skill_name}`.\n\nEach file demonstrates a specific use case or pattern.\n",
            "tests": f"# Tests\n\nIntegration tests for `{skill_name}`.\n\nThese tests verify the skill's capabilities work as expected.\n",
            "resources": f"# Resources\n\nResource files for `{skill_name}`.\n\nIncludes configuration files, data files, and other resources needed by the skill.\n",
            "references": f"# References\n\nReference documentation for `{skill_name}`.\n\n## Contents\n\n- [Quick Start](quick-start.md) - Get started quickly\n- [Common Patterns](common-patterns.md) - Frequently used patterns\n- [API Reference](api-reference.md) - Detailed API documentation\n- [Troubleshooting](troubleshooting.md) - Common issues and solutions\n",
            "scripts": f"# Scripts\n\nUtility scripts for `{skill_name}`.\n\nThese scripts help with setup, maintenance, or automation tasks.\n",
            "assets": f"# Assets\n\nStatic assets for `{skill_name}`.\n\nIncludes images, diagrams, and other static files.\n",
        }

        # Create each subdirectory with README.md
        for subdir, readme_content in subdirs.items():
            subdir_path = skill_dir / subdir
            subdir_path.mkdir(exist_ok=True)
            readme_path = subdir_path / "README.md"
            if not readme_path.exists():
                readme_path.write_text(readme_content, encoding="utf-8")

        # Create reference documentation templates
        references_dir = skill_dir / "references"

        quick_start_content = f"""# Quick Start Guide

Get started with `{skill_name}` in minutes.

## Prerequisites

- List prerequisites here

## Installation

```bash
# Installation steps
```

## Basic Usage

```python
# Basic usage example
```

## Next Steps

- See [Common Patterns](common-patterns.md) for more examples
- Check [API Reference](api-reference.md) for detailed documentation
"""

        common_patterns_content = f"""# Common Patterns

Frequently used patterns with `{skill_name}`.

## Pattern 1: Basic Usage

Description of the pattern.

```python
# Example code
```

## Pattern 2: Advanced Usage

Description of the pattern.

```python
# Example code
```

## Anti-Patterns

Things to avoid when using this skill.
"""

        api_reference_content = f"""# API Reference

Detailed API documentation for `{skill_name}`.

## Core Functions

### function_name

```python
def function_name(param1: type, param2: type) -> return_type:
    \"\"\"Description of the function.\"\"\"
```

**Parameters:**
- `param1`: Description
- `param2`: Description

**Returns:** Description of return value

**Example:**
```python
# Usage example
```

## Classes

### ClassName

Description of the class.

#### Methods

- `method_name()`: Description
"""

        troubleshooting_content = f"""# Troubleshooting

Common issues and solutions for `{skill_name}`.

## Common Issues

### Issue 1: Description

**Symptoms:** What you might see

**Cause:** Why this happens

**Solution:** How to fix it

```python
# Fix example
```

### Issue 2: Description

**Symptoms:** What you might see

**Cause:** Why this happens

**Solution:** How to fix it

## Getting Help

If you encounter issues not covered here:
1. Check the [API Reference](api-reference.md)
2. Review [Common Patterns](common-patterns.md)
3. Search existing issues
"""

        # Write reference documentation files if they don't exist
        ref_files = {
            "quick-start.md": quick_start_content,
            "common-patterns.md": common_patterns_content,
            "api-reference.md": api_reference_content,
            "troubleshooting.md": troubleshooting_content,
        }

        for filename, content in ref_files.items():
            file_path = references_dir / filename
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    def _write_extra_files(self, skill_dir: Path, extra_files: dict[str, Any]) -> None:
        """Populate skill subdirectories with additional content.

        Only creates directories when there is actual content to write.
        """
        # Handle capability implementations
        if "capability_implementations" in extra_files:
            caps = extra_files["capability_implementations"]
            if isinstance(caps, str) and caps.strip().startswith(("{", "[")):
                try:
                    caps = json.loads(caps)
                except json.JSONDecodeError:
                    pass

            if isinstance(caps, dict):
                caps_dir = skill_dir / "capabilities"
                caps_dir.mkdir(exist_ok=True)
                for cap_id, cap_content in caps.items():
                    raw_name = f"{str(cap_id).replace('/', '_')}.md"
                    filename = raw_name if is_safe_path_component(raw_name) else "implementation.md"
                    (caps_dir / filename).write_text(str(cap_content), encoding="utf-8")
            else:
                caps_dir = skill_dir / "capabilities"
                caps_dir.mkdir(exist_ok=True)
                (caps_dir / "implementations.md").write_text(str(caps), encoding="utf-8")

        # Handle usage examples
        if "usage_examples" in extra_files:
            examples = extra_files["usage_examples"]
            if isinstance(examples, str) and examples.strip().startswith(("{", "[")):
                try:
                    examples = json.loads(examples)
                except json.JSONDecodeError:
                    pass

            if isinstance(examples, list):
                examples_dir = skill_dir / "examples"
                examples_dir.mkdir(exist_ok=True)
                for i, example in enumerate(examples):
                    if isinstance(example, dict):
                        content = example.get("code") or example.get("content")
                        if content:
                            ext = ".py" if "code" in example else ".md"
                            suggested = str(example.get("filename", "")).strip()
                            default_name = f"example_{i + 1}{ext}"
                            filename = (
                                suggested
                                if suggested and is_safe_path_component(suggested)
                                else default_name
                            )
                        else:
                            suggested = str(example.get("filename", "")).strip()
                            default_name = f"example_{i + 1}.json"
                            filename = (
                                suggested
                                if suggested and is_safe_path_component(suggested)
                                else default_name
                            )
                            content = json.dumps(example, indent=2)
                    else:
                        filename = f"example_{i + 1}.md"
                        content = str(example)
                    (examples_dir / filename).write_text(content, encoding="utf-8")
            else:
                examples_dir = skill_dir / "examples"
                examples_dir.mkdir(exist_ok=True)
                (examples_dir / "examples.md").write_text(str(examples), encoding="utf-8")

        # Handle tests
        if "integration_tests" in extra_files:
            tests = extra_files["integration_tests"]
            if isinstance(tests, str) and tests.strip().startswith(("{", "[")):
                try:
                    tests = json.loads(tests)
                except json.JSONDecodeError:
                    pass

            if isinstance(tests, list):
                tests_dir = skill_dir / "tests"
                tests_dir.mkdir(exist_ok=True)
                for i, test in enumerate(tests):
                    if isinstance(test, dict):
                        content = test.get("code") or test.get("content")
                        if content:
                            ext = ".py" if "code" in test else ".md"
                            suggested = str(test.get("filename", "")).strip()
                            default_name = f"test_{i + 1}{ext}"
                            filename = (
                                suggested
                                if suggested and is_safe_path_component(suggested)
                                else default_name
                            )
                        else:
                            suggested = str(test.get("filename", "")).strip()
                            default_name = f"test_{i + 1}.json"
                            filename = (
                                suggested
                                if suggested and is_safe_path_component(suggested)
                                else default_name
                            )
                            content = json.dumps(test, indent=2)
                    else:
                        filename = f"test_{i + 1}.py"
                        content = str(test)
                    (tests_dir / filename).write_text(content, encoding="utf-8")
            else:
                tests_dir = skill_dir / "tests"
                tests_dir.mkdir(exist_ok=True)
                (tests_dir / "test_skill.py").write_text(str(tests), encoding="utf-8")

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
            resources_dir = skill_dir / "resources"
            resources_dir.mkdir(exist_ok=True)
            filename = (
                "requirements.json"
                if isinstance(res, (dict, list))
                or (isinstance(res, str) and res.strip().startswith(("{", "[")))
                else "requirements.md"
            )
            (resources_dir / filename).write_text(str(res), encoding="utf-8")

        # Handle bundled resources (scripts, assets, resources)
        for category in ["scripts", "assets", "resources"]:
            if category in extra_files:
                items = extra_files[category]
                if isinstance(items, dict):
                    target_dir = skill_dir / category
                    target_dir.mkdir(parents=True, exist_ok=True)
                    for filename, content in items.items():
                        # Allow subdirectories, but sanitize and enforce containment.
                        sanitized = sanitize_relative_file_path(str(filename))
                        if sanitized is None:
                            continue
                        file_path = resolve_path_within_root(target_dir, sanitized)
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        if isinstance(content, bytes):
                            file_path.write_bytes(content)
                        else:
                            file_path.write_text(str(content), encoding="utf-8")

    def _lint_and_format_skill(self, skill_dir: Path) -> None:
        """Lint and format Python files in generated skill directory.

        Runs ruff linting and formatting on all Python files in the skill's
        examples/ and scripts/ subdirectories to ensure code quality.

        Args:
            skill_dir: Path to skill directory
        """
        python_files = []
        examples_dir = skill_dir / "examples"
        scripts_dir = skill_dir / "scripts"

        # Collect Python files from examples/
        if examples_dir.exists():
            python_files.extend(examples_dir.rglob("*.py"))

        # Collect Python files from scripts/
        if scripts_dir.exists():
            python_files.extend(scripts_dir.rglob("*.py"))

        if not python_files:
            return

        # Run ruff check (linting)
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "check"] + [str(f) for f in python_files],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(f"Linting issues found in skill {skill_dir.name}: {result.stdout}")
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.warning(f"Failed to lint skill {skill_dir.name}: {e}")

        # Run ruff format
        try:
            result = subprocess.run(
                ["uv", "run", "ruff", "format"] + [str(f) for f in python_files],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                logger.warning(
                    f"Formatting issues found in skill {skill_dir.name}: {result.stdout}"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.warning(f"Failed to format skill {skill_dir.name}: {e}")

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
