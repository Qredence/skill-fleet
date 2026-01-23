"""
Taxonomy domain logic.

This package contains the adaptive taxonomy management:
- manager.py: Core taxonomy management
- adaptive.py: User-specific taxonomy adaptation
"""

from __future__ import annotations

# Re-export from existing location during migration
from skill_fleet.taxonomy.manager import TaxonomyManager

__all__ = ["TaxonomyManager"]
