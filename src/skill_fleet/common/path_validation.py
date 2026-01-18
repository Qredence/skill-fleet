"""Path validation utilities for security and safe filesystem operations.

This module consolidates path validation logic from multiple locations to ensure
consistent security and prevent path traversal attacks.

Functions:
- sanitize_taxonomy_path: Validate taxonomy path segments
- sanitize_relative_file_path: Validate relative file paths
- resolve_path_within_root: Resolve path and verify it's within root
- resolve_skill_md_path: Atomic skill path resolution (TOCTOU-safe)
- is_safe_path_component: Check if a path component is safe
"""

from __future__ import annotations

import re
from pathlib import Path

# Pattern for detecting safe path components (no special characters that could be used for attacks)
SAFE_COMPONENT_PATTERN = re.compile(r"^[a-zA-Z0-9_.\-/]+$")


def sanitize_taxonomy_path(path: str) -> str | None:
    """Validate and sanitize a taxonomy path.

    Args:
        path: The taxonomy path to validate (e.g., "python/fastapi")

    Returns:
        Sanitized path if valid, None otherwise

    Examples:
        >>> sanitize_taxonomy_path("python/fastapi")
        "python/fastapi"
        >>> sanitize_taxonomy_path("../etc/passwd")
        None
        >>> sanitize_taxonomy_path("python/../../etc")
        None
    """
    if not path:
        return None

    # Normalize path separators
    path = path.replace("\\", "/")

    # Check for path traversal attempts
    if ".." in path or path.startswith("/"):
        return None

    # Check for empty segments
    segments = [s for s in path.split("/") if s]
    if not segments:
        return None

    # Validate each segment
    for segment in segments:
        if not is_safe_path_component(segment):
            return None

    return "/".join(segments)


def sanitize_relative_file_path(path: str) -> str | None:
    """Validate and sanitize a relative file path.

    Args:
        path: The relative file path to validate

    Returns:
        Sanitized path if valid, None otherwise

    Examples:
        >>> sanitize_relative_file_path("skills/python/async.md")
        "skills/python/async.md"
        >>> sanitize_relative_file_path("../config.yaml")
        None
    """
    if not path:
        return None

    # Normalize path separators
    path = path.replace("\\", "/")

    # Check for path traversal attempts
    if ".." in path:
        return None

    # Ensure path doesn't start with /
    if path.startswith("/"):
        return None

    # Validate each segment
    segments = [s for s in path.split("/") if s]
    for segment in segments:
        if not is_safe_path_component(segment):
            return None

    return "/".join(segments)


def resolve_path_within_root(root: Path, relative_path: str) -> Path:
    """Resolve a relative path within a root directory, ensuring safety.

    This function validates that the resolved absolute path is within
    the specified root directory to prevent path traversal attacks.

    Args:
        root: The root directory path (must be absolute and exist)
        relative_path: The relative path to resolve

    Returns:
        The resolved absolute path

    Raises:
        ValueError: If the path would escape the root directory
        FileNotFoundError: If the root directory doesn't exist
    """
    if not root.is_absolute():
        raise ValueError("Root must be an absolute path")

    if not root.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root}")

    # Resolve both paths to absolute form
    root_resolved = root.resolve()
    resolved = (root_resolved / relative_path).resolve()

    # Verify the resolved path is within root
    resolved.relative_to(root_resolved)

    return resolved


def resolve_skill_md_path(skills_root: Path, taxonomy_path: str) -> Path:
    """Resolve the path to a skill's SKILL.md file atomically.

    This function is TOCTOU (time-of-check-time-of-use) safe and
    prevents symlink-based path traversal attacks.

    Args:
        skills_root: Root directory for skills
        taxonomy_path: The taxonomy path to the skill (e.g., "python/fastapi")

    Returns:
        The absolute path to the SKILL.md file

    Raises:
        ValueError: If the path is invalid or escapes the skills root
        FileNotFoundError: If the SKILL.md file doesn't exist
    """
    # Sanitize and validate taxonomy path
    safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_taxonomy_path is None:
        raise ValueError("Invalid path")

    skills_root_resolved = skills_root.resolve()

    # Resolve path atomically to prevent TOCTOU attacks
    # resolve(strict=True) raises FileNotFoundError if path doesn't exist
    # and resolves symlinks automatically while preserving safety
    skill_dir = skills_root_resolved / safe_taxonomy_path
    candidate_md = skill_dir / "SKILL.md"

    # Atomic check: verify SKILL.md exists
    # Using resolve(strict=True) is safe against TOCTOU
    try:
        resolved_md = candidate_md.resolve(strict=True)
    except FileNotFoundError:
        raise FileNotFoundError(candidate_md.as_posix()) from None

    # Verify resolved path is within skills root (prevents symlink escapes)
    try:
        resolved_md.relative_to(skills_root_resolved)
    except ValueError as e:
        raise ValueError("Invalid path") from e

    return resolved_md


def is_safe_path_component(component: str) -> bool:
    """Check if a path component is safe (no special characters or patterns).

    Args:
        component: A single path component (e.g., "python", "fastapi")

    Returns:
        True if the component is safe, False otherwise

    Examples:
        >>> is_safe_path_component("python")
        True
        >>> is_safe_path_component(".hidden")
        False
        >>> is_safe_path_component("file:name")
        False
    """
    if not component:
        return False

    # Check for hidden files/directories (starting with .)
    if component.startswith("."):
        return False

    # Check for unsafe patterns using regex
    # Only allow alphanumeric, underscore, hyphen, and forward slash
    return bool(SAFE_COMPONENT_PATTERN.match(component))
