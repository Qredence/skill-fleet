"""Middleware for request logging and request ID tracking."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with request ID and timing information."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and add logging.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with X-Request-ID header
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log request start
        start_time = time.monotonic()
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as exc:
            # Log unhandled exceptions
            logger.exception(
                f"[{request_id}] Unhandled exception",
                extra={
                    "request_id": request_id,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
            )
            raise

        # Calculate processing time
        process_time = (time.monotonic() - start_time) * 1000

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        # Log response
        logger.info(
            f"[{request_id}] {response.status_code} ({process_time:.2f}ms)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time_ms": process_time,
            },
        )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and format unexpected errors."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """Process request and handle unexpected errors.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response or JSON error response on exception
        """
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"[{request_id}] Unexpected error: {exc}",
                extra={
                    "request_id": request_id,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                },
                exc_info=True,
            )

            # Return generic error in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                },
            )


__all__: list[str] = [
    "LoggingMiddleware",
    "ErrorHandlingMiddleware",
]
