from __future__ import annotations

import json


def test_chat_stream_endpoint_returns_sse(client, monkeypatch):
    from skill_fleet.api.v1 import conversational as conversational_api

    async def fake_stream_prediction(module, **kwargs):
        yield {"type": "response", "content": "hello"}

    monkeypatch.setattr(conversational_api, "stream_prediction", fake_stream_prediction)

    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "hello", "context": {}, "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data: " in response.text
    assert "[DONE]" in response.text


def test_chat_stream_endpoint_serializes_non_json_objects(client, monkeypatch):
    from skill_fleet.api.v1 import conversational as conversational_api

    class _NonSerializable:
        def __init__(self, value: str):
            self.value = value

    async def fake_stream_prediction(module, **kwargs):
        yield {
            "type": "prediction",
            "data": {"fields": {"reasoning": _NonSerializable("thinking"), "response": "ok"}},
        }

    monkeypatch.setattr(conversational_api, "stream_prediction", fake_stream_prediction)

    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "hello", "context": {}, "stream": True},
    )

    assert response.status_code == 200
    payload_lines = [
        line.removeprefix("data: ").strip()
        for line in response.text.splitlines()
        if line.startswith("data: ") and "[DONE]" not in line
    ]
    assert payload_lines
    first_event = json.loads(payload_lines[0])
    assert first_event["data"]["fields"]["reasoning"]["value"] == "thinking"
