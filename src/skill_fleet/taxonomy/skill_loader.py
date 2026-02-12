"""
Skill loading utilities for taxonomy management.

Handles loading skill metadata from various storage formats:
- Single-file JSON skills
- Directory-based skills with metadata.json
- agentskills.io compliant skills with YAML frontmatter
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Callable


from .metadata import InfrastructureSkillMetadata
from .naming import skill_id_to_name

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def load_skill_file(skill_file: Path) -> InfrastructureSkillMetadata:
    """
    Load a skill definition stored as a single JSON file.

    Args:
        skill_file: Path to the JSON skill file

    Returns:
        InfrastructureSkillMetadata object containing the skill's metadata

    """
    skill_data = json.loads(skill_file.read_text(encoding="utf-8"))
    skill_id = skill_data["skill_id"]

    # Generate name from skill_id if not present
    name = skill_data.get("name") or skill_id_to_name(skill_id)
    description = skill_data.get("description", "")

    metadata = InfrastructureSkillMetadata(
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
    return metadata


def load_skill_dir_metadata(skill_dir: Path) -> InfrastructureSkillMetadata:
    """
    Load a skill definition stored as a directory containing `metadata.json`.

    Also attempts to parse YAML frontmatter from SKILL.md for agentskills.io
    compliant skills.

    Args:
        skill_dir: Path to the skill directory

    Returns:
        InfrastructureSkillMetadata object containing the skill's metadata

    """
    metadata_path = skill_dir / "metadata.json"
    skill_data = json.loads(metadata_path.read_text(encoding="utf-8"))
    skill_id = skill_data["skill_id"]

    # Try to get name/description from SKILL.md frontmatter first
    skill_md_path = skill_dir / "SKILL.md"
    frontmatter = {}
    if skill_md_path.exists():
        frontmatter = parse_skill_frontmatter(skill_md_path)

    # Use frontmatter values, fall back to metadata.json, then generate
    name = frontmatter.get("name") or skill_data.get("name") or skill_id_to_name(skill_id)
    description = frontmatter.get("description") or skill_data.get("description", "")

    metadata = InfrastructureSkillMetadata(
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
    return metadata


def parse_skill_frontmatter(skill_md_path: Path) -> dict[str, Any]:
    """
    Parse YAML frontmatter from a SKILL.md file.

    Args:
        skill_md_path: Path to the SKILL.md file

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

    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Failed to parse frontmatter from {skill_md_path}: {e}")
        return {}


def try_load_skill_by_id(
    skill_id: str,
    skills_root: Path,
    resolve_func: Callable,
) -> InfrastructureSkillMetadata | None:
    """
    Try to load skill metadata from disk by skill ID.

    Attempts to load from both directory-form and single-file skill formats.

    Args:
        skill_id: The skill identifier to load
        skills_root: Root directory of the taxonomy
        resolve_func: Function to resolve skill ID to canonical path

    Returns:
        InfrastructureSkillMetadata if found, None otherwise

    """
    from ..common.security import resolve_path_within_root

    try:
        canonical_path = resolve_func(skill_id)
    except FileNotFoundError:
        return None

    # Directory-form skill
    skill_dir = resolve_path_within_root(skills_root, canonical_path)
    if (skill_dir / "metadata.json").exists():
        return load_skill_dir_metadata(skill_dir)

    # Single-file skill
    skill_file = resolve_path_within_root(skills_root, f"{canonical_path}.json")
    if skill_file.exists():
        return load_skill_file(skill_file)

    return None
