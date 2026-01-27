"""
Skill discovery and agentskills.io integration utilities.

Provides XML generation for agent context injection and skill discovery
capabilities following the agentskills.io integration standard.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from .naming import skill_id_to_name

if TYPE_CHECKING:
    from pathlib import Path

    from .metadata import SkillMetadata

logger = logging.getLogger(__name__)


def generate_available_skills_xml(
    metadata_cache: dict[str, SkillMetadata],
    skills_root: Path,
    user_id: str | None = None,
) -> str:
    """
    Generate <available_skills> XML for agent context injection.

    This XML format follows the agentskills.io integration standard
    for injecting skill metadata into agent system prompts.

    Args:
        metadata_cache: Dictionary mapping skill IDs to SkillMetadata
        skills_root: Root directory of the taxonomy
        user_id: Optional user ID to filter skills (not yet implemented)

    Returns:
        XML string following agentskills.io format

    """
    xml_parts = ["<available_skills>"]

    for skill_id, meta in sorted(metadata_cache.items()):
        # Get the SKILL.md path
        if meta.path.name == "metadata.json":
            skill_md_location = meta.path.parent / "SKILL.md"
        else:
            # Single-file skill (JSON), no SKILL.md
            skill_md_location = meta.path

        # Escape XML special characters
        name = _xml_escape(meta.name or skill_id_to_name(skill_id))
        description = _xml_escape(meta.description or "")
        location = _xml_escape(str(skill_md_location))

        xml_parts.append(f"""  <skill>
    <name>{name}</name>
    <description>{description}</description>
    <location>{location}</location>
  </skill>""")

    xml_parts.append("</available_skills>")
    return "\n".join(xml_parts)


def ensure_all_skills_loaded(
    skills_root: Path,
    metadata_cache: dict[str, SkillMetadata],
    load_dir_func: Callable,
) -> None:
    """
    Load all skills from disk into the metadata cache.

    Args:
        skills_root: Root directory of the taxonomy
        metadata_cache: Dictionary mapping skill IDs to SkillMetadata
        load_dir_func: Function to load skill directory metadata

    """
    for skill_dir in skills_root.rglob("metadata.json"):
        skill_id = str(skill_dir.parent.relative_to(skills_root))
        if skill_id not in metadata_cache:
            try:
                load_dir_func(skill_dir.parent)
            except Exception:
                # Skip invalid skills - they may have malformed metadata
                pass


def get_skill_for_prompt(
    skill_id: str,
    metadata_cache: dict[str, SkillMetadata],
) -> str | None:
    """
    Get the full SKILL.md content for loading into an agent's context.

    This is the 'activation' step in the agentskills.io integration flow.

    Args:
        skill_id: The skill identifier
        metadata_cache: Dictionary mapping skill IDs to SkillMetadata

    Returns:
        Full SKILL.md content or None if not found

    """
    meta = metadata_cache.get(skill_id)
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


def _xml_escape(text: str) -> str:
    """
    Escape special XML characters.

    Args:
        text: Text to escape

    Returns:
        XML-escaped text

    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
