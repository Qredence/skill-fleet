"""
Custom exceptions for Skill Fleet API.

This module defines custom exception classes that can be caught by
global exception handlers to provide consistent error responses.
"""

from __future__ import annotations

from typing import Any


class SkillFleetAPIError(Exception):
    """Base exception for all Skill Fleet API errors."""

    status_code: int = 500
    detail: str = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(
        self,
        detail: str,
        status_code: int = 500,
        headers: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize exception.

        Args:
            detail: Human-readable error message
            status_code: HTTP status code
            headers: Optional response headers

        """
        self.detail = detail
        self.status_code = status_code
        self.headers = headers
        super().__init__(detail)


class NotFoundException(SkillFleetAPIError):
    """Resource not found exception."""

    status_code: int = 404

    def __init__(self, resource: str, identifier: str | None = None) -> None:
        """
        Initialize not found exception.

        Args:
            resource: Type of resource (e.g., "Skill", "Job")
            identifier: Optional identifier of the missing resource

        """
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} '{identifier}' not found"
        super().__init__(detail=message, status_code=404)


class BadRequestException(SkillFleetAPIError):
    """Bad request exception for invalid input."""

    status_code: int = 400

    def __init__(self, detail: str) -> None:
        """
        Initialize bad request exception.

        Args:
            detail: Error message explaining what's invalid

        """
        super().__init__(detail=detail, status_code=400)


class UnauthorizedException(SkillFleetAPIError):
    """Unauthorized exception for missing or invalid authentication."""

    status_code: int = 401

    def __init__(self, detail: str = "Authentication required") -> None:
        """
        Initialize unauthorized exception.

        Args:
            detail: Error message

        """
        super().__init__(detail=detail, status_code=401)


class ForbiddenException(SkillFleetAPIError):
    """Forbidden exception for valid authentication but insufficient permissions."""

    status_code: int = 403

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        """
        Initialize forbidden exception.

        Args:
            detail: Error message

        """
        super().__init__(detail=detail, status_code=403)


class ConflictException(SkillFleetAPIError):
    """Conflict exception for resource conflicts."""

    status_code: int = 409

    def __init__(self, detail: str) -> None:
        """
        Initialize conflict exception.

        Args:
            detail: Error message explaining the conflict

        """
        super().__init__(detail=detail, status_code=409)


class UnprocessableEntityException(SkillFleetAPIError):
    """Unprocessable entity exception for valid syntax but semantic errors."""

    status_code: int = 422

    def __init__(self, detail: str) -> None:
        """
        Initialize unprocessable entity exception.

        Args:
            detail: Error message explaining the validation error

        """
        super().__init__(detail=detail, status_code=422)


class TooManyRequestsException(SkillFleetAPIError):
    """Too many requests exception for rate limiting."""

    status_code: int = 429

    def __init__(self, detail: str = "Too many requests", retry_after: int | None = None) -> None:
        """
        Initialize rate limit exception.

        Args:
            detail: Error message
            retry_after: Optional seconds until retry is allowed

        """
        headers = None
        if retry_after is not None:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(detail=detail, status_code=429, headers=headers)


class InternalServerErrorException(SkillFleetAPIError):
    """Internal server error for unexpected errors."""

    status_code: int = 500

    def __init__(self, detail: str = "Internal server error") -> None:
        """
        Initialize internal server error exception.

        Args:
            detail: Error message (will be generic in production)

        """
        super().__init__(detail=detail, status_code=500)


class ServiceUnavailableException(SkillFleetAPIError):
    """Service unavailable for temporary maintenance or dependency failures."""

    status_code: int = 503

    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        """
        Initialize service unavailable exception.

        Args:
            detail: Error message
            retry_after: Optional seconds until retry is allowed

        """
        headers = None
        if retry_after is not None:
            headers = {"Retry-After": str(retry_after)}
        super().__init__(detail=detail, status_code=503, headers=headers)


class JobException(SkillFleetAPIError):
    """Exception for job-related errors."""

    status_code: int = 400

    def __init__(
        self,
        job_id: str,
        detail: str,
        status_code: int = 400,
    ) -> None:
        """
        Initialize job exception.

        Args:
            job_id: Job identifier
            detail: Error message
            status_code: HTTP status code

        """
        message = f"Job {job_id}: {detail}"
        super().__init__(detail=message, status_code=status_code)


class HITLException(SkillFleetAPIError):
    """Exception for Human-in-the-Loop interaction errors."""

    status_code: int = 400

    def __init__(
        self,
        detail: str,
        interaction_type: str | None = None,
    ) -> None:
        """
        Initialize HITL exception.

        Args:
            detail: Error message
            interaction_type: Optional type of HITL interaction

        """
        message = detail
        if interaction_type:
            message = f"HITL ({interaction_type}): {detail}"
        super().__init__(detail=message, status_code=400)


class ValidationException(SkillFleetAPIError):
    """Exception for skill validation failures."""

    status_code: int = 400

    def __init__(
        self,
        detail: str,
        validation_score: float | None = None,
    ) -> None:
        """
        Initialize validation exception.

        Args:
            detail: Error message explaining validation failure
            validation_score: Optional validation score

        """
        extra: dict[str, Any] = {}
        if validation_score is not None:
            extra["validation_score"] = validation_score

        super().__init__(
            detail=detail,
            status_code=400,
        )
        self.extra = extra


__all__ = [
    "SkillFleetAPIError",
    "NotFoundException",
    "BadRequestException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "UnprocessableEntityException",
    "TooManyRequestsException",
    "InternalServerErrorException",
    "ServiceUnavailableException",
    "JobException",
    "HITLException",
    "ValidationException",
]
