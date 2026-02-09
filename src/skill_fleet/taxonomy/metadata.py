"""
Skill metadata models for taxonomy.

This module provides infrastructure-level dataclass models for skill metadata,
used for loading skills from disk (metadata.json, SKILL.md frontmatter).

NOTE: This is different from core.models.SkillMetadata:
- taxonomy.metadata.InfrastructureSkillMetadata: Infrastructure model with 'path' field
- core.models.SkillMetadata: Domain model without 'path' field (pure business)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class InfrastructureSkillMetadata:
    """
    Lightweight representation of a skill's metadata from disk.

    Used by skill_loader.py for loading skills from various formats:
    - Single-file JSON skills
    - Directory-based skills with metadata.json
    - agentskills.io compliant skills with YAML frontmatter

    Attributes:
        skill_id: Unique identifier (taxonomy path without leading slash)
        version: Semantic version string
        type: Skill category/type
        weight: Loading priority weight (light, medium, heavy)
        load_priority: When to load (always_loaded, on_demand, recommended)
        dependencies: List of skill_ids this skill depends on
        capabilities: List of capabilities provided by this skill
        path: File system path to the skill's metadata.json or SKILL.md
        always_loaded: Whether this is an always-loaded skill
        name: agentskills.io compliant kebab-case name
        description: Brief description of when to use this skill

    """

    skill_id: str
    version: str
    type: str
    weight: str
    load_priority: str
    dependencies: list[str]
    capabilities: list[str]
    path: Path
    always_loaded: bool = False
    # agentskills.io fields
    name: str = ""
    description: str = ""
