"""Unit tests for CORS configuration in the FastAPI app."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# Set development environment for initial import to avoid RuntimeError during collection
with patch.dict(os.environ, {"SKILL_FLEET_ENV": "development"}):
    from skill_fleet.api.app import create_app

from fastapi.testclient import TestClient


def test_cors_default_production_insecure_fails():
    """Test that the app fails to start in production if CORS is not configured."""
    with patch(
        "skill_fleet.api.app.settings",
        MagicMock(
            is_development=False,
            cors_origins_list=[],
        ),
    ):
        # SKILL_FLEET_CORS_ORIGINS is not set, and SKILL_FLEET_ENV is production.
        # It should raise a ValueError.
        with pytest.raises(ValueError) as excinfo:
            create_app()
        assert "SKILL_FLEET_CORS_ORIGINS must be set in production environment" in str(
            excinfo.value
        )


def test_cors_production_with_wildcard_fails():
    """Test that the app fails to start in production if CORS is set to wildcard."""
    with patch(
        "skill_fleet.api.app.settings",
        MagicMock(
            is_development=False,
            cors_origins_list=["*"],
        ),
    ):
        with pytest.raises(ValueError) as excinfo:
            create_app()
        assert "Wildcard CORS origin ('*') is not allowed in production" in str(excinfo.value)


def test_cors_production_with_explicit_origins_works():
    """Test that the app starts in production with explicit CORS origins."""
    origins = ["https://example.com", "https://app.example.com"]
    with patch(
        "skill_fleet.api.app.settings",
        MagicMock(
            is_development=False,
            cors_origins_list=origins,
        ),
    ):
        app = create_app()
        client = TestClient(app)
        # Verify CORS headers
        response = client.options(
            "/health",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://example.com"


def test_cors_development_with_wildcard_works():
    """Test that the app starts in development with wildcard CORS."""
    with patch(
        "skill_fleet.api.app.settings",
        MagicMock(
            is_development=True,
            cors_origins_list=["*"],
        ),
    ):
        app = create_app()
        client = TestClient(app)
        response = client.options(
            "/health",
            headers={
                "Origin": "https://anydomain.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "*"


def test_cors_development_default_is_wildcard():
    """Test that in development, CORS defaults to wildcard if not set."""
    with patch(
        "skill_fleet.api.app.settings",
        MagicMock(
            is_development=True,
            cors_origins_list=[],
        ),
    ):
        # The app logic will set cors_origins_list to ["*"] if is_development is True and it's empty.
        app = create_app()
        client = TestClient(app)
        response = client.options(
            "/health",
            headers={
                "Origin": "https://anydomain.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "*"
