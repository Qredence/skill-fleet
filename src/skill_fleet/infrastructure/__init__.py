"""
Technical infrastructure for Skills Fleet.

This package contains technical concerns:

- config/: Configuration management
  - settings.py: Pydantic settings
  - profiles/: Configuration profiles
  - templates/: Configuration templates

- database/: Database layer (migrated from db/)
  - models.py: SQLAlchemy ORM models
  - repositories.py: Repository pattern implementations
  - database.py: Connection management

- messaging/: Event bus and messaging (future)
"""

from __future__ import annotations

__all__: list[str] = []
