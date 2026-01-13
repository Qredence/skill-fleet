import io

import pytest
from rich.console import Console

from skill_fleet.cli.hitl.runner import run_hitl_job
from skill_fleet.cli.ui.prompts import PromptUI


class FakeClient:
    def __init__(self, prompts: list[dict]):
        self._prompts = list(prompts)
        self._idx = 0
        self.posted: list[dict] = []

    async def get_hitl_prompt(self, _job_id: str) -> dict:
        prompt = self._prompts[self._idx]
        self._idx += 1
        return prompt

    async def post_hitl_response(self, _job_id: str, response_data: dict) -> dict:
        self.posted.append(response_data)
        return {"status": "accepted"}


class FakeUI(PromptUI):
    def __init__(self, *, text_answers: list[str] | None = None, choice_answer: str = "proceed"):
        self._text_answers = list(text_answers or [])
        self._choice_answer = choice_answer

    async def ask_text(self, _prompt: str, *, default: str = "") -> str:
        if self._text_answers:
            return self._text_answers.pop(0)
        return default

    async def choose_one(self, _prompt: str, _choices, *, default_id: str | None = None) -> str:
        return self._choice_answer or (default_id or "")

    async def choose_many(self, _prompt: str, _choices, *, default_ids=None):
        return list(default_ids or [])


@pytest.mark.asyncio
async def test_run_hitl_job_clarify_multiple_questions_one_at_a_time_combined_response():
    # Arrange
    prompts = [
        {
            "status": "pending_hitl",
            "type": "clarify",
            "questions": [
                {"question": "What is the target audience?"},
                {"question": "Any constraints?"},
            ],
            "rationale": "Need to tailor the skill.",
        },
        {"status": "completed"},
    ]
    client = FakeClient(prompts)
    ui = FakeUI(text_answers=["Intermediate", "No external deps"])
    console = Console(file=io.StringIO(), force_terminal=False)

    # Act
    final = await run_hitl_job(
        console=console, client=client, job_id="job-1", ui=ui, poll_interval=0
    )

    # Assert
    assert final["status"] == "completed"
    assert len(client.posted) == 1
    payload = client.posted[0]
    assert payload["answers"]["response"].count("Q1:") == 1
    assert "Intermediate" in payload["answers"]["response"]
    assert "No external deps" in payload["answers"]["response"]


@pytest.mark.asyncio
async def test_run_hitl_job_confirm_uses_choice_ui():
    # Arrange
    prompts = [
        {
            "status": "pending_hitl",
            "type": "confirm",
            "summary": "Summary...",
            "path": "technical_skills/python",
        },
        {"status": "completed"},
    ]
    client = FakeClient(prompts)
    ui = FakeUI(choice_answer="cancel")
    console = Console(file=io.StringIO(), force_terminal=False)

    # Act
    final = await run_hitl_job(
        console=console, client=client, job_id="job-2", ui=ui, poll_interval=0
    )

    # Assert
    assert final["status"] == "completed"
    assert client.posted == [{"action": "cancel"}]


@pytest.mark.asyncio
async def test_run_hitl_job_clarify_splits_numbered_markdown_string():
    # Arrange
    prompts = [
        {
            "status": "pending_hitl",
            "type": "clarify",
            "questions": """1. **First:** One?\n2. **Second:** Two?\n3. **Third:** Three?""",
        },
        {"status": "completed"},
    ]
    client = FakeClient(prompts)
    ui = FakeUI(text_answers=["A1", "A2", "A3"])
    console = Console(file=io.StringIO(), force_terminal=False)

    # Act
    final = await run_hitl_job(
        console=console, client=client, job_id="job-3", ui=ui, poll_interval=0
    )

    # Assert
    assert final["status"] == "completed"
    assert len(client.posted) == 1
    combined = client.posted[0]["answers"]["response"]
    assert "First" in combined
    assert "Second" in combined
    assert "Third" in combined
    assert "A1" in combined
    assert "A2" in combined
    assert "A3" in combined
