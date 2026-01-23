"""FastAPI app configuration.

This module provides configuration for the FastAPI application.
It delegates to the existing API configuration in skill_fleet.api.config.

The app layer exists to provide a clean separation between the
application entry point (app/) and internal API implementation (api/).
"""

from __future__ import annotations

from functools import lru_cache

from ..api.config import APISettings, get_settings

__all__ = ["APISettings", "get_settings"]
