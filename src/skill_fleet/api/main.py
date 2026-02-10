"""
FastAPI application entry point for Skills Fleet.

This module provides the main FastAPI application instance for production use.
The FastAPI app is the primary interface for all skill-fleet operations.

Usage:
    # Run with uvicorn
    uvicorn skill_fleet.api.main:app --reload

    # Or via CLI
    skill-fleet serve

    # Programmatic usage (testing)
    from skill_fleet.api.factory import create_app
    app = create_app()
"""

from __future__ import annotations

from .factory import create_app

# Module-level app instance for uvicorn compatibility
# This is the only module-level app creation in the codebase
# Usage: uvicorn skill_fleet.api.main:app
app = create_app()
