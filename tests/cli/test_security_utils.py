"""Tests for CLI security utilities.

This module tests input validation and sanitization functions used throughout
the CLI to prevent security vulnerabilities including:
- Path traversal attacks
- Injection attacks
- Invalid protocol usage
- Invalid timeout values
"""

from pathlib import Path

import pytest

from skill_fleet.cli.utils.security import (
    sanitize_user_id,
    validate_api_url,
    validate_path_within_root,
    validate_timeout,
)


def test_validate_path_within_root_accepts_valid_path():
    """Test path validation accepts paths within root."""
    root = Path("/tmp/skills")
    user_path = Path("/tmp/skills/general/testing")

    result = validate_path_within_root(user_path, root, "Skills root")
    assert result == user_path.resolve()


def test_validate_path_within_root_rejects_traversal():
    """Test path validation rejects ../ traversal."""
    root = Path("/tmp/skills")
    user_path = Path("/tmp/skills/../etc/passwd")

    with pytest.raises(ValueError, match="must be within"):
        validate_path_within_root(user_path, root, "Skills root")


def test_sanitize_user_id_accepts_valid_id():
    """Test user ID sanitization accepts valid IDs."""
    assert sanitize_user_id("user-123") == "user-123"
    assert sanitize_user_id("user@example.com") == "user@example.com"


def test_sanitize_user_id_rejects_special_chars():
    """Test user ID sanitization rejects dangerous characters."""
    with pytest.raises(ValueError, match="invalid characters"):
        sanitize_user_id("../../../etc/passwd")


def test_validate_api_url_accepts_valid_protocols():
    """Test API URL validation accepts http/https."""
    assert validate_api_url("http://localhost:8000") == "http://localhost:8000"
    assert validate_api_url("https://api.example.com") == "https://api.example.com"


def test_validate_api_url_rejects_invalid_protocol():
    """Test API URL validation rejects invalid protocols."""
    with pytest.raises(ValueError, match="must use http:// or https://"):
        validate_api_url("ftp://localhost:8000")


def test_validate_api_url_warns_on_http_non_localhost():
    """Test API URL validation warns on HTTP with non-localhost."""
    with pytest.warns(UserWarning, match="Using HTTP.*non-localhost"):
        validate_api_url("http://example.com")


def test_sanitize_user_id_rejects_empty():
    """Test user ID sanitization rejects empty strings."""
    with pytest.raises(ValueError, match="cannot be empty"):
        sanitize_user_id("")


def test_sanitize_user_id_rejects_too_long():
    """Test user ID sanitization rejects IDs over 100 characters."""
    with pytest.raises(ValueError, match="must be between 1 and 100 characters"):
        sanitize_user_id("a" * 101)


def test_sanitize_user_id_rejects_too_short():
    """Test user ID sanitization rejects empty after sanitization."""
    with pytest.raises(ValueError, match="invalid characters"):
        sanitize_user_id("!!!")


def test_validate_timeout_accepts_valid_values():
    """Test timeout validation accepts valid values."""
    assert validate_timeout(0) == 0
    assert validate_timeout(30) == 30
    assert validate_timeout(300) == 300


def test_validate_timeout_rejects_negative():
    """Test timeout validation rejects negative values."""
    with pytest.raises(ValueError, match="must be non-negative"):
        validate_timeout(-1)


def test_validate_timeout_rejects_too_large():
    """Test timeout validation rejects values over 300 seconds."""
    with pytest.raises(ValueError, match="must be 300 seconds"):
        validate_timeout(301)
