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
        """Test getting prompt for a non-existent job returns 404."""
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
        # Create a job (a background task is mocked)
        create_response = client.post(
            "/api/v2/skills/create",
            json={"task_description": "Create a skill for Docker best practices"},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        # Get the prompt - job exists but may be in the initial state
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
        # Use dependency override for the TaxonomyManager dependency
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
        finally:
            app.dependency_overrides.clear()


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
        """Test validation with a valid skill path."""
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
                json={"path": "general/testing"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["passed"] is True
            assert "checks" in data
            assert "warnings" in data
            assert "errors" in data


# ============================================================================
# Test Optimization Endpoints
# ============================================================================


class TestOptimizationEndpoints:
    """Tests for optimization endpoints."""

    def test_start_optimization_rejects_training_paths_traversal(self, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"training_paths": ["../.codex/skills/some-skill"]},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_training_paths_absolute(self, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"training_paths": ["/tmp/outside"]},
        )
        assert response.status_code == 422

    @patch("skill_fleet.api.routes.optimization._run_optimization")
    def test_start_optimization_accepts_sanitized_training_paths(self, mock_run, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"training_paths": ["general//testing"]},
        )
        assert response.status_code == 200
        (_, kwargs) = mock_run.call_args
        assert kwargs["request"].training_paths == ["general/testing"]

    def test_start_optimization_rejects_save_path_traversal(self, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": "../outside"},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_save_path_absolute(self, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": "/tmp/outside"},
        )
        assert response.status_code == 422

    def test_start_optimization_rejects_save_path_backslashes(self, client):
        response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": r"..\\outside"},
        )
        assert response.status_code == 422

    @patch("skill_fleet.api.routes.optimization._run_optimization")
    def test_start_optimization_accepts_sanitized_save_path(self, mock_run, client):
        response: Response = client.post(
            "/api/v2/optimization/start",
            json={"save_path": "my_program//program"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "job_id" in data

    def test_run_optimization_creates_save_parents(self, tmp_path, monkeypatch):
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


# ============================================================================
# Test Evaluation Endpoints
# ============================================================================


class TestEvaluationEndpoints:
    """Tests for evaluation endpoints."""

    def test_evaluate_skill_rejects_path_traversal(self, client, tmp_path):
        """Test evaluation rejects traversal attempts that could escape skills_root."""
        from skill_fleet.api.dependencies import get_skills_root

        skills_root = tmp_path / "skills"
        skills_root.mkdir(parents=True, exist_ok=True)

        app.dependency_overrides[get_skills_root] = lambda: skills_root
        try:
            response = client.post(
                "/api/v2/evaluation/evaluate",
                json={"path": "../.codex/skills/universal-memory"},
            )
            assert response.status_code == 400
            assert "Invalid path" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_skill_allows_valid_taxonomy_path(self, client, tmp_path):
        """Test evaluation succeeds for a valid taxonomy path under skills_root."""
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
                    json={"path": "general/testing"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["overall_score"] == 0.5
        finally:
            app.dependency_overrides.clear()

    def test_evaluate_batch_marks_invalid_path_as_error(self, client, tmp_path):
        """Test batch evaluation marks invalid paths as errors rather than reading files."""
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
                    json={"paths": ["general/testing", "../.codex/skills/universal-memory"]},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["total_evaluated"] == 1
                assert data["total_errors"] == 1
                assert data["average_score"] == 0.25
                errors = [r for r in data["results"] if r.get("error")]
                assert len(errors) == 1
                assert errors[0]["error"] == "Invalid path"
        finally:
            app.dependency_overrides.clear()
