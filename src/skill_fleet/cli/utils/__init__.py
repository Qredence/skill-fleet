"""CLI utilities submodule."""

from .constants import (
    COLOR_ERROR,
    COLOR_INFO,
    COLOR_MUTED,
    COLOR_SUCCESS,
    COLOR_WARNING,
    CONSOLE_REFRESH_RATE,
    DEFAULT_API_TIMEOUT,
    DEFAULT_API_URL,
    EXIT_CONFIG_ERROR,
    EXIT_ERROR,
    EXIT_NETWORK_ERROR,
    EXIT_SUCCESS,
    EXIT_VALIDATION_ERROR,
    HITL_POLL_INTERVAL,
    ICON_ERROR,
    ICON_INFO,
    ICON_SUCCESS,
    ICON_WARNING,
    ICON_WORKING,
    JSON_INDENT,
    MAX_API_TIMEOUT,
    MAX_POLL_ATTEMPTS,
    MAX_USER_ID_LENGTH,
    MIN_API_TIMEOUT,
    MIN_USER_ID_LENGTH,
    SEPARATOR_WIDTH,
)
from .security import (
    sanitize_user_id,
    validate_api_url,
    validate_path_within_root,
    validate_timeout,
)

__all__ = [
    # Constants - API
    "DEFAULT_API_URL",
    "DEFAULT_API_TIMEOUT",
    "MIN_API_TIMEOUT",
    "MAX_API_TIMEOUT",
    # Constants - Polling
    "HITL_POLL_INTERVAL",
    "MAX_POLL_ATTEMPTS",
    # Constants - Display
    "CONSOLE_REFRESH_RATE",
    "JSON_INDENT",
    "SEPARATOR_WIDTH",
    # Constants - Colors
    "COLOR_SUCCESS",
    "COLOR_WARNING",
    "COLOR_ERROR",
    "COLOR_INFO",
    "COLOR_MUTED",
    # Constants - Icons
    "ICON_SUCCESS",
    "ICON_WARNING",
    "ICON_ERROR",
    "ICON_INFO",
    "ICON_WORKING",
    # Constants - Exit codes
    "EXIT_SUCCESS",
    "EXIT_ERROR",
    "EXIT_CONFIG_ERROR",
    "EXIT_VALIDATION_ERROR",
    "EXIT_NETWORK_ERROR",
    # Constants - Validation
    "MAX_USER_ID_LENGTH",
    "MIN_USER_ID_LENGTH",
    # Security
    "validate_path_within_root",
    "sanitize_user_id",
    "validate_api_url",
    "validate_timeout",
]
