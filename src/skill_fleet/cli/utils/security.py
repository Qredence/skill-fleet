"""Security utilities for input validation and sanitization."""

import re
import warnings
from pathlib import Path
from urllib.parse import urlparse


def validate_path_within_root(user_path: Path, root_path: Path, path_type: str = "Path") -> Path:
    """
    Validate that a path is within a root directory to prevent path traversal attacks.

    Args:
        user_path: The user-provided path to validate
        root_path: The root directory that the path must be within
        path_type: Description of the path type for error messages

    Returns:
        The resolved absolute path

    Raises:
        ValueError: If the path would escape the root directory
    """
    # Resolve both paths to absolute paths
    resolved_user = user_path.resolve()
    resolved_root = root_path.resolve()

    # Check if user_path is within root_path
    try:
        resolved_user.relative_to(resolved_root)
    except ValueError as e:
        raise ValueError(f"{path_type} must be within {resolved_root}. Got: {resolved_user}") from e

    return resolved_user


def sanitize_user_id(user_id: str) -> str:
    """
    Sanitize user ID to prevent injection attacks.

    Only allows alphanumeric characters, hyphens, underscores, @, and periods.

    Args:
        user_id: The user ID to sanitize

    Returns:
        The sanitized user ID

    Raises:
        ValueError: If the user ID contains invalid characters or has invalid length
    """
    if not user_id:
        raise ValueError("User ID cannot be empty")

    # Remove dangerous characters
    sanitized = re.sub(r"[^\w\-@.]", "", user_id)

    # Check if characters were removed
    if sanitized != user_id:
        raise ValueError(
            f"User ID contains invalid characters. "
            f"Only alphanumeric, hyphen, underscore, @, and period are allowed. Got: {user_id}"
        )

    # Validate length
    if len(sanitized) < 1 or len(sanitized) > 100:
        raise ValueError(f"User ID must be between 1 and 100 characters. Got: {len(sanitized)}")

    return sanitized


def validate_api_url(url: str) -> str:
    """
    Validate API URL to ensure it uses secure protocols.

    Args:
        url: The URL to validate

    Returns:
        The validated URL

    Raises:
        ValueError: If the URL uses an invalid protocol
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"API URL must use http:// or https:// protocol. Got: {parsed.scheme}")

    # Warn if using HTTP with non-localhost
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
        warnings.warn(
            f"Using HTTP (non-secure) protocol with non-localhost host: {parsed.hostname}. "
            "Consider using HTTPS for secure communication.",
            UserWarning,
            stacklevel=2,
        )

    return url


def validate_timeout(seconds: float) -> float:
    """
    Validate timeout value is within acceptable bounds.

    Args:
        seconds: The timeout value in seconds

    Returns:
        The validated timeout value

    Raises:
        ValueError: If the timeout is out of bounds
    """
    if seconds < 0:
        raise ValueError(f"Timeout must be non-negative. Got: {seconds}")

    if seconds > 300:
        raise ValueError(f"Timeout must be 300 seconds (5 minutes) or less. Got: {seconds}")

    return seconds
