"""API-specific test fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# API Client Fixtures
# =============================================================================


@pytest.fixture
def api_client(app):
    """Create API test client with default headers."""
    client = TestClient(app)
    client.headers["Content-Type"] = "application/json"
    return client


@pytest.fixture
def authenticated_client(api_client):
    """Create authenticated API client."""
    # Add auth header if needed
    api_client.headers["Authorization"] = "Bearer test-token"
    return api_client


# =============================================================================
# Service Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_cached_taxonomy_service():
    """Mock cached taxonomy service."""
    with patch("skill_fleet.api.v1.taxonomy.get_cached_taxonomy_service") as mock:
        service = MagicMock()
        service.get_global_taxonomy = MagicMock(
            return_value={
                "version": "1.0.0",
                "categories": [
                    {"id": "testing", "name": "Testing", "path": "testing", "skills": []}
                ],
            }
        )
        service.get_user_taxonomy = MagicMock(
            return_value={"user_id": "test-user", "categories": [], "adapted": True}
        )
        mock.return_value = service
        yield service


@pytest.fixture
def mock_job_manager():
    """Mock job manager."""
    with patch("skill_fleet.api.v1.jobs.get_job_manager") as mock:
        manager = MagicMock()
        manager.get_job = MagicMock(
            return_value={
                "job_id": "test-job-123",
                "status": "completed",
                "result": {"skill_id": "test-skill-456"},
            }
        )
        manager.list_jobs = MagicMock(
            return_value=[{"job_id": "test-job-123", "status": "completed"}]
        )
        mock.return_value = manager
        yield manager


# =============================================================================
# Router-Specific Fixtures
# =============================================================================


@pytest.fixture
def skills_api_client(api_client, mock_skill_service):
    """API client with skills service mocked."""
    return api_client


@pytest.fixture
def taxonomy_api_client(api_client, mock_cached_taxonomy_service):
    """API client with taxonomy service mocked."""
    return api_client
