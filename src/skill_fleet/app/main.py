"""
FastAPI application entry point for Skills Fleet.

This module provides the main FastAPI application factory and instance.
The FastAPI app is the primary interface for all skill-fleet operations.

Usage:
    # Run with uvicorn
    uvicorn skill_fleet.app.main:app --reload

    # Or via CLI
    skill-fleet serve

    # Programmatic usage
    from skill_fleet.app import create_app
    app = create_app()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function creates the FastAPI app with all routes,
    middleware, and configurations.

    Returns:
        FastAPI: The configured application instance.

    Example:
        >>> app = create_app()
        >>> # Use with uvicorn
        >>> import uvicorn
        >>> uvicorn.run(app, host="0.0.0.0", port=8000)

    """
    from .factory import create_app as _create_app

    return _create_app()


def get_app() -> FastAPI:
    """
    Get or create the FastAPI application instance (cached).

    Returns:
        FastAPI: Cached application instance.

    """
    from .factory import get_app as _get_app

    return _get_app()


# Module-level app instance for uvicorn compatibility
# Usage: uvicorn skill_fleet.app.main:app
app = get_app()
