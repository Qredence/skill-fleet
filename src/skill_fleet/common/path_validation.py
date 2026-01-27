"""
Path validation utilities - DEPRECATED.

This module is deprecated. All functions have been moved to security.py.
Import from security.py directly for new code.

This module is kept for backward compatibility and re-exports all functions
from security.py.
"""

from __future__ import annotations

import warnings

# Re-export all functions from security.py
from .security import (
    is_safe_path_component,
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)


# Deprecated alias for backward compatibility
def resolve_skill_md_path(skills_root, taxonomy_path):
    """
    Resolve the path to a skill's SKILL.md file.

    DEPRECATED: Use resolve_path_within_root() directly instead.
    """
    warnings.warn(
        "resolve_skill_md_path is deprecated, use resolve_path_within_root directly",
        DeprecationWarning,
        stacklevel=2,
    )

    safe_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_path is None:
        raise ValueError("Invalid taxonomy path")

    skill_dir = skills_root / safe_path
    candidate_md = skill_dir / "SKILL.md"

    if not candidate_md.exists():
        raise FileNotFoundError(candidate_md)

    return candidate_md.resolve()


__all__ = [
    "is_safe_path_component",
    "resolve_path_within_root",
    "resolve_skill_md_path",
    "sanitize_relative_file_path",
    "sanitize_taxonomy_path",
]
