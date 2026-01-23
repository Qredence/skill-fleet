"""
Domain logic for Skills Fleet (non-DSPy business logic).

This package contains business logic independent of DSPy:

- skill/: Skill domain logic
  - creator.py: Skill creation orchestration
  - models.py: Domain models (SkillMetadata, etc.)
  - repository/: Skill storage/retrieval

- taxonomy/: Taxonomy management
  - manager.py: Adaptive taxonomy logic
  - adaptive.py: User-specific taxonomy adaptation

- quality/: Quality evaluation logic
  - evaluators.py: Quality evaluators
  - metrics.py: Quality metrics
"""

from __future__ import annotations

__all__: list[str] = []
