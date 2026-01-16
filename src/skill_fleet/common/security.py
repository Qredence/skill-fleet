"""Security utilities for path validation and sanitization.

This module provides centralized security functions for validating and sanitizing
user-provided paths to prevent path traversal attacks and ensure paths remain
within expected boundaries.
"""

from __future__ import annotations

import os
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
    if path.startswith("/") or ".." in path or "\\" in path:
        return None

    # Filter and validate segments
    segments = []
    for segment in path.split("/"):
        s = segment.strip()
        if not s or s == ".":
            continue
        if s == "..":
            return None
        # Allow letters, numbers, hyphen, underscore only
        if not all(c.isalnum() or c in "-_" for c in s):
            return None
        segments.append(s)

    if not segments:
        return None

    return "/".join(segments)


def sanitize_relative_file_path(path: str) -> str | None:
    """Sanitize a relative file path to prevent traversal attacks.

    Validates and normalizes a relative path to ensure it:
    - Is not empty
    - Is not absolute
    - Does not contain Windows-style separators
    - Contains only safe path components (alphanumeric, dot, hyphen, underscore)
    - Does not contain "." or ".." components

    This is intended for user-controlled paths that are later joined onto a fixed
    server-side root directory.
    """
    if not path or "\0" in path:
        return None

    # Reject absolute paths and traversal to avoid ambiguities
    if path.startswith("/") or "\\" in path or ".." in path:
        return None

    segments = []
    for segment in path.split("/"):
        s = segment.strip()
        if not s or s == ".":
            continue
        if s == "..":
            return None
        if not is_safe_path_component(s):
            return None
        segments.append(s)

    if not segments:
        return None

    return "/".join(segments)


def resolve_path_within_root(root: Path, relative_path: str) -> Path:
    """Resolve a sanitized relative path under a root directory.

    Returns an absolute path and raises ValueError if the resolved path escapes
    the given root directory (including via `..` segments or symlink traversal).
    """
    sanitized = sanitize_relative_file_path(relative_path)
    if not sanitized:
        raise ValueError("Invalid relative path")

    root_resolved = root.resolve()
    candidate = root_resolved.joinpath(sanitized).resolve(strict=False)

    # Use os.path.commonpath for maximum robustness against CodeQL false positives.
    root_str = os.fspath(root_resolved)
    candidate_str = os.fspath(candidate)
    if os.path.commonpath([root_str, candidate_str]) != root_str:
        raise ValueError(f"Path escapes root: {candidate_str}")

    return candidate


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


__all__ = [
    "is_safe_path_component",
    "resolve_path_within_root",
    "sanitize_relative_file_path",
    "sanitize_taxonomy_path",
]
