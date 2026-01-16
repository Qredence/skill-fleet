"""Pydantic models for the Taxonomy Index system.

These models define the structure of the `taxonomy_index.json` file,
which serves as the canonical source of truth for the skill taxonomy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class CategoryNode(BaseModel):
    """A node in the logical taxonomy tree."""

    description: str | None = Field(default=None, description="Description of this category")
    children: dict[str, CategoryNode] = Field(
        default_factory=dict, description="Child categories keyed by slug"
    )


class SkillEntry(BaseModel):
    """An entry in the flat skill inventory."""

    canonical_path: str = Field(
        description="The current primary filesystem path relative to skills/ root"
    )
    taxonomy_location: str | None = Field(
        default=None,
        description="Dot-notation path in the logical taxonomy tree (e.g. 'python.async')",
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="List of legacy or alternative paths that resolve to this skill",
    )
    facets: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value tags for filtering (e.g., lang:python, type:pattern)",
    )
    status: Literal["active", "deprecated", "draft"] = Field(default="active")


class TaxonomyIndex(BaseModel):
    """The root model for taxonomy_index.json."""

    version: str = Field(default="1.0", description="Schema version")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
    taxonomy_tree: dict[str, CategoryNode] = Field(
        default_factory=dict, description="The logical taxonomy tree structure"
    )
    skills: dict[str, SkillEntry] = Field(
        default_factory=dict,
        description="Flat inventory of skills mapped by unique skill_id",
    )
