"""Security utilities for path validation and sanitization.

This module provides centralized security functions for validating and sanitizing
user-provided paths to prevent path traversal attacks and ensure paths remain
within expected boundaries.
"""

from __future__ import annotations

from pathlib import Path


def sanitize_taxonomy_path(path: str) -> str | None:
    """Sanitize a taxonomy path to prevent traversal attacks.

    Validates and normalizes a taxonomy-relative path to ensure it:
    - Is not empty
    - Does not start with `/` (absolute path)
    - Does not contain `..` (parent directory traversal)
    - Contains only alphanumeric characters, hyphens, and underscores in each segment

    Args:
        path: The raw taxonomy path from user input or workflow output

    Returns:
        Sanitized path as a POSIX-style string, or None if invalid

    Examples:
        >>> sanitize_taxonomy_path("technical_skills/programming/python")
        'technical_skills/programming/python'
        >>> sanitize_taxonomy_path("/absolute/path")
        None
        >>> sanitize_taxonomy_path("../traversal")
        None
        >>> sanitize_taxonomy_path("path/with spaces")
        None
    """
    if not path:
        return None

    # Reject absolute paths and parent-directory traversal
    if path.startswith("/") or ".." in path:
        return None

    # Normalize and ensure it remains within expected boundaries
    normalized = Path(path).as_posix().strip("/")

    # Validate each path segment with character whitelist
    for segment in normalized.split("/"):
        if not segment:
            return None
        # Allow letters, numbers, hyphen, underscore only
        if not all(c.isalnum() or c in "-_" for c in segment):
            return None

    return normalized


def is_safe_path_component(component: str) -> bool:
    """Validate that a single path component is safe.

    A safe component:
    - Is not empty
    - Does not contain path separators (/ or \\)
    - Does not contain null bytes
    - Is not "." or ".."
    - Contains only alphanumeric characters, dots, hyphens, and underscores

    Args:
        component: A single path component (filename or directory name)

    Returns:
        True if the component is safe, False otherwise

    Examples:
        >>> is_safe_path_component("valid_name.py")
        True
        >>> is_safe_path_component("..")
        False
        >>> is_safe_path_component("path/traversal")
        False
    """
    if not component:
        return False

    if "\0" in component:
        return False

    if "/" in component or "\\" in component:
        return False

    if component in (".", ".."):
        return False

    if ".." in component:
        return False

    # Allow alphanumeric, dot, hyphen, underscore
    return all(c.isalnum() or c in "._-" for c in component)


__all__ = ["sanitize_taxonomy_path", "is_safe_path_component"]
