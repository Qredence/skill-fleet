"""
API v2 routes.

Re-exports routes from existing api.routes during migration period.
After migration, implementations will move here.
"""

from __future__ import annotations

# Re-export from existing api.routes during migration
from skill_fleet.api.routes import (
    chat_streaming,
    drafts,
    evaluation,
    hitl,
    jobs,
    optimization,
    skills,
    taxonomy,
    training,
    validation,
)

__all__ = [
    "chat_streaming",
    "drafts",
    "evaluation",
    "hitl",
    "jobs",
    "optimization",
    "skills",
    "taxonomy",
    "training",
    "validation",
]
