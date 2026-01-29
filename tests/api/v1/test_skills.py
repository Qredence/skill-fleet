"""Tests for skills router endpoints.

Tests CRUD operations for the skills API including:
- Create skill (POST /api/v1/skills)
- Get skill (GET /api/v1/skills/{skill_id})
- Update skill (PUT /api/v1/skills/{skill_id})
- Validate skill (POST /api/v1/skills/{skill_id}/validate)
- Refine skill (POST /api/v1/skills/{skill_id}/refine)
"""

from __future__ import annotations

from unittest.mock import patch

# =============================================================================
# Test Create Skill Endpoint
# =============================================================================


class TestCreateSkill:
    """Tests for POST /api/v1/skills endpoint."""

    def test_create_skill_success(self, client, valid_skill_request, mock_skill_service):
        """Test successful skill creation returns job ID."""
        response = client.post("/api/v1/skills", json=valid_skill_request)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        mock_skill_service.create_skill.assert_called_once()

    def test_create_skill_missing_description(self, client):
        """Test validation error when description is missing."""
        response = client.post("/api/v1/skills", json={"user_id": "test-user"})

        assert response.status_code == 422
        assert "task_description" in str(response.json())

    def test_create_skill_empty_description(self, client):
        """Test validation error when description is empty."""
        response = client.post(
            "/api/v1/skills", json={"task_description": "", "user_id": "test-user"}
        )

        assert response.status_code == 422

    def test_create_skill_invalid_json(self, client):
        """Test error handling for invalid JSON."""
        response = client.post(
            "/api/v1/skills", data="invalid json", headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


# =============================================================================
# Test Get Skill Endpoint
# =============================================================================


class TestGetSkill:
    """Tests for GET /api/v1/skills/{skill_id} endpoint."""

    def test_get_skill_success(self, client, sample_skill):
        """Test retrieving an existing skill."""
        with patch("skill_fleet.api.v1.skills.get_skill_by_id") as mock_get:
            mock_get.return_value = sample_skill

            response = client.get(f"/api/v1/skills/{sample_skill['skill_id']}")

            assert response.status_code == 200
            data = response.json()
            assert data["skill_id"] == sample_skill["skill_id"]
            assert data["name"] == sample_skill["name"]

    def test_get_skill_not_found(self, client):
        """Test 404 response for non-existent skill."""
        with patch("skill_fleet.api.v1.skills.get_skill_by_id") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/skills/non-existent-id")

            assert response.status_code == 404

    def test_get_skill_invalid_id_format(self, client):
        """Test error handling for invalid skill ID format."""
        response = client.get("/api/v1/skills/invalid<>id")

        # Should either return 404 or 422 depending on validation
        assert response.status_code in [404, 422]


# =============================================================================
# Test Update Skill Endpoint
# =============================================================================


class TestUpdateSkill:
    """Tests for PUT /api/v1/skills/{skill_id} endpoint."""

    def test_update_skill_success(self, client, sample_skill):
        """Test successful skill update."""
        update_data = {"name": "Updated Skill Name", "description": "Updated description"}

        with patch("skill_fleet.api.v1.skills.update_skill") as mock_update:
            mock_update.return_value = {**sample_skill, **update_data}

            response = client.put(f"/api/v1/skills/{sample_skill['skill_id']}", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == update_data["name"]

    def test_update_skill_not_found(self, client):
        """Test 404 when updating non-existent skill."""
        with patch("skill_fleet.api.v1.skills.update_skill") as mock_update:
            mock_update.return_value = None

            response = client.put("/api/v1/skills/non-existent-id", json={"name": "New Name"})

            assert response.status_code == 404

    def test_update_skill_partial(self, client, sample_skill):
        """Test partial update (only some fields)."""
        update_data = {"description": "Only updating description"}

        with patch("skill_fleet.api.v1.skills.update_skill") as mock_update:
            mock_update.return_value = {**sample_skill, **update_data}

            response = client.put(f"/api/v1/skills/{sample_skill['skill_id']}", json=update_data)

            assert response.status_code == 200


# =============================================================================
# Test Validate Skill Endpoint
# =============================================================================


class TestValidateSkill:
    """Tests for POST /api/v1/skills/{skill_id}/validate endpoint."""

    def test_validate_skill_success(self, client, sample_skill, mock_skill_service):
        """Test successful skill validation."""
        mock_skill_service.validate_skill.return_value = {
            "valid": True,
            "score": 0.95,
            "issues": [],
        }

        response = client.post(f"/api/v1/skills/{sample_skill['skill_id']}/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["score"] == 0.95

    def test_validate_skill_with_issues(self, client, sample_skill, mock_skill_service):
        """Test validation with issues found."""
        mock_skill_service.validate_skill.return_value = {
            "valid": False,
            "score": 0.65,
            "issues": ["Missing examples", "Description too short"],
        }

        response = client.post(f"/api/v1/skills/{sample_skill['skill_id']}/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["issues"]) > 0

    def test_validate_skill_not_found(self, client):
        """Test 404 when validating non-existent skill."""
        response = client.post("/api/v1/skills/non-existent-id/validate")

        assert response.status_code == 404


# =============================================================================
# Test Refine Skill Endpoint
# =============================================================================


class TestRefineSkill:
    """Tests for POST /api/v1/skills/{skill_id}/refine endpoint."""

    def test_refine_skill_success(self, client, sample_skill):
        """Test successful skill refinement."""
        refine_request = {"feedback": "Add more examples", "focus_areas": ["examples", "clarity"]}

        with patch("skill_fleet.api.v1.skills.refine_skill") as mock_refine:
            mock_refine.return_value = {
                "job_id": "refine-job-789",
                "status": "pending",
                "message": "Refinement started",
            }

            response = client.post(
                f"/api/v1/skills/{sample_skill['skill_id']}/refine", json=refine_request
            )

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert data["status"] == "pending"

    def test_refine_skill_not_found(self, client):
        """Test 404 when refining non-existent skill."""
        response = client.post(
            "/api/v1/skills/non-existent-id/refine", json={"feedback": "Test feedback"}
        )

        assert response.status_code == 404

    def test_refine_skill_missing_feedback(self, client, sample_skill):
        """Test validation error when feedback is missing."""
        response = client.post(f"/api/v1/skills/{sample_skill['skill_id']}/refine", json={})

        assert response.status_code == 422


# =============================================================================
# Test List Skills Endpoint
# =============================================================================


class TestListSkills:
    """Tests for GET /api/v1/skills endpoint."""

    def test_list_skills_success(self, client):
        """Test listing all skills."""
        with patch("skill_fleet.api.v1.skills.list_skills") as mock_list:
            mock_list.return_value = [
                {"skill_id": "skill-1", "name": "Skill 1"},
                {"skill_id": "skill-2", "name": "Skill 2"},
            ]

            response = client.get("/api/v1/skills")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 2

    def test_list_skills_empty(self, client):
        """Test listing skills when none exist."""
        with patch("skill_fleet.api.v1.skills.list_skills") as mock_list:
            mock_list.return_value = []

            response = client.get("/api/v1/skills")

            assert response.status_code == 200
            data = response.json()
            assert data == []

    def test_list_skills_with_filters(self, client):
        """Test listing skills with query filters."""
        with patch("skill_fleet.api.v1.skills.list_skills") as mock_list:
            mock_list.return_value = [
                {"skill_id": "skill-1", "name": "Python Skill", "status": "active"}
            ]

            response = client.get("/api/v1/skills?status=active&search=python")

            assert response.status_code == 200
            mock_list.assert_called_once()
