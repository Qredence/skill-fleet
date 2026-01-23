"""
Skills Fleet FastAPI Application.

This is the main application package. The FastAPI app serves as the primary
interface for skill creation, taxonomy management, and all DSPy workflows.

Directory Structure:
- main.py: FastAPI application entry point and factory
- config.py: Application configuration (Pydantic settings)
- dependencies.py: FastAPI dependency injection
- middleware/: Custom middleware (logging, auth, etc.)
- api/: API routes organized by domain
  - v2/: Versioned API routes (single-file pattern)
  - schemas/: Pydantic request/response models

Usage:
    # Run the server
    uvicorn skill_fleet.app.main:app --reload

    # Or via CLI
    skill-fleet serve
"""

from skill_fleet.app.main import app, create_app

__all__ = ["create_app", "app"]
