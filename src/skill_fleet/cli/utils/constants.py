"""Constants for CLI configuration and theming.

Centralizes all magic numbers and configuration values
to improve maintainability and consistency.
"""

from __future__ import annotations

# API configuration
DEFAULT_API_URL = "http://localhost:8000"
DEFAULT_API_TIMEOUT = 30.0
MIN_API_TIMEOUT = 0.1
MAX_API_TIMEOUT = 300.0

# Polling configuration
HITL_POLL_INTERVAL = 2.0  # seconds between HITL polls
MAX_POLL_ATTEMPTS = 100  # maximum polling iterations

# Display configuration
CONSOLE_REFRESH_RATE = 10  # times per second for Live displays
JSON_INDENT = 2  # spaces for JSON output
SEPARATOR_WIDTH = 60  # characters for separator lines

# Rich color palette (consistent theming)
COLOR_SUCCESS = "green"
COLOR_WARNING = "yellow"
COLOR_ERROR = "red"
COLOR_INFO = "cyan"
COLOR_MUTED = "dim"

# Icons for status messages
ICON_SUCCESS = "✓"
ICON_WARNING = "⚠️"
ICON_ERROR = "❌"
ICON_INFO = "ℹ️"
ICON_WORKING = "⏳"

# Exit codes (same as in exceptions.py)
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4

# Validation constraints
MAX_USER_ID_LENGTH = 100
MIN_USER_ID_LENGTH = 1
