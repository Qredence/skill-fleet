"""HTTP client for communicating with the Skill Fleet API."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SkillFleetClient:
    """Async HTTP client for Skill Fleet API."""

    def __init__(self, base_url: str = "http://localhost:8000", user_id: str | None = None):
        """
        Initialize the client.

        Args:
            base_url: API server base URL.
            user_id: Optional user ID sent as ``X-User-Id`` header for
                ownership verification on HITL and other endpoints.
        """
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        headers: dict[str, str] = {}
        if user_id:
            headers["X-User-Id"] = user_id
        # Increase timeout for long-running operations (5 minutes)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0, headers=headers)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def create_skill(self, task: str, user_id: str = "default") -> dict[str, Any]:
        """Call the skill creation endpoint (v1 API)."""
        try:
            response = await self.client.post(
                "/api/v1/skills/", json={"task_description": task, "user_id": user_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError as e:
            raise ValueError(
                "Failed to connect to the API server. "
                "Make sure the server is running at the configured URL."
            ) from e

    async def create_skill_streaming(
        self, task: str, user_id: str = "default", quality_threshold: float = 0.75
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Create a skill with streaming progress updates.

        Yields:
            Dict containing event type and data:
            - type='phase_start': New workflow phase started
            - type='progress': Progress update with message
            - type='reasoning': AI reasoning/thoughts
            - type='module_start': Module execution started
            - type='module_end': Module execution completed
            - type='hitl_required': Waiting for user input
            - type='completed': Workflow completed
            - type='error': Error occurred

        Example:
            async for event in client.create_skill_streaming("Build a React app"):
                if event['type'] == 'reasoning':
                    print(f"AI thinking: {event['data'].get('reasoning')}")
                elif event['type'] == 'progress':
                    print(f"Progress: {event['message']}")
        """
        request_data = {
            "task_description": task,
            "user_id": user_id,
            "enable_hitl": True,
            "quality_threshold": quality_threshold,
        }

        async with self.client.stream(
            "POST",
            "/api/v1/skills/stream",
            json=request_data,
            timeout=None,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    break

                try:
                    event = json.loads(data_str)
                    yield event
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse SSE data: {data_str}")

    async def get_hitl_prompt(self, job_id: str) -> dict[str, Any]:
        """Poll for a pending HITL prompt (v1 API)."""
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
        """Send a response to a HITL prompt (v1 API)."""
        response = await self.client.post(f"/api/v1/hitl/{job_id}/response", json=response_data)
        response.raise_for_status()
        return response.json()

    async def list_skills(self) -> list[dict[str, Any]]:
        """List all skills from the taxonomy (v1 API)."""
        response = await self.client.get("/api/v1/taxonomy/")
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("skills"), list):
            return payload["skills"]
        return []

    async def get_job(self, job_id: str) -> dict[str, Any]:
        """Fetch job status and any persisted artifacts/results (v1 API)."""
        response = await self.client.get(f"/api/v1/jobs/{job_id}")
        if response.status_code == 404:
            raise ValueError(f"Job {job_id} not found.")
        response.raise_for_status()
        return response.json()

    async def stream_job_events(self, job_id: str) -> AsyncIterator[dict[str, Any]]:
        """
        Stream events for an existing job via SSE.

        This connects to GET /api/v1/skills/{job_id}/stream and yields
        events as they occur. Use this instead of polling for real-time updates.

        Yields:
            Dict containing event type and data:
            - type='status': Current job status
            - type='phase_start/phase_end': Phase transitions
            - type='progress': Progress update
            - type='reasoning': AI reasoning/thoughts
            - type='hitl_required': Waiting for user input
            - type='complete': Workflow completed
            - type='error': Error occurred

        Example:
            async for event in client.stream_job_events(job_id):
                if event['type'] == 'hitl_required':
                    break  # Handle HITL interaction
                elif event['type'] == 'complete':
                    print("Done!")
        """
        try:
            async with self.client.stream(
                "GET",
                f"/api/v1/skills/{job_id}/stream",
                timeout=None,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        event = json.loads(data_str)
                        yield event
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data_str}")
        except httpx.RemoteProtocolError:
            # Server closed connection (expected after HITL pause or completion)
            pass
        except httpx.ReadTimeout:
            # Timeout waiting for events
            logger.debug(f"SSE stream timeout for job {job_id}")
            pass

    async def promote_draft(
        self,
        job_id: str,
        *,
        overwrite: bool = True,
        delete_draft: bool = False,
        force: bool = False,
    ) -> dict[str, Any]:
        """Promote a draft created by a job into the real taxonomy (v1 API)."""
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
