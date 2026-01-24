"""HTTP client for communicating with the Skill Fleet API."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SkillFleetClient:
    """Async HTTP client for Skill Fleet API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client."""
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def create_skill(self, task: str, user_id: str = "default") -> dict[str, Any]:
        """Call the skill creation endpoint."""
        response = await self.client.post(
            "/api/v1/skills/", json={"task_description": task, "user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

    async def get_hitl_prompt(self, job_id: str) -> dict[str, Any]:
        """Poll for a pending HITL prompt."""
        response = await self.client.get(f"/api/v1/hitl/{job_id}/prompt")
        if response.status_code == 404:
            raise ValueError(
                f"Job {job_id} not found. The server may have restarted and lost the job state."
            )
        response.raise_for_status()
        return response.json()

    async def post_hitl_response(
        self, job_id: str, response_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a response to a HITL prompt."""
        response = await self.client.post(f"/api/v1/hitl/{job_id}/response", json=response_data)
        response.raise_for_status()
        return response.json()

    async def list_skills(self) -> list[dict[str, Any]]:
        """List all skills from the taxonomy."""
        response = await self.client.get("/api/v1/taxonomy/")
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("skills"), list):
            return payload["skills"]
        return []

    async def get_job(self, job_id: str) -> dict[str, Any]:
        """Fetch job status and any persisted artifacts/results."""
        response = await self.client.get(f"/api/v1/jobs/{job_id}")
        if response.status_code == 404:
            raise ValueError(f"Job {job_id} not found.")
        response.raise_for_status()
        return response.json()

    async def promote_draft(
        self,
        job_id: str,
        *,
        overwrite: bool = True,
        delete_draft: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Promote a draft created by a job into the real taxonomy."""
        response = await self.client.post(
            f"/api/v1/drafts/{job_id}/promote",
            json={"overwrite": overwrite, "delete_draft": delete_draft, "force": force},
        )
        response.raise_for_status()
        return response.json()

    async def stream_chat(
        self, message: str, session_id: str | None = None, context: dict[str, Any] | None = None
    ):
        """
        Stream chat events from the API.

        Yields:
            Dict containing event 'type' and 'data' (parsed JSON).
        """
        import json

        async with self.client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"message": message, "session_id": session_id, "context": context},
            timeout=None,
        ) as response:
            response.raise_for_status()

            # Simple SSE parser
            current_event_type = "message"

            async for line in response.aiter_lines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith("event: "):
                    current_event_type = line[7:].strip()
                elif line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                        yield {"type": current_event_type, "data": data}
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data_str}")
