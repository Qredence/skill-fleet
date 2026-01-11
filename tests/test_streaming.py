"""Unit tests for DSPy streaming integration.

Tests the streaming utilities in src/skill_fleet/common/streaming.py

Based on: https://dspy.ai/tutorials/streaming/
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import dspy
import pytest

from skill_fleet.common.streaming import (
    SkillFleetStatusProvider,
    StubPrediction,
    StubStatusMessage,
    StubStreamResponse,
    create_async_module,
    create_streaming_module,
    process_stream_sync,
    stream_dspy_response,
)

# ============================================================================
# Test SkillFleetStatusProvider
# ============================================================================


class TestSkillFleetStatusProvider:
    """Tests for SkillFleetStatusProvider."""

    def test_lm_start_status_message(self):
        """Test status message at start of LLM call."""
        provider = SkillFleetStatusProvider()
        instance = MagicMock()
        inputs = {"question": "test"}

        message = provider.lm_start_status_message(instance, inputs)

        assert message == "🤖 Calling LLM..."

    def test_lm_end_status_message(self):
        """Test status message at end of LLM call."""
        provider = SkillFleetStatusProvider()
        prediction = MagicMock()

        message = provider.lm_end_status_message(prediction)

        assert message == "✅ LLM call complete"

    def test_module_start_status_message(self):
        """Test status message at start of module execution."""
        provider = SkillFleetStatusProvider()
        instance = MagicMock()
        instance.__class__.__name__ = "TestModule"
        inputs = {}

        message = provider.module_start_status_message(instance, inputs)

        assert message == "🔄 Running TestModule..."

    def test_module_end_status_message(self):
        """Test status message at end of module execution."""
        provider = SkillFleetStatusProvider()
        prediction = MagicMock()

        message = provider.module_end_status_message(prediction)

        assert message == "✅ Module complete"

    def test_tool_start_status_message(self):
        """Test status message at start of tool call."""
        provider = SkillFleetStatusProvider()
        instance = MagicMock()
        instance.name = "test_tool"
        inputs = {}

        message = provider.tool_start_status_message(instance, inputs)

        assert message == "🔧 Calling tool: test_tool..."

    def test_tool_start_status_message_no_name(self):
        """Test status message when tool has no name."""
        provider = SkillFleetStatusProvider()
        instance = MagicMock(spec=[])  # No 'name' attribute
        inputs = {}

        message = provider.tool_start_status_message(instance, inputs)

        assert message == "🔧 Calling tool: unknown_tool..."

    def test_tool_end_status_message(self):
        """Test status message at end of tool call."""
        provider = SkillFleetStatusProvider()
        outputs = MagicMock()

        message = provider.tool_end_status_message(outputs)

        assert message == "✅ Tool call complete"


# ============================================================================
# Test create_streaming_module
# ============================================================================


class TestCreateStreamingModule:
    """Tests for create_streaming_module function."""

    @patch("skill_fleet.common.streaming.dspy.streamify")
    def test_create_streaming_module_sync(self, mock_streamify):
        """Test creating streaming module in sync mode (for CLI)."""
        mock_module = MagicMock()
        mock_result = MagicMock()
        mock_streamify.return_value = mock_result

        result = create_streaming_module(
            mock_module,
            reasoning_field="reasoning",
            async_mode=False,
        )

        assert result == mock_result
        mock_streamify.assert_called_once()
        call_args = mock_streamify.call_args
        assert call_args[1]["async_streaming"] is False
        assert len(call_args[1]["stream_listeners"]) == 1
        assert call_args[1]["stream_listeners"][0].signature_field_name == "reasoning"
        assert isinstance(call_args[1]["status_message_provider"], SkillFleetStatusProvider)

    @patch("skill_fleet.common.streaming.dspy.streamify")
    def test_create_streaming_module_async(self, mock_streamify):
        """Test creating streaming module in async mode (for FastAPI)."""
        mock_module = MagicMock()
        mock_result = MagicMock()
        mock_streamify.return_value = mock_result

        result = create_streaming_module(
            mock_module,
            reasoning_field="custom_reasoning",
            async_mode=True,
        )

        assert result == mock_result
        mock_streamify.assert_called_once()
        call_args = mock_streamify.call_args
        assert call_args[1]["async_streaming"] is True
        assert call_args[1]["stream_listeners"][0].signature_field_name == "custom_reasoning"

    @patch("skill_fleet.common.streaming.dspy.streamify")
    def test_create_streaming_module_default_values(self, mock_streamify):
        """Test default values for create_streaming_module."""
        mock_module = MagicMock()
        mock_result = MagicMock()
        mock_streamify.return_value = mock_result

        result = create_streaming_module(mock_module)

        assert result == mock_result
        call_args = mock_streamify.call_args
        assert call_args[1]["async_streaming"] is False  # Default to sync
        assert call_args[1]["stream_listeners"][0].signature_field_name == "reasoning"


# ============================================================================
# Test create_async_module
# ============================================================================


class TestCreateAsyncModule:
    """Tests for create_async_module function."""

    @patch("skill_fleet.common.streaming.dspy.configure")
    @patch("skill_fleet.common.streaming.dspy.asyncify")
    def test_create_async_module_default_workers(self, mock_asyncify, mock_configure):
        """Test creating async module with default workers."""
        mock_module = MagicMock()
        mock_result = MagicMock()
        mock_asyncify.return_value = mock_result

        result = create_async_module(mock_module)

        assert result == mock_result
        mock_configure.assert_called_once_with(async_max_workers=4)
        mock_asyncify.assert_called_once_with(mock_module)

    @patch("skill_fleet.common.streaming.dspy.configure")
    @patch("skill_fleet.common.streaming.dspy.asyncify")
    def test_create_async_module_custom_workers(self, mock_asyncify, mock_configure):
        """Test creating async module with custom workers."""
        mock_module = MagicMock()
        mock_result = MagicMock()
        mock_asyncify.return_value = mock_result

        result = create_async_module(mock_module, max_workers=8)

        assert result == mock_result
        mock_configure.assert_called_once_with(async_max_workers=8)
        mock_asyncify.assert_called_once_with(mock_module)


# ============================================================================
# Test stream_dspy_response
# ============================================================================


class TestStreamDspyResponse:
    """Tests for stream_dspy_response async generator."""

    @pytest.mark.asyncio
    async def test_stream_with_prediction(self):
        """Test streaming DSPy prediction."""
        # Mock streaming program that yields a prediction
        mock_prediction = StubPrediction({"answer": "42"})

        async def mock_stream(**kwargs):
            yield mock_prediction

        # Collect results
        results = []
        async for chunk in stream_dspy_response(mock_stream):
            results.append(chunk)

        assert len(results) == 2  # prediction + [DONE]
        assert results[0] == 'data: {"type": "prediction", "data": {"answer": "42"}}\n\n'
        assert results[1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_stream_with_reasoning(self):
        """Test streaming reasoning chunks."""
        # Mock streaming program that yields StreamResponse
        mock_chunk = StubStreamResponse("Thinking")

        async def mock_stream(**kwargs):
            yield mock_chunk

        # Collect results
        results = []
        async for chunk in stream_dspy_response(mock_stream):
            results.append(chunk)

        assert len(results) == 2  # reasoning + [DONE]
        assert results[0] == 'data: {"type": "reasoning", "chunk": "Thinking"}\n\n'
        assert results[1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_stream_with_status_message(self):
        """Test streaming status messages."""
        # Mock streaming program that yields StatusMessage
        mock_status = StubStatusMessage("Processing...")

        async def mock_stream(**kwargs):
            yield mock_status

        # Collect results
        results = []
        async for chunk in stream_dspy_response(mock_stream):
            results.append(chunk)

        assert len(results) == 2  # status + [DONE]
        assert results[0] == 'data: {"type": "status", "message": "Processing..."}\n\n'
        assert results[1] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_stream_with_mixed_chunks(self):
        """Test streaming mixed chunk types."""
        # Mock streaming program that yields different types
        mock_status = StubStatusMessage("Starting")
        mock_reasoning = StubStreamResponse("Thinking...")
        mock_prediction = StubPrediction({"result": "done"})

        async def mock_stream(**kwargs):
            yield mock_status
            yield mock_reasoning
            yield mock_prediction

        # Collect results
        results = []
        async for chunk in stream_dspy_response(mock_stream, param="value"):
            results.append(chunk)

        assert len(results) == 4  # 3 chunks + [DONE]
        assert '"type": "status"' in results[0]
        assert '"type": "reasoning"' in results[1]
        assert '"type": "prediction"' in results[2]
        assert results[3] == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_stream_passes_kwargs(self):
        """Test that kwargs are passed to streaming program."""

        async def mock_stream(**kwargs):
            # Verify kwargs passed through
            assert kwargs.get("question") == "test"
            assert kwargs.get("param2") == "value"
            return
            yield  # Make this a generator (unreachable but required for syntax)

        async for _ in stream_dspy_response(mock_stream, question="test", param2="value"):
            pass  # Just verify kwargs are passed


# ============================================================================
# Test process_stream_sync
# ============================================================================


class TestProcessStreamSync:
    """Tests for process_stream_sync generator."""

    def test_process_with_prediction(self):
        """Test processing stream with prediction."""
        # Mock streaming program that yields a prediction
        mock_prediction = StubPrediction({"result": "done"})

        def mock_stream(**kwargs):
            yield mock_prediction

        # Collect results
        results = list(process_stream_sync(mock_stream))

        assert len(results) == 1
        assert results[0]["type"] == "prediction"
        # Check that the content is a Prediction instance (avoiding __eq__ recursion)
        assert isinstance(results[0]["content"], dspy.Prediction)

    def test_process_with_reasoning(self):
        """Test processing stream with reasoning."""
        # Mock streaming program that yields StreamResponse
        mock_chunk = StubStreamResponse("thinking")

        def mock_stream(**kwargs):
            yield mock_chunk

        # Collect results
        results = list(process_stream_sync(mock_stream))

        assert len(results) == 1
        assert results[0]["type"] == "reasoning"
        assert results[0]["content"] == "thinking"

    def test_process_with_status_message(self):
        """Test processing stream with status message."""
        # Mock streaming program that yields StatusMessage
        mock_status = StubStatusMessage("Status")

        def mock_stream(**kwargs):
            yield mock_status

        # Collect results
        results = list(process_stream_sync(mock_stream))

        assert len(results) == 1
        assert results[0]["type"] == "status"
        assert results[0]["content"] == "Status"

    def test_process_with_mixed_chunks(self):
        """Test processing stream with mixed chunk types."""
        mock_status = StubStatusMessage("Starting")
        mock_reasoning = StubStreamResponse("Thinking...")
        mock_prediction = StubPrediction({"result": "done"})

        def mock_stream(**kwargs):
            yield mock_status
            yield mock_reasoning
            yield mock_prediction

        # Collect results
        results = list(process_stream_sync(mock_stream))

        assert len(results) == 3
        assert results[0]["type"] == "status"
        assert results[1]["type"] == "reasoning"
        assert results[2]["type"] == "prediction"

    def test_process_passes_kwargs(self):
        """Test that kwargs are passed to streaming program."""

        def mock_stream(**kwargs):
            assert kwargs.get("question") == "test"
            assert kwargs.get("param2") == "value"
            yield from ()

        list(process_stream_sync(mock_stream, question="test", param2="value"))


# ============================================================================
# Integration Tests (with mocked dspy)
# ============================================================================


class TestStreamingIntegration:
    """Integration tests with mocked DSPy components."""

    @patch("skill_fleet.common.streaming.dspy")
    def test_full_streaming_workflow(self, mock_dspy):
        """Test end-to-end streaming workflow."""
        # Setup mocks
        mock_module = MagicMock()
        mock_streamified = MagicMock()
        mock_dspy.streamify.return_value = mock_streamified

        # Create streaming module
        streaming = create_streaming_module(mock_module, async_mode=False)

        assert streaming == mock_streamified
        mock_dspy.streamify.assert_called_once()

    @patch("skill_fleet.common.streaming.dspy")
    def test_async_workflow(self, mock_dspy):
        """Test async workflow with dspy.asyncify."""
        mock_module = MagicMock()
        mock_asyncified = MagicMock()
        mock_dspy.asyncify.return_value = mock_asyncified

        # Create async module
        async_module = create_async_module(mock_module, max_workers=4)

        assert async_module == mock_asyncified
        mock_dspy.configure.assert_called_once_with(async_max_workers=4)
        mock_dspy.asyncify.assert_called_once_with(mock_module)
