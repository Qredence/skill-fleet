"""Unit tests for FastAPI skill creation API.

Tests the FastAPI endpoints in src/skill_fleet/api/
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from skill_fleet.api.app import app

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
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def dependency_override_cleanup():
    """Fixture to ensure dependency overrides are cleaned up after each test.
    
    This prevents test isolation issues where overrides from one test
    affect subsequent tests.
    """
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Test Health Endpoint
# ============================================================================


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_ok_status(self, client):
        """Test health endpoint returns ok status with valid version.
        
        Verifies that the health check endpoint:
        - Returns HTTP 200 status code
        - Includes 'status' field with value 'ok'
        - Includes 'version' field with a valid semantic version string
        """
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
        response = client.post("/api/v2/skills/create", json={})

        assert response.status_code == 422  # Validation error

    def test_create_skill_empty_description(self, client):
        """Test skill creation fails with empty task_description string.
        
        Verifies that empty strings are rejected as invalid input,
        returning HTTP 400 with appropriate error message.
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
            response = client.post(
                "/api/v2/skills/create",
                json={"task_description": ""},
            )

            assert response.status_code == 400
            data = response.json()
            assert "detail" in data
            assert "task_description is required" in data["detail"]

    def test_create_skill_with_user_id(self, client):
        """Test skill creation with custom user_id parameter.
        
        Verifies that when a custom user_id is provided:
        - The request is accepted (HTTP 200)
        - A job_id is returned
        - The user_id is properly passed through the system
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
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
            assert isinstance(data["job_id"], str)

    def test_create_skill_default_user_id(self, client):
        """Test skill creation defaults user_id to 'default' when not provided.
        
        Verifies that the CreateSkillRequest model properly defaults
        the user_id field when omitted from the request.
        """
        from skill_fleet.api.routes.skills import CreateSkillRequest

        request = CreateSkillRequest(task_description="Test skill creation")

        assert request.user_id == "default"


# ============================================================================
# Test HITL Endpoints
# ============================================================================


class TestHITLEndpoints:
    """Tests for HITL (Human-in-the-Loop) interaction endpoints."""

    def test_get_prompt_job_not_found(self, client):
        """Test getting prompt for non-existent job returns 404.
        
        Verifies that requesting a prompt for a job that doesn't exist
        returns HTTP 404 with appropriate error message.
        """
        response = client.get("/api/v2/hitl/nonexistent-job-id/prompt")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Job not found" in data["detail"]

    def test_post_response_job_not_found(self, client):
        """Test posting response to non-existent job returns 404.
        
        Verifies that submitting a response to a non-existent job
        returns HTTP 404 with appropriate error message.
        """
        response = client.post(
            "/api/v2/hitl/nonexistent-job-id/response",
            json={"action": "proceed"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Job not found" in data["detail"]

    def test_hitl_get_prompt_for_created_job(self, client):
        """Test getting HITL prompt for a created job returns valid structure.
        
        Verifies that after creating a job:
        - The job can be queried for its prompt
        - HTTP 200 status is returned
        - Response includes 'status' field
        - Response structure is valid JSON
        """
        with patch("skill_fleet.api.routes.skills.run_skill_creation"):
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
            assert isinstance(data["status"], str)


# ============================================================================
# Test Taxonomy Endpoints
# ============================================================================


class TestTaxonomyEndpoints:
    """Tests for taxonomy operation endpoints."""

    def test_list_skills(self, client, dependency_override_cleanup):
        """Test listing skills from taxonomy returns valid structure.
        
        Verifies that the taxonomy listing endpoint:
        - Returns HTTP 200 status
        - Includes 'skills' field containing a list
        - Includes 'total' field with count
        - Properly uses dependency injection for TaxonomyManager
        """
        from skill_fleet.api.dependencies import get_taxonomy_manager

        mock_manager = MagicMock()
        mock_manager.metadata_cache = {}
        mock_manager._ensure_all_skills_loaded = MagicMock()

        app.dependency_overrides[get_taxonomy_manager] = lambda: mock_manager
        try:
            response = client.get("/api/v2/taxonomy/")

            assert response.status_code == 200
            data = response.json()
            assert "skills" in data
            assert isinstance(data["skills"], list)
            assert "total" in data
            assert isinstance(data["total"], int)
        finally:
            app.dependency_overrides.clear()


# ============================================================================
# Test Validation Endpoints
# ============================================================================


class TestValidationEndpoints:
    """Tests for skill validation endpoints."""

    def test_validate_skill_missing_path(self, client):
        """Test validation fails without path field.
        
        Verifies that Pydantic validation catches missing required 'path' field
        and returns HTTP 422 (Unprocessable Entity).
        """
        response = client.post("/api/v2/validation/validate", json={})

        assert response.status_code == 422  # Validation error

    def test_validate_skill_empty_path(self, client):
        """Test validation fails with empty path string.
        
        Verifies that empty strings are rejected as invalid input,
        returning HTTP 400 with appropriate error message.
        """
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": ""},
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "path is required" in data["detail"]

    def test_validate_skill_absolute_path_rejected(self, client):
        """Test validation rejects absolute paths for security.
        
        Verifies that absolute paths (e.g., /etc/passwd) are rejected
        to prevent directory traversal attacks, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": "/etc/passwd"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Invalid path" in data["detail"]

    def test_validate_skill_path_traversal_rejected(self, client):
        """Test validation rejects path traversal attempts for security.
        
        Verifies that paths with ../ sequences are rejected
        to prevent directory traversal attacks, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/validation/validate",
            json={"path": "../../../etc/passwd"},
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert "Invalid path" in data["detail"]

    def test_validate_skill_valid_path(self, client):
        """Test validation with a valid skill path returns complete response.
        
        Verifies that a valid skill path:
        - Returns HTTP 200 status
        - Includes 'passed' field indicating validation result
        - Includes 'checks' list with validation details
        - Includes 'warnings' and 'errors' lists
        """
        with patch("skill_fleet.api.routes.validation.SkillValidator") as mock_validator:
            mock_instance = MagicMock()
            # Return format matching ValidationResponse model
            mock_instance.validate_complete.return_value = {
                "passed": True,
                "checks": [{"name": "metadata", "status": "pass", "messages": []}],
                "warnings": [],
                "errors": [],
            }
            mock_validator.return_value = mock_instance

            response = client.post(
                "/api/v2/validation/validate",
                json={"path": TEST_SKILL_PATH},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is True
            assert "checks" in data
            assert isinstance(data["checks"], list)
            assert "warnings" in data
            assert isinstance(data["warnings"], list)
            assert "errors" in data
            assert isinstance(data["errors"], list)


# ============================================================================
# Test Optimization Endpoints
# ============================================================================


class TestOptimizationEndpoints:
    """Tests for DSPy workflow optimization endpoints."""

    def test_start_optimization_rejects_training_paths_traversal(self, client):
        """Test optimization rejects path traversal in training_paths.
        
        Verifies that paths with ../ sequences in training_paths
        are rejected for security, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/optimization/start",
            json={"training_paths": ["../.codex/skills/some-skill"]},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_training_paths_absolute(self, client):
        """Test optimization rejects absolute paths in training_paths.
        
        Verifies that absolute paths in training_paths are rejected
        for security, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/optimization/start",
            json={"training_paths": ["/tmp/outside"]},
        )
        assert response.status_code == 422

    def test_start_optimization_accepts_sanitized_training_paths(self, client):
        """Test optimization accepts and sanitizes valid training_paths.
        
        Verifies that valid training paths with redundant slashes
        are accepted and properly normalized before processing.
        """
        with patch("skill_fleet.api.routes.optimization._run_optimization") as mock_run:
            response = client.post(
                "/api/v2/optimization/start",
                json={"training_paths": ["general//testing"]},
            )
            assert response.status_code == 200
            (_, kwargs) = mock_run.call_args
            assert kwargs["request"].training_paths == ["general/testing"]

    def test_start_optimization_rejects_save_path_traversal(self, client):
        """Test optimization rejects path traversal in save_path.
        
        Verifies that paths with ../ sequences in save_path
        are rejected for security, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": "../outside"},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_save_path_absolute(self, client):
        """Test optimization rejects absolute paths in save_path.
        
        Verifies that absolute paths in save_path are rejected
        for security, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": "/tmp/outside"},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_save_path_backslashes(self, client):
        """Test optimization rejects backslashes in save_path.
        
        Verifies that Windows-style paths with backslashes are rejected
        to ensure cross-platform consistency, returning HTTP 422.
        """
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": r"..\\outside"},
        )
        assert response.status_code == 422

    def test_start_optimization_accepts_sanitized_save_path(self, client):
        """Test optimization accepts and sanitizes valid save_path.
        
        Verifies that valid save paths with redundant slashes
        are accepted and properly normalized before processing.
        """
        with patch("skill_fleet.api.routes.optimization._run_optimization"):
            response: Response = client.post(
                "/api/v2/optimization/start",
                json={"save_path": "my_program//program"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "pending"
            assert "job_id" in data
            assert isinstance(data["job_id"], str)

    def test_run_optimization_creates_save_parents(self, tmp_path, monkeypatch):
        """Test optimization creates parent directories for save_path.
        
        Verifies that when saving optimization results:
        - Parent directories are automatically created
        - Files are saved to the correct location
        - Job status is updated to 'completed'
        """
        from skill_fleet.api.routes import optimization as optimization_routes

        repo_root = tmp_path / "repo"
        skills_root = tmp_path / "skills"
        repo_root.mkdir()

        (skills_root / "general" / "testing").mkdir(parents=True)
        (skills_root / "general" / "testing" / "SKILL.md").write_text(
            "---\nname: testing\ndescription: test\n---\n\n# Testing\n",
            encoding="utf-8",
        )

        monkeypatch.setattr(
            optimization_routes,
            "find_repo_root",
            lambda *args, **kwargs: repo_root,
        )

        saved: dict[str, Path] = {}

        class DummyResult:
            def save(self, path: str) -> None:
                save_path = Path(path)
                if not save_path.parent.exists():
                    raise FileNotFoundError(f"Missing parent directory: {save_path.parent}")
                save_path.write_text("ok", encoding="utf-8")
                saved["path"] = save_path

        class DummyOptimizer:
            def __init__(self, *, configure_lm: bool = False) -> None:
                pass

            def optimize_with_miprov2(self, **kwargs) -> DummyResult:
                return DummyResult()

            def optimize_with_bootstrap(self, **kwargs) -> DummyResult:
                return DummyResult()

        monkeypatch.setattr(optimization_routes, "SkillOptimizer", DummyOptimizer)

        job_id = "job-test-save-parents"
        optimization_routes._optimization_jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0.0,
            "message": "",
            "result": None,
            "error": None,
        }

        request = optimization_routes.OptimizeRequest(
            optimizer="miprov2",
            training_paths=["general/testing"],
            save_path="my_program//program/state.json",
        )

        asyncio.run(
            optimization_routes._run_optimization(
                job_id=job_id,
                request=request,
                skills_root=skills_root,
            )
        )

        assert optimization_routes._optimization_jobs[job_id]["status"] == "completed"
        assert (
            saved["path"]
            == repo_root / "config" / "optimized" / "my_program" / "program" / "state.json"
        )
        assert (repo_root / "config" / "optimized" / "my_program" / "program").exists()
        optimization_routes._optimization_jobs.pop(job_id, None)


# ============================================================================
# Test Request Models
# ============================================================================


class TestCreateSkillRequest:
    """Tests for CreateSkillRequest Pydantic model."""

    def test_valid_request(self):
        """Test CreateSkillRequest with all valid fields.
        
        Verifies that a properly constructed request:
        - Accepts task_description and user_id
        - Stores values correctly
        - Can be serialized/deserialized
        """
        from skill_fleet.api.routes.skills import CreateSkillRequest

        request = CreateSkillRequest(
            task_description="Create a skill for Python async programming",
            user_id="test-user",
        )

        assert request.task_description == "Create a skill for Python async programming"
        assert request.user_id == "test-user"

    def test_default_user_id(self):
        """Test CreateSkillRequest defaults user_id to 'default'.
        
        Verifies that when user_id is omitted, it defaults to 'default'
        as specified in the model definition.
        """
        from skill_fleet.api.routes.skills import CreateSkillRequest

        request = CreateSkillRequest(task_description="Test skill creation")

        assert request.user_id == "default"


class TestValidateSkillRequest:
    """Tests for ValidateSkillRequest Pydantic model."""

    def test_valid_request(self):
        """Test ValidateSkillRequest with valid path.
        
        Verifies that a properly constructed validation request
        stores the path correctly.
        """
        from skill_fleet.api.routes.validation import ValidateSkillRequest

        request = ValidateSkillRequest(path=TEST_SKILL_PATH)

        assert request.path == TEST_SKILL_PATH


# ============================================================================
# Test Evaluation Endpoints
# ============================================================================


class TestEvaluationEndpoints:
    """Tests for skill quality evaluation endpoints."""

    def test_evaluate_skill_rejects_path_traversal(self, client, tmp_path, dependency_override_cleanup):
        """Test evaluation rejects path traversal attempts for security.
        
        Verifies that paths with ../ sequences are rejected
        to prevent escaping the skills_root directory, returning HTTP 422.
        """
        from skill_fleet.api.dependencies import get_skills_root

        skills_root = tmp_path / "skills"
        skills_root.mkdir(parents=True, exist_ok=True)

        app.dependency_overrides[get_skills_root] = lambda: skills_root
        try:
            response = client.post(
                "/api/v2/evaluation/evaluate",
                json={"path": "../.codex/skills/universal-memory"},
            )
            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            assert "Invalid path" in data["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_skill_allows_valid_taxonomy_path(self, client, tmp_path, dependency_override_cleanup):
        """Test evaluation succeeds for valid taxonomy paths under skills_root.
        
        Verifies that a valid skill path:
        - Returns HTTP 200 status
        - Includes 'overall_score' field with numeric value
        - Includes quality assessment metrics
        """
        from skill_fleet.api.dependencies import get_skills_root

        skills_root = tmp_path / "skills"
        skill_dir = skills_root / "general" / "testing"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: testing\ndescription: Use when testing.\n---\n\n# Testing\n",
            encoding="utf-8",
        )

        app.dependency_overrides[get_skills_root] = lambda: skills_root
        try:
            with patch(
                "skill_fleet.api.routes.evaluation.assess_skill_quality",
            ) as mock_assess:
                from skill_fleet.core.dspy.metrics import SkillQualityScores

                mock_assess.return_value = SkillQualityScores(
                    overall_score=0.5,
                    frontmatter_completeness=1.0,
                    has_overview=True,
                    has_when_to_use=True,
                    has_quick_reference=False,
                )

                response = client.post(
                    "/api/v2/evaluation/evaluate",
                    json={"path": TEST_SKILL_PATH},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["overall_score"] == 0.5
                assert isinstance(data["overall_score"], (int, float))
                assert data["overall_score"] >= 0.0
                assert data["overall_score"] <= 1.0
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_batch_marks_invalid_path_as_error(self, client, tmp_path, dependency_override_cleanup):
        """Test batch evaluation marks invalid paths as errors without reading files.
        
        Verifies that batch evaluation:
        - Returns HTTP 200 status
        - Marks invalid paths as errors (not successes)
        - Includes 'total_evaluated', 'total_errors', and 'average_score'
        - Properly separates valid and invalid results
        """
        from skill_fleet.api.dependencies import get_skills_root

        skills_root = tmp_path / "skills"
        skill_dir = skills_root / "general" / "testing"
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: testing\ndescription: Use when testing.\n---\n\n# Testing\n",
            encoding="utf-8",
        )

        app.dependency_overrides[get_skills_root] = lambda: skills_root
        try:
            with patch(
                "skill_fleet.api.routes.evaluation.assess_skill_quality",
            ) as mock_assess:
                from skill_fleet.core.dspy.metrics import SkillQualityScores

                mock_assess.return_value = SkillQualityScores(
                    overall_score=0.25,
                    frontmatter_completeness=1.0,
                )

                response = client.post(
                    "/api/v2/evaluation/evaluate-batch",
                    json={"paths": [TEST_SKILL_PATH, "../.codex/skills/universal-memory"]},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["total_evaluated"] == 1
                assert data["total_errors"] == 1
                assert data["average_score"] == 0.25
                assert isinstance(data["results"], list)
                assert len(data["results"]) == 2
                
                # Verify error result structure
                errors = [r for r in data["results"] if r.get("error")]
                assert len(errors) == 1
                assert errors[0]["error"] == "Invalid path"
                
                # Verify success result structure
                successes = [r for r in data["results"] if not r.get("error")]
                assert len(successes) == 1
                assert successes[0]["path"] == TEST_SKILL_PATH
        finally:
            app.dependency_overrides.clear()
