from __future__ import annotations


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
