"""Unit tests for FastAPI skill creation API.

Tests FastAPI endpoints in src/skill_fleet/api/
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from skill_fleet.api.app import get_app

# ============================================================================
# Constants
# ============================================================================

TEST_SKILL_PATH = "general/testing"
TEST_SKILL_DESCRIPTION = "Use when testing."
API_VERSION = "2.0.0"

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def client():
    """Create a test client for FastAPI app."""
    return TestClient(get_app())


@pytest.fixture
def dependency_override_cleanup():
    """Fixture to ensure dependency overrides are cleaned up after each test.

    This prevents test isolation issues where overrides from one test
    affect subsequent tests.
    """
    yield
    get_app().dependency_overrides.clear()


# ============================================================================
# Test Health Endpoint
# ============================================================================


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok_status(self, client):
        """Test health endpoint returns ok status with valid version."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        # Verify version is a non-empty string (semantic versioning format)
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0


# ============================================================================
# Test Skills Create Endpoint
# ============================================================================


class TestSkillsCreateEndpoint:
    """Tests for /api/v2/skills/create endpoint."""

    def test_create_skill_returns_job_id(self, client):
        """Test skill creation returns a job ID and accepted status.

        Verifies that when a valid skill creation request is submitted:
        - HTTP 200 status is returned
        - Response includes a 'job_id' field
        - Response includes 'status' field with value 'accepted'
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
            response = client.post(
                "/api/v2/skills/create",
                json={"task_description": "Create an OpenAPI skill for REST endpoints"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert isinstance(data["job_id"], str)
            assert len(data["job_id"]) > 0
            assert data["status"] == "accepted"

    def test_create_skill_missing_description(self, client):
        """Test skill creation fails without task_description field.

        Verifies that Pydantic validation catches missing required fields
        and returns HTTP 422 (Unprocessable Entity).
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
            response = client.post("/api/v2/skills/create", json={})

            assert response.status_code == 422  # Validation error
            data = response.json()
            assert "details" in data
            assert data["error"] == "Validation error"
            assert "Field required" in str(data["details"])

    def test_create_skill_empty_description(self, client):
        """Test skill creation fails with empty or too short task_description.

        Verifies that inputs failing min_length validation are correctly handled
        by Pydantic, returning HTTP 422.
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
            response = client.post(
                "/api/v2/skills/create",
                # Now fails min_length=10
                json={"task_description": "short"},
            )

            assert response.status_code == 422
            data = response.json()
            assert "details" in data
            assert data["error"] == "Validation error"
            assert "at least 10 characters" in str(data["details"])
