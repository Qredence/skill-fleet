"""
Skill Fleet API module.

Provides FastAPI server for skill creation with real-time streaming.
"""

from __future__ import annotations

from .app import get_app

# Import app at module level (calls get_app() which uses lazy caching)
app = get_app()

__all__ = ["app", "get_app"]
