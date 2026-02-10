"""
Skills Fleet FastAPI Application.

This is the main application package. The FastAPI app serves as the primary
interface for skill creation, taxonomy management, and all DSPy workflows.

Directory Structure:
- main.py: FastAPI application entry point (module-level app for uvicorn)
- factory.py: Application factory functions
- config.py: Application configuration (Pydantic settings)
- dependencies.py: FastAPI dependency injection
- middleware/: Custom middleware (logging, auth, etc.)
- api/: API routes organized by domain
  - v1/: Versioned API routes
- schemas/: Pydantic request/response models
- services/: Business logic and service layer

Usage:
    # Run the server
    uvicorn skill_fleet.api.main:app --reload

    # Or via CLI
    skill-fleet serve
"""

from .factory import create_app, get_app

__all__ = ["create_app", "get_app"]
