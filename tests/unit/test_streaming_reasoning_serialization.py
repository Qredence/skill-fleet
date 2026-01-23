import json

import dspy
import pytest
from pydantic import BaseModel

from skill_fleet.common.streaming import StubPrediction, stream_dspy_response


@pytest.mark.asyncio
async def test_stream_serializes_reasoning_labels() -> None:
    async def mock_stream(**kwargs):
        yield StubPrediction({"answer": "42", "reasoning": dspy.Reasoning(content="why")})

    results = []
    async for chunk in stream_dspy_response(mock_stream):
        results.append(chunk)

    assert len(results) == 2

    payload = json.loads(results[0].removeprefix("data: ").strip())
    assert payload["type"] == "prediction"
    assert payload["data"]["answer"] == "42"
    assert payload["data"]["reasoning"] == "why"


@pytest.mark.asyncio
async def test_stream_serializes_nested_reasoning_labels() -> None:
    async def mock_stream(**kwargs):
        yield StubPrediction(
            {
                "nested": [
                    dspy.Reasoning(content="first"),
                    {"inner": (dspy.Reasoning(content="second"),)},
                ]
            }
        )

    results = []
    async for chunk in stream_dspy_response(mock_stream):
        results.append(chunk)

    payload = json.loads(results[0].removeprefix("data: ").strip())
    assert payload["data"]["nested"][0] == "first"
    assert payload["data"]["nested"][1]["inner"][0] == "second"


@pytest.mark.asyncio
async def test_stream_serializes_model_dump_reasoning() -> None:
    class Payload(BaseModel):
        reasoning: dspy.Reasoning
        items: list[str]

    async def mock_stream(**kwargs):
        yield StubPrediction(
            {"payload": Payload(reasoning=dspy.Reasoning(content="why"), items=["a"])}
        )

    results = []
    async for chunk in stream_dspy_response(mock_stream):
        results.append(chunk)

    payload = json.loads(results[0].removeprefix("data: ").strip())
    assert payload["data"]["payload"]["reasoning"] == "why"
    assert payload["data"]["payload"]["items"] == ["a"]


@pytest.mark.asyncio
async def test_stream_serializes_cycles_as_placeholder() -> None:
    async def mock_stream(**kwargs):
        data: dict[str, object] = {}
        data["self"] = data
        yield StubPrediction({"cycle": data})

    results = []
    async for chunk in stream_dspy_response(mock_stream):
        results.append(chunk)

    payload = json.loads(results[0].removeprefix("data: ").strip())
    assert payload["data"]["cycle"]["self"] == "<cycle>"
