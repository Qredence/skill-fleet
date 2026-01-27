"""FastAPI server for Skill Fleet with auto-discovery and HITL support."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..llm.dspy_config import configure_dspy
from .config import get_settings
from .exceptions import SkillFleetAPIException
from .lifespan import lifespan
from .middleware.logging import ErrorHandlingMiddleware, LoggingMiddleware

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


def _configure_middleware(app: FastAPI) -> None:
    """
    Register middleware in correct order.

    Order matters:
    1. ErrorHandlingMiddleware first (catches everything)
    2. LoggingMiddleware second (has request ID)
    """
    app.add_middleware(ErrorHandlingMiddleware)  # type: ignore[arg-type]
    app.add_middleware(LoggingMiddleware)  # type: ignore[arg-type]


def _configure_cors(app: FastAPI) -> None:
    """
    Configure CORS with security validation.

    Enforces:
    - Explicit origins required in production
    - Wildcard (*) only allowed in development
    - Credentials disabled when using wildcard

    Args:
        app: FastAPI application instance

    Raises:
        ValueError: If CORS configuration is invalid for production

    """
    cors_origins = settings.cors_origins_list

    # Default to wildcard in development only
    if not cors_origins:
        if settings.is_development:
            logger.warning("CORS_ORIGINS not set; defaulting to '*' in development")
            cors_origins = ["*"]
        else:
            raise ValueError(
                "SKILL_FLEET_CORS_ORIGINS must be set in production environment. "
                "Set it to a comma-separated list of allowed origins, or set "
                "SKILL_FLEET_ENV=development for testing with wildcards."
            )

    # Security check: wildcard not allowed in production
    if "*" in cors_origins and not settings.is_development:
        raise ValueError(
            "Wildcard CORS origin ('*') is not allowed in production. "
            "Set SKILL_FLEET_CORS_ORIGINS to a comma-separated list of allowed origins."
        )

    # Prefer explicit origins over wildcard
    if "*" in cors_origins and len(cors_origins) > 1:
        cors_origins = [o for o in cors_origins if o != "*"]

    if "*" in cors_origins:
        logger.warning(
            "CORS wildcard disables credentials (cookies, auth headers). "
            "Use explicit origins in production for authenticated requests."
        )

    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=cors_origins,
        allow_credentials="*" not in cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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

    # Configure middleware (order matters)
    _configure_middleware(app)

    # Configure CORS (security validation)
    _configure_cors(app)

    # Register exception handlers
    _register_exception_handlers(app)

    # Include v1 API router (the only API version)
    from .api.v1.router import router as v1_router

    app.include_router(v1_router, prefix="/api/v1", tags=["v1-api"])

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
# Usage: uvicorn skill_fleet.app.factory:app
app = get_app()
