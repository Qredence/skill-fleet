"""Global pytest configuration and fixtures."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Set development environment for all tests to allow wildcard CORS,
# SQLite database fallback, and other development-friendly defaults.
# This must happen before any imports that use settings
os.environ["SKILL_FLEET_ENV"] = "development"
os.environ["SKILL_FLEET_CORS_ORIGINS"] = "*"
# Allow deterministic fallbacks when LMs are not configured (tests run offline).
os.environ.setdefault("SKILL_FLEET_ALLOW_LLM_FALLBACK", "1")

# Use in-memory SQLite for tests unless DATABASE_URL is explicitly set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./test_skill_fleet.db"

if TYPE_CHECKING:
    pass


# =============================================================================
# FastAPI App Fixtures
# =============================================================================


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    from skill_fleet.api.factory import create_app

    return create_app()


@pytest.fixture
def client(app):
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def dependency_override_cleanup(app):
    """Cleanup dependency overrides after test."""
    yield
    app.dependency_overrides.clear()


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_skill_service():
    """Mock SkillService for testing."""
    with patch("skill_fleet.api.v1.skills.SkillService") as mock:
        service = MagicMock()
        service.create_skill = AsyncMock(
            return_value={
                "job_id": "test-job-123",
                "status": "pending",
                "message": "Skill creation started",
            }
        )
        service.get_skill = MagicMock(
            return_value={"skill_id": "test-skill-456", "name": "Test Skill", "status": "active"}
        )
        service.validate_skill = AsyncMock(
            return_value={"valid": True, "score": 0.95, "issues": []}
        )
        mock.return_value = service
        yield service


@pytest.fixture
def mock_taxonomy_manager():
    """Mock TaxonomyManager for testing."""
    with patch("skill_fleet.api.dependencies.get_taxonomy_manager") as mock:
        manager = MagicMock()
        manager.get_global_taxonomy = MagicMock(return_value={"categories": [], "total_skills": 0})
        manager.get_user_taxonomy = MagicMock(return_value={"categories": [], "adapted": True})
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    return session


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def valid_skill_request():
    """Valid skill creation request data."""
    return {"task_description": "Create a skill for testing purposes", "user_id": "test-user-123"}


@pytest.fixture
def invalid_skill_request():
    """Invalid skill creation request data (missing required fields)."""
    return {"task_description": ""}


@pytest.fixture
def sample_skill():
    """Sample skill data."""
    return {
        "skill_id": "test-skill-456",
        "name": "Test Skill",
        "description": "A test skill for testing purposes",
        "taxonomy_path": "testing/test-skill",
        "status": "active",
        "content": "# Test Skill\n\nThis is a test skill.",
    }


@pytest.fixture
def sample_job():
    """Sample job data."""
    return {
        "job_id": "test-job-123",
        "status": "completed",
        "task_description": "Create a test skill",
        "user_id": "test-user-123",
        "result": {"skill_id": "test-skill-456", "status": "success"},
    }


# =============================================================================
# File System Fixtures
# =============================================================================


@pytest.fixture
def temp_skills_root(tmp_path):
    """Create temporary skills root directory."""
    skills_root = tmp_path / "skills"
    skills_root.mkdir()

    # Create basic structure
    (skills_root / "_core").mkdir()
    (skills_root / "testing").mkdir()

    return skills_root


@pytest.fixture
def mock_skills_root(temp_skills_root):
    """Mock skills root path."""
    with patch("skill_fleet.api.dependencies.get_skills_root") as mock:
        mock.return_value = temp_skills_root
        yield temp_skills_root


# =============================================================================
# DSPy Configuration
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def configure_dspy_for_tests():
    """Configure DSPy with a dummy LM for unit tests."""
    import dspy

    # Create a dummy LM that returns predictable, parseable text outputs.
    class DummyLM(dspy.LM):
        def __init__(self):
            super().__init__(model="dummy/test")

        def __call__(self, prompt=None, messages=None, **kwargs):
            # DSPy v3 adapters expect a list of strings (or dicts with "text").
            response_text = (
                "domain: technical\n"
                "category: web\n"
                "target_level: intermediate\n"
                'topics: ["test"]\n'
                "constraints: []\n"
                "ambiguities: []\n"
            )
            return [response_text]

    # Configure DSPy with dummy LM
    dspy.configure(lm=DummyLM())
    yield
    # Cleanup - reset to default
    dspy.settings.configure(lm=None)
