"""
Agentic skills system.

This package provides a hierarchical, composable skills taxonomy plus a DSPy-powered
workflow for generating new skills on demand.
"""

from __future__ import annotations

from .taxonomy.manager import TaxonomyManager
from .taxonomy.metadata import InfrastructureSkillMetadata

__all__ = [
    "InfrastructureSkillMetadata",
    "TaxonomyManager",
]
