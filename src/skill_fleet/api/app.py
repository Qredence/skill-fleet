"""FastAPI server for Skill Fleet with auto-discovery and HITL support."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..core.dspy import modules, programs
from ..llm.dspy_config import configure_dspy
from .config import get_settings
from .discovery import discover_and_expose
from .exceptions import (
    SkillFleetAPIException,
)
from .lifespan import lifespan
from .middleware.logging import ErrorHandlingMiddleware, LoggingMiddleware
from .routes import (
    chat_streaming,
    drafts,
    evaluation,
    hitl,
    jobs,
    optimization,
    skills,
    taxonomy,
    training,
    validation,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _configure_logging() -> None:
    """Configure application logging based on settings."""
    # Patch logging settings to handle MagicMock in tests
    log_level_attr = getattr(settings, "log_level", "INFO")
    if not isinstance(log_level_attr, str):
        log_level_attr = "INFO"

    log_level = getattr(logging, log_level_attr.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    # In production with JSON logging, use structured format
    log_format = getattr(settings, "log_format", "text")
    if isinstance(log_format, str) and log_format == "json":
        # Could integrate structlog here in the future
        pass


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured application instance.

    """
    # Configure logging
    _configure_logging()

    # Configure DSPy globally for the API
    try:
        configure_dspy()
        logger.info("DSPy configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure DSPy: {e}")

    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
    )

    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)  # type: ignore[arg-type]
    app.add_middleware(LoggingMiddleware)  # type: ignore[arg-type]

    # CORS configuration
    cors_origins = settings.cors_origins_list

    # Security enforcement for CORS
    if not cors_origins:
        if settings.is_development:
            logger.warning("CORS_ORIGINS not set; defaulting to wildcard '*' in development mode")
            cors_origins = ["*"]
        else:
            raise ValueError(
                "SKILL_FLEET_CORS_ORIGINS must be set in production environment. "
                "Set it to a comma-separated list of allowed origins, or set "
                "SKILL_FLEET_ENV=development for testing with wildcards."
            )

    if "*" in cors_origins:
        if not settings.is_development:
            raise ValueError(
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
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=cors_origins,
        allow_credentials="*" not in cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    _register_exception_handlers(app)

    # Include static routers
    app.include_router(skills.router, prefix="/api/v2/skills", tags=["skills"])
    app.include_router(hitl.router, prefix="/api/v2/hitl", tags=["hitl"])
    app.include_router(jobs.router, prefix="/api/v2/jobs", tags=["jobs"])
    app.include_router(drafts.router, prefix="/api/v2/drafts", tags=["drafts"])
    app.include_router(taxonomy.router, prefix="/api/v2/taxonomy", tags=["taxonomy"])
    app.include_router(validation.router, prefix="/api/v2/validation", tags=["validation"])
    app.include_router(evaluation.router, prefix="/api/v2/evaluation", tags=["evaluation"])
    app.include_router(optimization.router, prefix="/api/v2/optimization", tags=["optimization"])
    app.include_router(training.router, prefix="/api/v2/training", tags=["training"])
    app.include_router(chat_streaming.router, tags=["chat"])

    # Auto-discovery of DSPy modules
    discover_and_expose(app, programs, prefix="/api/v2/programs")
    discover_and_expose(app, modules, prefix="/api/v2/modules")

    @app.get("/health")
    async def health():
        """
        Health check endpoint to verify API availability.

        Returns:
            dict: Status and version information

        """
        return {"status": "ok", "version": settings.api_version}

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers for consistent error responses.

    Args:
        app: FastAPI application instance

    """

    @app.exception_handler(SkillFleetAPIException)
    async def skill_fleet_exception_handler(
        request: Request, exc: SkillFleetAPIException
    ) -> JSONResponse:
        """Handle custom Skill Fleet exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"[{request_id}] {exc.__class__.__name__}: {exc.detail}",
            extra={
                "request_id": request_id,
                "exception_type": exc.__class__.__name__,
                "status_code": exc.status_code,
            },
        )

        content = {"error": exc.detail, "request_id": request_id}
        if hasattr(exc, "extra") and exc.extra:
            content.update(exc.extra)  # type: ignore[no-untyped-call]

        return JSONResponse(
            status_code=exc.status_code,
            content=content,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle standard HTTP exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"[{request_id}] HTTPException: {exc.detail}",
            extra={
                "request_id": request_id,
                "status_code": exc.status_code,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.detail, "request_id": request_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(
            f"[{request_id}] Validation error: {exc.errors()}",
            extra={
                "request_id": request_id,
                "validation_errors": exc.errors(),
            },
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": exc.errors(),
                "request_id": request_id,
            },
        )


# Lazy app initialization to allow environment variables to be set before import
# This is important for testing where conftest.py sets SKILL_FLEET_ENV and SKILL_FLEET_CORS_ORIGINS
_app: FastAPI | None = None


def get_app() -> FastAPI:
    """
    Get or create the FastAPI application instance.

    Returns:
        Cached FastAPI instance

    """
    global _app
    if _app is None:
        _app = create_app()
    return _app


# Module-level app for backward compatibility with uvicorn
# Tests should use get_app() from skill_fleet.api.app
app = get_app()

# For backward compatibility with uvicorn run: python -m skill_fleet.api
# This will create the app when run as a module
if __name__ == "__main__":
    app = get_app()
