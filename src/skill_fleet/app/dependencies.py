"""
FastAPI app dependencies.

This module provides dependency injection for the app layer.
It delegates to the existing API dependencies in skill_fleet.api.dependencies.

The app layer exists to provide a clean separation between the
application entry point (app/) and internal API implementation (api/).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends

from ..api.dependencies import (
    get_drafts_root as _get_drafts_root,
)
from ..api.dependencies import (
    get_skills_root as _get_skills_root,
)
from ..api.dependencies import (
    get_taxonomy_manager as _get_taxonomy_manager,
)


# Re-export dependencies for app layer
# These wrap the existing API dependencies
def get_settings():
    """Get API settings."""
    from ..api.config import get_settings as _get_settings
    return _get_settings()


def get_skills_root() -> Path:
    """Get the configured skills root directory."""
    return _get_skills_root()


def get_drafts_root(skills_root: Annotated[Path, Depends(get_skills_root)]) -> Path:
    """Get the drafts root directory."""
    return _get_drafts_root(skills_root)


def get_taxonomy_manager(
    skills_root: Annotated[Path, Depends(get_skills_root)],
):
    """Get a TaxonomyManager instance."""
    return _get_taxonomy_manager(skills_root)


# Type aliases for use with Depends
DraftsRoot = Annotated[Path, Depends(get_drafts_root)]
SkillsRoot = Annotated[Path, Depends(get_skills_root)]
TaxonomyManagerDep = Annotated[Path, Depends(get_taxonomy_manager)]

__all__ = [
    "get_settings",
    "get_skills_root",
    "get_drafts_root",
    "get_taxonomy_manager",
    "DraftsRoot",
    "SkillsRoot",
    "TaxonomyManagerDep",
]
