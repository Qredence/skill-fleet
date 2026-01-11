"""Unit tests for FastAPI skill creation API.

Tests the FastAPI endpoints in src/skill_fleet/api/app.py

Based on: https://dspy.ai/tutorials/deployment/#deploying-with-fastapi
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture
def mock_agent():
    """Mock ConversationalSkillAgent."""
    with patch("skill_fleet.api.app.ConversationalSkillAgent") as mock:
        yield mock


# ============================================================================
# Test Root Endpoint
# ============================================================================


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data
        assert "streaming" in data


# ============================================================================
# Test Health Endpoint
# ============================================================================


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @patch("skill_fleet.api.app.dspy")
    def test_health_returns_healthy_status(self, mock_dspy, client):
        """Test health endpoint returns healthy status."""
        mock_dspy.settings.async_max_workers = 4

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["async_workers"] == 4

    @patch("skill_fleet.api.app.dspy")
    def test_health_with_custom_workers(self, mock_dspy, client):
        """Test health endpoint reflects custom worker count."""
        mock_dspy.settings.async_max_workers = 8

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["async_workers"] == 8


# ============================================================================
# Test Create Skill Endpoint (Non-Streaming)
# ============================================================================


class TestCreateSkillEndpoint:
    """Tests for /api/v1/create-skill endpoint."""

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_create_skill_success(
        self, mock_agent_class, mock_create_async, mock_configure_llm, client
    ):
        """Test successful skill creation."""
        # Setup mocks
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_async_agent = AsyncMock()
        mock_async_agent.return_value = MagicMock(
            toDict=lambda: {"skill_id": "test-skill", "content": "..."}
        )
        mock_create_async.return_value = mock_async_agent

        # Make request
        response = client.post(
            "/api/v1/create-skill",
            json={"task_description": "Create an OpenAPI skill"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["skill_id"] == "test-skill"

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_create_skill_with_stream_false(
        self, mock_agent_class, mock_create_async, mock_configure_llm, client
    ):
        """Test skill creation with stream=false."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_async_agent = AsyncMock()
        mock_async_agent.return_value = MagicMock(toDict=lambda: {"result": "ok"})
        mock_create_async.return_value = mock_async_agent

        response = client.post(
            "/api/v1/create-skill",
            json={"task_description": "Test skill creation", "stream": False},
        )

        assert response.status_code == 200

    def test_create_skill_missing_description(self, client):
        """Test skill creation fails without description."""
        response = client.post("/api/v1/create-skill", json={})

        assert response.status_code == 422  # Validation error

    def test_create_skill_short_description(self, client):
        """Test skill description must be at least 10 characters."""
        response = client.post("/api/v1/create-skill", json={"task_description": "Short"})

        assert response.status_code == 422  # Validation error

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_create_skill_handles_exception(
        self, mock_agent_class, mock_create_async, mock_configure_llm, client
    ):
        """Test skill creation handles exceptions gracefully."""
        mock_agent_class.side_effect = Exception("Test error")

        response = client.post(
            "/api/v1/create-skill",
            json={"task_description": "Create a test skill"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"]


# ============================================================================
# Test Create Skill Stream Endpoint
# ============================================================================


class TestCreateSkillStreamEndpoint:
    """Tests for /api/v1/create-skill/stream endpoint."""

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.create_streaming_module")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_stream_returns_sse_headers(
        self,
        mock_agent_class,
        mock_create_async,
        mock_create_streaming,
        mock_configure_llm,
        client,
    ):
        """Test streaming endpoint returns correct headers."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_async_agent = MagicMock()
        mock_create_async.return_value = mock_async_agent

        # Mock streaming program that yields nothing
        async def mock_stream(**kwargs):
            return
            yield  # Make this a generator (unreachable but required)

        mock_streaming = MagicMock()
        mock_streaming.return_value = mock_stream()
        mock_create_streaming.return_value = mock_streaming

        response = client.post(
            "/api/v1/create-skill/stream",
            json={"task_description": "Create a test skill"},
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"
        assert "connection" in response.headers

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.stream_dspy_response")
    @patch("skill_fleet.api.app.create_streaming_module")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_stream_yields_sse_format(
        self,
        mock_agent_class,
        mock_create_async,
        mock_create_streaming,
        mock_stream_dspy_response,
        mock_configure_llm,
        client,
    ):
        """Test streaming endpoint yields SSE formatted data."""
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent
        mock_async_agent = MagicMock()
        mock_create_async.return_value = mock_async_agent

        # Mock streaming module (returned by create_streaming_module)
        mock_streaming_module = MagicMock()

        # Mock streaming response generator
        async def mock_stream_response(**kwargs):
            yield 'data: {"type": "status", "message": "Starting"}\n\n'
            yield 'data: {"type": "reasoning", "chunk": "Thinking"}\n\n'
            yield 'data: {"type": "prediction", "data": {}}\n\n'
            yield "data: [DONE]\n\n"

        mock_create_streaming.return_value = mock_streaming_module
        mock_stream_dspy_response.return_value = mock_stream_response()

        response = client.post(
            "/api/v1/create-skill/stream",
            json={"task_description": "Test skill"},
        )

        assert response.status_code == 200

        # Check SSE content
        content = response.text
        assert 'data: {"type": "status"' in content
        assert "data: [DONE]" in content

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.create_streaming_module")
    @patch("skill_fleet.api.app.create_async_module")
    @patch("skill_fleet.agent.agent.ConversationalSkillAgent")
    def test_stream_handles_exception(
        self,
        mock_agent_class,
        mock_create_async,
        mock_create_streaming,
        mock_configure_llm,
        client,
    ):
        """Test streaming endpoint handles exceptions."""
        mock_agent_class.side_effect = Exception("Stream error")

        response = client.post(
            "/api/v1/create-skill/stream",
            json={"task_description": "Test skill"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "Stream error" in data["detail"]


# ============================================================================
# Test Request Models
# ============================================================================


class TestTaskRequest:
    """Tests for TaskRequest pydantic model."""

    def test_valid_task_request(self):
        """Test valid task request."""
        from skill_fleet.api.app import TaskRequest

        request = TaskRequest(
            task_description="Create an OpenAPI skill for REST endpoints",
            stream=True,
        )

        assert request.task_description == "Create an OpenAPI skill for REST endpoints"
        assert request.stream is True

    def test_task_request_default_stream(self):
        """Test stream defaults to True."""
        from skill_fleet.api.app import TaskRequest

        request = TaskRequest(task_description="Test skill creation")

        assert request.stream is True

    def test_task_request_validation_too_short(self):
        """Test task description must be at least 10 characters."""
        from pydantic import ValidationError

        from skill_fleet.api.app import TaskRequest

        with pytest.raises(ValidationError):
            TaskRequest(task_description="Short")

    def test_task_request_validation_exact_min_length(self):
        """Test task description with exactly 10 characters."""
        from skill_fleet.api.app import TaskRequest

        # 10 characters exactly
        request = TaskRequest(task_description="1234567890")

        assert request.task_description == "1234567890"


# ============================================================================
# Test Response Models
# ============================================================================


class TestTaskResponse:
    """Tests for TaskResponse pydantic model."""

    def test_task_response_with_data(self):
        """Test task response with data."""
        from skill_fleet.api.app import TaskResponse

        response = TaskResponse(status="success", data={"skill_id": "test", "content": "..."})

        assert response.status == "success"
        assert response.data["skill_id"] == "test"

    def test_task_response_without_data(self):
        """Test task response without data."""
        from skill_fleet.api.app import TaskResponse

        response = TaskResponse(status="success")

        assert response.status == "success"
        assert response.data is None


# ============================================================================
# Test Startup/Shutdown Events
# ============================================================================


class TestLifecycleEvents:
    """Tests for startup and shutdown events."""

    @patch("skill_fleet.api.app._configure_llm")
    @patch("skill_fleet.api.app.logger")
    def test_startup_event(self, mock_logger, mock_configure_llm):
        """Test startup event initializes resources."""
        from fastapi.testclient import TestClient

        # Startup runs automatically when TestClient is created
        with TestClient(app):
            pass  # Startup/shutdown tested

    @patch("skill_fleet.api.app.logger")
    def test_shutdown_event(self, mock_logger):
        """Test shutdown event logs message."""
        from fastapi.testclient import TestClient

        with TestClient(app):
            pass  # Shutdown happens on context exit


# ============================================================================
# Test Helper Functions
# ============================================================================


class TestStreamDspyResponse:
    """Tests for stream_dspy_response generator function."""

    @pytest.mark.asyncio
    async def test_stream_dspy_response_yields_sse(self):
        """Test stream_dspy_response yields SSE formatted chunks."""
        from skill_fleet.api.app import stream_dspy_response
        from skill_fleet.common.streaming import StubStatusMessage

        # Mock streaming program
        mock_status = StubStatusMessage("Test status")

        async def mock_program(**kwargs):
            yield mock_status
            return

        # Collect chunks
        chunks = []
        async for chunk in stream_dspy_response(mock_program):
            chunks.append(chunk)

        assert len(chunks) == 2  # status + [DONE]
        assert '"type": "status"' in chunks[0]
        assert '"message": "Test status"' in chunks[0]
        assert chunks[1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_stream_dspy_response_passes_kwargs(self):
        """Test kwargs are passed to streaming program."""
        from skill_fleet.api.app import stream_dspy_response

        async def mock_program(**kwargs):
            assert kwargs.get("task_description") == "Test task"
            return
            yield  # pylint: disable=unreachable

        async for _ in stream_dspy_response(mock_program, task_description="Test task"):
            pass
