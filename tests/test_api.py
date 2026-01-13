"""Unit tests for FastAPI skill creation API.

Tests the FastAPI endpoints in src/skill_fleet/api/
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from skill_fleet.api.app import app

# ============================================================================
# Test Client Setup
# ============================================================================


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ============================================================================
# Test Health Endpoint
# ============================================================================


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok_status(self, client):
        """Test health endpoint returns ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"


# ============================================================================
# Test Skills Create Endpoint
# ============================================================================


class TestSkillsCreateEndpoint:
    """Tests for /api/v2/skills/create endpoint."""

    @patch("skill_fleet.api.routes.skills.run_skill_creation")
    def test_create_skill_returns_job_id(self, mock_run, client):
        """Test skill creation returns a job ID."""
        response = client.post(
            "/api/v2/skills/create",
            json={"task_description": "Create an OpenAPI skill for REST endpoints"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "accepted"

    def test_create_skill_missing_description(self, client):
        """Test skill creation fails without description."""
        response = client.post("/api/v2/skills/create", json={})

        assert response.status_code == 422  # Validation error

    @patch("skill_fleet.api.routes.skills.run_skill_creation")
    def test_create_skill_empty_description(self, mock_run, client):
        """Test skill creation fails with empty description."""
        response = client.post(
            "/api/v2/skills/create",
            json={"task_description": ""},
        )

        assert response.status_code == 400
        assert "task_description is required" in response.json()["detail"]

    @patch("skill_fleet.api.routes.skills.run_skill_creation")
    def test_create_skill_with_user_id(self, mock_run, client):
        """Test skill creation with custom user_id."""
        response = client.post(
            "/api/v2/skills/create",
            json={
                "task_description": "Create a skill for Python async programming",
                "user_id": "test-user-123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data


# ============================================================================
# Test HITL Endpoints
# ============================================================================


class TestHITLEndpoints:
    """Tests for HITL interaction endpoints."""

    def test_get_prompt_job_not_found(self, client):
        """Test getting prompt for non-existent job returns 404."""
        response = client.get("/api/v2/hitl/nonexistent-job-id/prompt")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_post_response_job_not_found(self, client):
        """Test posting response to non-existent job returns 404."""
        response = client.post(
            "/api/v2/hitl/nonexistent-job-id/response",
            json={"action": "proceed"},
        )

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    @patch("skill_fleet.api.routes.skills.run_skill_creation")
    def test_hitl_get_prompt_for_created_job(self, mock_run, client):
        """Test getting HITL prompt for a created job."""
        # Create a job (background task is mocked)
        create_response = client.post(
            "/api/v2/skills/create",
            json={"task_description": "Create a skill for Docker best practices"},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Get the prompt - job exists but may be in initial state
        prompt_response = client.get(f"/api/v2/hitl/{job_id}/prompt")
        assert prompt_response.status_code == 200
        data = prompt_response.json()
        assert "status" in data


# ============================================================================
# Test Taxonomy Endpoints
# ============================================================================


class TestTaxonomyEndpoints:
    """Tests for taxonomy operation endpoints."""

    def test_list_skills(self, client):
        """Test listing skills from taxonomy."""
        with patch("skill_fleet.api.routes.taxonomy.TaxonomyManager") as mock_manager:
            mock_instance = MagicMock()
            mock_instance.list_skills.return_value = []
            mock_manager.return_value = mock_instance

            response = client.get("/api/v2/taxonomy/")

            assert response.status_code == 200
            data = response.json()
            assert "skills" in data
            assert isinstance(data["skills"], list)


# ============================================================================
# Test Validation Endpoints
# ============================================================================


class TestValidationEndpoints:
    """Tests for validation endpoints."""

    def test_validate_skill_missing_path(self, client):
        """Test validation fails without path."""
        response = client.post("/api/v2/validation/validate", json={})

        assert response.status_code == 422  # Validation error

    def test_validate_skill_empty_path(self, client):
        """Test validation fails with empty path."""
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": ""},
        )

        assert response.status_code == 400
        assert "path is required" in response.json()["detail"]

    def test_validate_skill_absolute_path_rejected(self, client):
        """Test validation rejects absolute paths."""
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": "/etc/passwd"},
        )

        assert response.status_code == 400
        assert "Invalid path" in response.json()["detail"]

    def test_validate_skill_path_traversal_rejected(self, client):
        """Test validation rejects path traversal attempts."""
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": "../../../etc/passwd"},
        )

        assert response.status_code == 400
        assert "Invalid path" in response.json()["detail"]

    def test_validate_skill_valid_path(self, client):
        """Test validation with valid skill path."""
        with patch("skill_fleet.api.routes.validation.SkillValidator") as mock_validator:
            mock_instance = MagicMock()
            mock_instance.validate_complete.return_value = {
                "valid": True,
                "issues": [],
            }
            mock_validator.return_value = mock_instance

            response = client.post(
                "/api/v2/validation/validate",
                json={"path": "general/testing"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True


# ============================================================================
# Test Request Models
# ============================================================================


class TestCreateSkillRequest:
    """Tests for CreateSkillRequest pydantic model."""

    def test_valid_request(self):
        """Test valid create skill request."""
        from skill_fleet.api.routes.skills import CreateSkillRequest

        request = CreateSkillRequest(
            task_description="Create a skill for Python async programming",
            user_id="test-user",
        )

        assert request.task_description == "Create a skill for Python async programming"
        assert request.user_id == "test-user"

    def test_default_user_id(self):
        """Test user_id defaults to 'default'."""
        from skill_fleet.api.routes.skills import CreateSkillRequest

        request = CreateSkillRequest(task_description="Test skill creation")

        assert request.user_id == "default"


class TestValidateSkillRequest:
    """Tests for ValidateSkillRequest pydantic model."""

    def test_valid_request(self):
        """Test valid validate skill request."""
        from skill_fleet.api.routes.validation import ValidateSkillRequest

        request = ValidateSkillRequest(path="general/testing")

        assert request.path == "general/testing"
