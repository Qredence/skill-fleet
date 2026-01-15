"""FastAPI server for Skill Fleet with auto-discovery and HITL support."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..core.dspy import modules, programs
from ..llm.dspy_config import configure_dspy
from .discovery import discover_and_expose
from .routes import drafts, evaluation, hitl, jobs, optimization, skills, taxonomy, validation

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    # Configure DSPy globally for the API
    try:
        configure_dspy()
        logger.info("DSPy configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure DSPy: {e}")

    app = FastAPI(
        title="Skill Fleet API",
        description="Reworked AI-powered skill creation API with HITL support",
        version="2.0.0",
    )

    # Middleware
    env = os.environ.get("SKILL_FLEET_ENV", "production").lower()
    cors_origins_raw = os.environ.get("SKILL_FLEET_CORS_ORIGINS", "")
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

    # Security enforcement for CORS
    if not cors_origins:
        if env == "development":
            logger.warning("CORS_ORIGINS not set; defaulting to wildcard '*' in development mode")
            cors_origins = ["*"]
        else:
            raise RuntimeError(
                "SKILL_FLEET_CORS_ORIGINS must be set in production environment. "
                "Set it to a comma-separated list of allowed origins, or set "
                "SKILL_FLEET_ENV=development for testing with wildcards."
            )

    if "*" in cors_origins:
        if env != "development":
            raise RuntimeError(
                "Wildcard CORS origin ('*') is not allowed in production. "
                "Set the SKILL_FLEET_CORS_ORIGINS environment variable to a "
                "comma-separated list of allowed origins."
            )
        if len(cors_origins) > 1:
            # If multiple origins including wildcard, prefer explicit ones
            cors_origins = [origin for origin in cors_origins if origin != "*"]

    if cors_origins == ["*"]:
        logger.warning(
            "CORS is configured with wildcard origins ('*'). "
            "Note: when using '*', CORS credentials (cookies, auth headers) "
            "are disabled (allow_credentials=False)."
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials="*" not in cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include static routers
    app.include_router(skills.router, prefix="/api/v2/skills", tags=["skills"])
    app.include_router(hitl.router, prefix="/api/v2/hitl", tags=["hitl"])
    app.include_router(jobs.router, prefix="/api/v2/jobs", tags=["jobs"])
    app.include_router(drafts.router, prefix="/api/v2/drafts", tags=["drafts"])
    app.include_router(taxonomy.router, prefix="/api/v2/taxonomy", tags=["taxonomy"])
    app.include_router(validation.router, prefix="/api/v2/validation", tags=["validation"])
    app.include_router(evaluation.router, prefix="/api/v2/evaluation", tags=["evaluation"])
    app.include_router(optimization.router, prefix="/api/v2/optimization", tags=["optimization"])

    # Auto-discovery of DSPy modules
    discover_and_expose(app, programs, prefix="/api/v2/programs")
    discover_and_expose(app, modules, prefix="/api/v2/modules")

    @app.get("/health")
    async def health():
        """Health check endpoint to verify API availability.

        Returns:
            dict: Status and version information
        """
        return {"status": "ok", "version": "2.0.0"}

    return app


app = create_app()
