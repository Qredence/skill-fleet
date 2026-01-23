"""FastAPI app middleware.

This module provides custom middleware for the app layer.
It delegates to existing middleware in skill_fleet.api.middleware.

The app layer exists to provide a clean separation between the
application entry point (app/) and internal API implementation (api/).
"""

from __future__ import annotations

from ..api.middleware.logging import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
)

__all__ = ["ErrorHandlingMiddleware", "LoggingMiddleware"]
