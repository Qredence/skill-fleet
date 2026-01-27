"""
Path resolution utilities for taxonomy management.

Provides methods for resolving skill identifiers to their canonical storage paths,
with support for aliases and filesystem fallback for legacy support.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from ..common.security import (
    resolve_path_within_root,
    sanitize_taxonomy_path,
)

if TYPE_CHECKING:
    from pathlib import Path

    from .models import TaxonomyIndex

logger = logging.getLogger(__name__)


def resolve_skill_location(
    skill_identifier: str,
    skills_root: Path,
    index: TaxonomyIndex,
) -> str:
    """
    Resolve a skill identifier (ID, path, or alias) to its canonical storage path.

    This implements the polyfill strategy:
    1. Check Index (canonical ID or alias).
    2. Fallback to Filesystem (legacy support).

    Args:
        skill_identifier: The skill ID, path, or alias to resolve
        skills_root: Root directory of the taxonomy
        index: Taxonomy index containing canonical paths and aliases

    Returns:
        Canonical storage path for the skill

    Raises:
        FileNotFoundError: If skill cannot be found in index or filesystem

    """
    # 1. Check Index direct match
    if skill_identifier in index.skills:
        return index.skills[skill_identifier].canonical_path

    # 1b. Check Index aliases
    for skill_id, entry in index.skills.items():
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
        full_path = resolve_path_within_root(skills_root, safe_path)

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


def get_parent_skills(
    taxonomy_path: str,
    skills_root: Path,
) -> list[dict[str, Any]]:
    """
    Get parent and sibling skills for context.

    Walks up the taxonomy tree, searching for metadata.json or single-file JSON skills.

    Args:
        taxonomy_path: The taxonomy path to get parents for
        skills_root: Root directory of the taxonomy

    Returns:
        List of parent skill metadata dictionaries with 'path' and 'metadata' keys

    """
    import json

    from ..common.security import resolve_path_within_root, sanitize_taxonomy_path

    safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_taxonomy_path is None:
        return []

    path_parts = safe_taxonomy_path.split("/")
    parent_skills: list[dict[str, Any]] = []

    # Walk up the tree, searching for metadata.json or single-file JSON skills.
    for i in range(len(path_parts) - 1, 0, -1):
        parent_path = "/".join(path_parts[:i])
        parent_dir = resolve_path_within_root(skills_root, parent_path)
        parent_meta_path = parent_dir / "metadata.json"
        parent_file_path = resolve_path_within_root(skills_root, f"{parent_path}.json")

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


def get_branch_structure(
    branch_path: str,
    skills_root: Path,
) -> dict[str, str]:
    """
    Get directory structure of a taxonomy branch.

    Args:
        branch_path: The branch path to get structure for
        skills_root: Root directory of the taxonomy

    Returns:
        Dictionary mapping subdirectory names to "available" status

    """
    from ..common.security import resolve_path_within_root, sanitize_taxonomy_path

    safe_branch_path = sanitize_taxonomy_path(branch_path)
    if safe_branch_path is None:
        return {}

    full_path = resolve_path_within_root(skills_root, safe_branch_path)
    if not full_path.exists():
        return {}

    structure: dict[str, str] = {}
    for item in full_path.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            structure[item.name] = "available"
    return structure
