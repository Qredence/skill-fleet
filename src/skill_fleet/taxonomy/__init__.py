"""Taxonomy subsystem for the agentic skills system."""

from __future__ import annotations

# Export submodules for direct access if needed
from . import (
    discovery,
    metadata,
    naming,
    path_resolver,
    skill_loader,
    skill_registration,
)
from .manager import TaxonomyManager
from .metadata import InfrastructureSkillMetadata
from .naming import name_to_skill_id, skill_id_to_name, validate_skill_name

__all__ = [
    "TaxonomyManager",
    "InfrastructureSkillMetadata",
    "skill_id_to_name",
    "name_to_skill_id",
    "validate_skill_name",
    # Submodules
    "discovery",
    "metadata",
    "naming",
    "path_resolver",
    "skill_loader",
    "skill_registration",
]
