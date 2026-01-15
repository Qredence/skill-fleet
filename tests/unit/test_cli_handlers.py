"""Tests for CLI interaction handlers.

Following TDD principles, these tests were written BEFORE implementing
the handler modules. Each handler should be independently testable
and follow a consistent interface.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from skill_fleet.cli.hitl.handlers import (
    DeepUnderstandingHandler,
    TDDGreenHandler,
    TDDRedHandler,
    TDDRefactorHandler,
    get_handler,
)


class TestBaseHandlerInterface:
    """Tests for the base handler interface."""

    def test_get_handler_returns_none_for_unknown_type(self):
        """Test that get_handler returns None for unknown interaction types."""
        from rich.console import Console

        console = Console()
        handler = get_handler("unknown_type", console)

        assert handler is None

    def test_get_handler_returns_deep_understanding_handler(self):
        """Test that get_handler returns DeepUnderstandingHandler for deep_understanding."""
        from rich.console import Console

        console = Console()
        handler = get_handler("deep_understanding", console)

        assert isinstance(handler, DeepUnderstandingHandler)

    def test_get_handler_returns_tdd_red_handler(self):
        """Test that get_handler returns TDDRedHandler for tdd_red."""
        from rich.console import Console

        console = Console()
        handler = get_handler("tdd_red", console)

        assert isinstance(handler, TDDRedHandler)

    def test_get_handler_returns_tdd_green_handler(self):
        """Test that get_handler returns TDDGreenHandler for tdd_green."""
        from rich.console import Console

        console = Console()
        handler = get_handler("tdd_green", console)

        assert isinstance(handler, TDDGreenHandler)

    def test_get_handler_returns_tdd_refactor_handler(self):
        """Test that get_handler returns TDDRefactorHandler for tdd_refactor."""
        from rich.console import Console

        console = Console()
        handler = get_handler("tdd_refactor", console)

        assert isinstance(handler, TDDRefactorHandler)


class TestDeepUnderstandingHandler:
    """Tests for DeepUnderstandingHandler."""

    @pytest.mark.asyncio
    async def test_handle_displays_current_understanding(self):
        """Test that handler displays current understanding when provided."""
        from rich.console import Console

        console = Console()
        handler = DeepUnderstandingHandler(console)
        client = AsyncMock()

        prompt_data = {
            "question": "What problem are you solving?",
            "research_performed": ["Found similar skills"],
            "current_understanding": "User wants test detection",
            "readiness_score": 0.6,
        }

        # Mock the UI to avoid blocking on input
        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="skip")
        handler.ui.ask_text = AsyncMock(return_value="")

        await handler.handle("job_123", prompt_data, client)

        # Verify client was called with skip action
        client.post_hitl_response.assert_called_once()
        # Handlers call: client.post_hitl_response(job_id, payload)
        # call_args[0] is positional args tuple
        assert client.post_hitl_response.call_args[0][0] == "job_123"
        assert (
            client.post_hitl_response.call_args[0][1]["action"] == "proceed"
        )  # skip maps to proceed

    @pytest.mark.asyncio
    async def test_handle_with_proceed_action_collects_full_response(self):
        """Test that proceed action collects problem and goals."""
        from rich.console import Console

        console = Console()
        handler = DeepUnderstandingHandler(console)
        client = AsyncMock()

        prompt_data = {
            "question": "What problem are you solving?",
            "research_performed": [],
            "current_understanding": "",
            "readiness_score": 0.5,
        }

        # Mock UI to provide answers
        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="proceed")
        # Handler calls ask_text 3 times: answer, problem, goals
        handler.ui.ask_text = AsyncMock(
            side_effect=["Flaky tests", "Flaky tests", "reliability, speed"]
        )

        await handler.handle("job_456", prompt_data, client)

        # Verify full response was sent
        client.post_hitl_response.assert_called_once()
        payload = client.post_hitl_response.call_args[0][1]
        assert payload["answer"] == "Flaky tests"
        assert payload["problem"] == "Flaky tests"  # Second ask_text call
        assert payload["goals"] == ["reliability", "speed"]

    @pytest.mark.asyncio
    async def test_handle_with_cancel_action(self):
        """Test that cancel action sends cancel response."""
        from rich.console import Console

        console = Console()
        handler = DeepUnderstandingHandler(console)
        client = AsyncMock()

        prompt_data = {
            "question": "What problem?",
            "research_performed": [],
            "current_understanding": "",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="cancel")

        await handler.handle("job_789", prompt_data, client)

        client.post_hitl_response.assert_called_once_with("job_789", {"action": "cancel"})


class TestTDDRedHandler:
    """Tests for TDDRedHandler."""

    @pytest.mark.asyncio
    async def test_handle_displays_test_requirements(self):
        """Test that handler displays test requirements and acceptance criteria."""
        from rich.console import Console

        console = Console()
        handler = TDDRedHandler(console)
        client = AsyncMock()

        prompt_data = {
            "test_requirements": "Write tests for TDDWorkflowState serialization",
            "acceptance_criteria": [
                "phase field included",
                "checklist field included",
                "nested models serialize",
            ],
            "checklist_items": [
                {"text": "Write failing test", "done": False},
                {"text": "Verify test fails", "done": False},
            ],
            "rationalizations_identified": ["just this once"],
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="proceed")
        handler.ui.ask_text = AsyncMock(return_value="")

        await handler.handle("job_abc", prompt_data, client)

        client.post_hitl_response.assert_called_once()
        payload = client.post_hitl_response.call_args[0][1]
        assert payload["action"] == "proceed"

    @pytest.mark.asyncio
    async def test_handle_with_revise_action_collects_feedback(self):
        """Test that revise action collects feedback from user."""
        from rich.console import Console

        console = Console()
        handler = TDDRedHandler(console)
        client = AsyncMock()

        prompt_data = {
            "test_requirements": "Test something",
            "acceptance_criteria": [],
            "checklist_items": [],
            "rationalizations_identified": [],
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="revise")
        handler.ui.ask_text = AsyncMock(return_value="Need clearer requirements")

        await handler.handle("job_def", prompt_data, client)

        payload = client.post_hitl_response.call_args[0][1]
        assert payload["action"] == "revise"
        assert payload["feedback"] == "Need clearer requirements"


class TestTDDGreenHandler:
    """Tests for TDDGreenHandler."""

    @pytest.mark.asyncio
    async def test_handle_displays_failing_test_info(self):
        """Test that handler displays failing test and hint."""
        from rich.console import Console

        console = Console()
        handler = TDDGreenHandler(console)
        client = AsyncMock()

        prompt_data = {
            "failing_test": "test_tdd_workflow_state_serialization",
            "test_location": "tests/unit/test_api_jobs.py:62",
            "minimal_implementation_hint": "Create TDDWorkflowState with phase and checklist fields",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="proceed")

        await handler.handle("job_ghi", prompt_data, client)

        client.post_hitl_response.assert_called_once()
        assert client.post_hitl_response.call_args[0][1]["action"] == "proceed"

    @pytest.mark.asyncio
    async def test_handle_with_revise_collects_adjustment_feedback(self):
        """Test that revise action collects adjustment feedback."""
        from rich.console import Console

        console = Console()
        handler = TDDGreenHandler(console)
        client = AsyncMock()

        prompt_data = {
            "failing_test": "test_foo",
            "test_location": "test.py:1",
            "minimal_implementation_hint": "Implement foo",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="revise")
        handler.ui.ask_text = AsyncMock(return_value="Need better test setup")

        await handler.handle("job_jkl", prompt_data, client)

        payload = client.post_hitl_response.call_args[0][1]
        assert payload["action"] == "revise"
        assert payload["feedback"] == "Need better test setup"


class TestTDDRefactorHandler:
    """Tests for TDDRefactorHandler."""

    @pytest.mark.asyncio
    async def test_handle_displays_refactor_opportunities(self):
        """Test that handler displays refactor opportunities and code smells."""
        from rich.console import Console

        console = Console()
        handler = TDDRefactorHandler(console)
        client = AsyncMock()

        prompt_data = {
            "refactor_opportunities": [
                "Extract duplicate test setup into fixtures",
                "Combine similar assertions",
            ],
            "code_smells": ["test file too long"],
            "coverage_report": "92% coverage, all tests passing",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="proceed")

        await handler.handle("job_mno", prompt_data, client)

        client.post_hitl_response.assert_called_once()
        assert client.post_hitl_response.call_args[0][1]["action"] == "proceed"

    @pytest.mark.asyncio
    async def test_handle_with_skip_action(self):
        """Test that skip action sends proceed with skip indicated."""
        from rich.console import Console

        console = Console()
        handler = TDDRefactorHandler(console)
        client = AsyncMock()

        prompt_data = {
            "refactor_opportunities": [],
            "code_smells": [],
            "coverage_report": "95% coverage",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="skip")

        await handler.handle("job_pqr", prompt_data, client)

        # skip should map to proceed (user chose to skip refactoring)
        payload = client.post_hitl_response.call_args[0][1]
        assert payload["action"] == "proceed"

    @pytest.mark.asyncio
    async def test_handle_with_revise_collects_feedback(self):
        """Test that revise action collects what still needs work."""
        from rich.console import Console

        console = Console()
        handler = TDDRefactorHandler(console)
        client = AsyncMock()

        prompt_data = {
            "refactor_opportunities": ["Extract constants"],
            "code_smells": [],
            "coverage_report": "90%",
        }

        handler.ui = MagicMock()
        handler.ui.choose_one = AsyncMock(return_value="revise")
        handler.ui.ask_text = AsyncMock(return_value="Still needs more extraction")

        await handler.handle("job_stu", prompt_data, client)

        payload = client.post_hitl_response.call_args[0][1]
        assert payload["action"] == "revise"
        assert payload["feedback"] == "Still needs more extraction"
