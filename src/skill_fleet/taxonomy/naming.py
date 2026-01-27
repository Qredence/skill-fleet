"""
agentskills.io naming utilities for skill names and IDs.

This module provides utilities for converting between skill IDs,
taxonomy paths, and kebab-case names per the agentskills.io specification.

Requirements:
- Names must be 1-64 characters
- Lowercase letters, numbers, and hyphens only
- Must not start or end with hyphen
- No consecutive hyphens
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def skill_id_to_name(skill_id: str) -> str:
    """
    Convert path-style skill_id to kebab-case name per agentskills.io spec.

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
    """
    Convert kebab-case name back to skill_id given taxonomy context.

    The taxonomy_path is the canonical source of truth for the full ID.
    """
    return taxonomy_path


def validate_skill_name(name: str) -> tuple[bool, str | None]:
    """
    Validate skill name per agentskills.io spec.

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
        return False, "Name must be 64 characters or less"

    if len(name) < 1:
        return False, "Name must be at least 1 character"

    # Check for valid characters
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, "Name can only contain lowercase letters, numbers, and hyphens"

    # Must not start or end with hyphen
    if name.startswith("-") or name.endswith("-"):
        return False, "Name must not start or end with a hyphen"

    # No consecutive hyphens
    if "--" in name:
        return False, "Name must not contain consecutive hyphens"

    return True, None
