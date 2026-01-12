"""Tests for CLI constants."""

from skill_fleet.cli.utils.constants import (
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


def test_default_api_url():
    """Test default API URL is localhost."""
    assert DEFAULT_API_URL == "http://localhost:8000"


def test_default_api_timeout():
    """Test default API timeout is reasonable."""
    assert DEFAULT_API_TIMEOUT == 30.0


def test_poll_interval():
    """Test HITL poll interval is 2 seconds."""
    assert HITL_POLL_INTERVAL == 2.0


def test_exit_codes():
    """Test exit codes match standard values."""
    assert EXIT_SUCCESS == 0
    assert EXIT_ERROR == 1


def test_api_timeout_bounds():
    """Test API timeout bounds."""
    assert MIN_API_TIMEOUT == 0.1
    assert MAX_API_TIMEOUT == 300.0


def test_max_poll_attempts():
    """Test max poll attempts."""
    assert MAX_POLL_ATTEMPTS == 100


def test_display_constants():
    """Test display configuration constants."""
    assert CONSOLE_REFRESH_RATE == 10
    assert JSON_INDENT == 2
    assert SEPARATOR_WIDTH == 60


def test_color_palette():
    """Test Rich color palette constants."""
    assert COLOR_SUCCESS == "green"
    assert COLOR_WARNING == "yellow"
    assert COLOR_ERROR == "red"
    assert COLOR_INFO == "cyan"
    assert COLOR_MUTED == "dim"


def test_status_icons():
    """Test status icon constants."""
    assert ICON_SUCCESS == "✓"
    assert ICON_WARNING == "⚠️"
    assert ICON_ERROR == "❌"
    assert ICON_INFO == "ℹ️"
    assert ICON_WORKING == "⏳"


def test_all_exit_codes():
    """Test all exit code constants."""
    assert EXIT_SUCCESS == 0
    assert EXIT_ERROR == 1
    assert EXIT_CONFIG_ERROR == 2
    assert EXIT_VALIDATION_ERROR == 3
    assert EXIT_NETWORK_ERROR == 4


def test_user_id_constraints():
    """Test user ID validation constraints."""
    assert MAX_USER_ID_LENGTH == 100
    assert MIN_USER_ID_LENGTH == 1
