"""ReAct agent routes for workflow-aware conversational API."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from skill_fleet.api.schemas.agent import AgentMessageRequest, AgentMessageResponse
from skill_fleet.api.services.react_agent_service import ReActAgentService

logger = logging.getLogger(__name__)

router = APIRouter()


# Keep a process-local singleton to preserve in-memory session continuity.
_AGENT_SERVICE: ReActAgentService | None = None


def get_react_agent_service() -> ReActAgentService:
    """Return a singleton ReAct agent service instance."""
    global _AGENT_SERVICE
    if _AGENT_SERVICE is None:
        from skill_fleet.api.dependencies import get_drafts_root, get_skills_root
        from skill_fleet.api.services.skill_service import SkillService
        from skill_fleet.taxonomy.manager import TaxonomyManager

        skills_root = get_skills_root()
        drafts_root = get_drafts_root(skills_root)
        _AGENT_SERVICE = ReActAgentService(
            taxonomy_manager=TaxonomyManager(skills_root),
            skill_service=SkillService(skills_root=skills_root, drafts_root=drafts_root),
        )
    return _AGENT_SERVICE


@router.post("/message", response_model=AgentMessageResponse)
async def send_agent_message(request: AgentMessageRequest) -> AgentMessageResponse:
    """Handle non-streaming ReAct agent requests."""
    service = get_react_agent_service()
    session_id = request.session_id or "default"

    try:
        ui_action_payload = request.ui_action.model_dump() if request.ui_action else None
        payload = await service.send_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            context=request.context,
            active_job_id=request.active_job_id,
            workflow_intent=request.workflow_intent,
            ui_action=ui_action_payload,
        )
        return AgentMessageResponse(**payload)
    except Exception as exc:
        logger.error("ReAct /message failure", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/stream")
async def stream_agent_message(request: AgentMessageRequest) -> StreamingResponse:
    """Handle streaming ReAct agent requests (SSE)."""
    service = get_react_agent_service()
    session_id = request.session_id or "default"

    async def event_generator() -> AsyncIterator[str]:
        ui_action_payload = request.ui_action.model_dump() if request.ui_action else None
        async for event in service.stream_message(
            message=request.message,
            session_id=session_id,
            user_id=request.user_id,
            context=request.context,
            active_job_id=request.active_job_id,
            workflow_intent=request.workflow_intent,
            ui_action=ui_action_payload,
        ):
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
