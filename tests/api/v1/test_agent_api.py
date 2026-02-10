from __future__ import annotations


class _FakeAgentService:
    async def send_message(self, **kwargs):
        return {
            "response": "hello from agent",
            "reasoning": "because",
            "suggested_actions": ["create skill"],
            "session_id": kwargs.get("session_id", "default"),
            "active_job_id": "job-1",
            "phase": "understanding",
            "awaiting_hitl": True,
            "hitl_type": "clarify",
            "job_status": "pending_hitl",
            "next_step": {"type": "submit_hitl"},
            "recommended_ui_actions": [{"type": "submit_hitl", "payload": {"action": "proceed"}}],
            "metadata": {"agent": "fake"},
        }

    async def stream_message(self, **kwargs):
        yield {"type": "workflow_status", "data": {"job_id": "job-1", "status": "pending_hitl"}}
        yield {"type": "stream", "data": {"field": "response", "content": "hello "}}
        yield {"type": "hitl_required", "data": {"job_id": "job-1", "hitl_type": "clarify"}}
        yield {
            "type": "prediction",
            "data": {"fields": {"response": "hello from agent"}},
        }


def test_agent_message_endpoint(client, monkeypatch):
    from skill_fleet.api.v1 import agent as agent_api

    monkeypatch.setattr(agent_api, "get_react_agent_service", lambda: _FakeAgentService())

    response = client.post(
        "/api/v1/agent/message",
        json={"message": "hi", "user_id": "default", "session_id": "s-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == "hello from agent"
    assert payload["session_id"] == "s-1"
    assert payload["active_job_id"] == "job-1"
    assert payload["awaiting_hitl"] is True
    assert payload["hitl_type"] == "clarify"


def test_agent_stream_endpoint_returns_sse(client, monkeypatch):
    from skill_fleet.api.v1 import agent as agent_api

    monkeypatch.setattr(agent_api, "get_react_agent_service", lambda: _FakeAgentService())

    response = client.post(
        "/api/v1/agent/stream",
        json={"message": "hi", "context": {}, "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "data: " in response.text
    assert "workflow_status" in response.text
    assert "hitl_required" in response.text
    assert "[DONE]" in response.text
