"""
Skill discovery and agentskills.io integration utilities.

Provides XML generation for agent context injection and skill discovery
capabilities following the agentskills.io integration standard.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from .naming import skill_id_to_name

if TYPE_CHECKING:
    from pathlib import Path

    from .metadata import InfrastructureSkillMetadata

logger = logging.getLogger(__name__)

_DISCOVERY_SCAN_INTERVAL_SECONDS = 30.0
_last_discovery_scan: dict[str, float] = {}
_discovery_scan_lock = threading.Lock()


def _should_scan(skills_root: Path) -> bool:
    """
    Determine whether discovery scan should run based on last scan time.

    Throttles repeated filesystem walks to reduce overhead on hot paths like
    list endpoints that call this helper frequently.
    """
    now = time.monotonic()
    root_key = str(skills_root.resolve())
    with _discovery_scan_lock:
        last_scan = _last_discovery_scan.get(root_key)
        if last_scan is not None and now - last_scan < _DISCOVERY_SCAN_INTERVAL_SECONDS:
            return False
        _last_discovery_scan[root_key] = now
        return True


def generate_available_skills_xml(
    metadata_cache: dict[str, InfrastructureSkillMetadata],
    skills_root: Path,
    user_id: str | None = None,
) -> str:
    """
    Generate <available_skills> XML for agent context injection.

    This XML format follows the agentskills.io integration standard
    for injecting skill metadata into agent system prompts.

    Args:
        metadata_cache: Dictionary mapping skill IDs to InfrastructureSkillMetadata
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
    metadata_cache: dict[str, InfrastructureSkillMetadata],
    load_dir_func: Callable,
) -> None:
    """
    Load all skills from disk into the metadata cache.

    Args:
        skills_root: Root directory of the taxonomy
        metadata_cache: Dictionary mapping skill IDs to InfrastructureSkillMetadata
        load_dir_func: Function to load skill directory metadata

    """
    if not _should_scan(skills_root):
        return

    # Single directory traversal to find both metadata.json and SKILL.md files
    candidate_dirs: set[Path] = set()
    for file_path in skills_root.rglob("*"):
        if file_path.is_file() and file_path.name in ("metadata.json", "SKILL.md"):
            candidate_dirs.add(file_path.parent)

    for skill_dir in sorted(candidate_dirs):
        skill_id = skill_dir.relative_to(skills_root).as_posix()
        # Skip system/internal branches (e.g. _drafts) from discoverable XML output.
        if any(part.startswith("_") for part in skill_dir.relative_to(skills_root).parts):
            continue
        if skill_id not in metadata_cache:
            try:
                load_dir_func(skill_dir)
            except (OSError, ValueError, KeyError) as exc:
                # Skip invalid skills - they may have malformed metadata
                logger.debug("Skipping invalid skill %s: %s", skill_dir, exc)


def get_skill_for_prompt(
    skill_id: str,
    metadata_cache: dict[str, InfrastructureSkillMetadata],
) -> str | None:
    """
    Get the full SKILL.md content for loading into an agent's context.

    This is the 'activation' step in the agentskills.io integration flow.

    Args:
        skill_id: The skill identifier
        metadata_cache: Dictionary mapping skill IDs to InfrastructureSkillMetadata

    Returns:
        Full SKILL.md content or None if not found

    """
    meta = metadata_cache.get(skill_id)
    if meta is None:
        return None

    # Determine SKILL.md path
    if meta.path.name == "metadata.json":
        skill_md_path = meta.path.parent / "SKILL.md"
    elif meta.path.name == "SKILL.md":
        # v2 skills can be represented directly by SKILL.md without metadata.json
        skill_md_path = meta.path
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
