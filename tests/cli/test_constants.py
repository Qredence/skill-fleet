"""Tests for CLI constants."""

from skill_fleet.cli.utils.constants import (
    DEFAULT_API_URL,
    DEFAULT_API_TIMEOUT,
    HITL_POLL_INTERVAL,
    MAX_POLL_ATTEMPTS,
    EXIT_SUCCESS,
    EXIT_ERROR,
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
