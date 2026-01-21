"""Tests for training analytics API."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from skill_fleet.api.app import create_app
from skill_fleet.config.training.manager import ExampleMetadata


def test_get_training_analytics():
    """Test getting training analytics."""
    app = create_app()
    client = TestClient(app)

    with patch("skill_fleet.api.routes.training.TrainingDataManager") as MockManager:
        manager_instance = MockManager.return_value

        # Mock metadata
        manager_instance._metadata = {
            "1": ExampleMetadata(
                example_id="1",
                task_description="Task 1",
                category="technical",
                quality_score=0.9,
                success_rate=1.0,
            ),
            "2": ExampleMetadata(
                example_id="2",
                task_description="Task 2",
                category="domain",
                quality_score=0.4,
                success_rate=0.2,
            ),
        }

        response = client.get("/api/v2/training/analytics")

        assert response.status_code == 200
        data = response.json()

        assert data["total_examples"] == 2
        assert data["quality_distribution"]["high (>=0.8)"] == 1
        assert data["quality_distribution"]["low (<0.5)"] == 1
        assert len(data["top_performers"]) > 0
