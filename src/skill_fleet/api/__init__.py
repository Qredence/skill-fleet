"""
Skills Fleet FastAPI Application.

This is the main application package. The FastAPI app serves as the primary
interface for skill creation, taxonomy management, and all DSPy workflows.

Directory Structure:
- factory.py: FastAPI application entry point and factory
- config.py: Application configuration (Pydantic settings)
- dependencies.py: FastAPI dependency injection
- middleware/: Custom middleware (logging, auth, etc.)
- api/: API routes organized by domain
  - v1/: Versioned API routes
- schemas/: Pydantic request/response models
- services/: Business logic and service layer

Usage:
    # Run the server
    uvicorn skill_fleet.api.factory:app --reload

    # Or via CLI
    skill-fleet serve
"""

from .factory import app, create_app, get_app

__all__ = ["create_app", "get_app", "app"]
