"""ReAct-based workflow agent service for interactive skill creation."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import dspy

from skill_fleet.api.schemas.skills import CreateSkillRequest
from skill_fleet.api.services.job_manager import get_job_manager
from skill_fleet.api.services.jobs import create_job, update_job
from skill_fleet.api.services.skill_service import SkillService
from skill_fleet.common.logging_utils import sanitize_for_log
from skill_fleet.dspy import dspy_context
from skill_fleet.taxonomy.discovery import ensure_all_skills_loaded
from skill_fleet.taxonomy.manager import TaxonomyManager

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"completed", "failed", "cancelled", "pending_review"}
HITL_STATUSES = {"pending_user_input", "pending_hitl", "pending_review"}


class ReActAgentSignature(dspy.Signature):
    """Signature used for non-workflow general chat responses."""

    message: str = dspy.InputField(desc="Latest user message")
    conversation_context: str = dspy.InputField(
        desc="Recent conversation turns and optional runtime context",
        default="",
    )
    response: str = dspy.OutputField(desc="Helpful assistant response")
    reasoning: dspy.Reasoning = dspy.OutputField(desc="Reasoning trace")
    suggested_actions: list[str] = dspy.OutputField(
        desc="Actionable next steps for the user",
        default=[],
    )


@dataclass
class SessionMessage:
    """Single in-memory conversation turn."""

    role: str
    text: str
    timestamp: datetime


@dataclass
class SessionWorkflowState:
    """Workflow lifecycle state tracked per chat session."""

    active_job_id: str | None = None
    current_phase: str | None = None
    awaiting_hitl: bool = False
    hitl_type: str | None = None
    job_status: str | None = None
    last_prompt_signature: str | None = None
    last_job_snapshot: dict[str, Any] = field(default_factory=dict)


class ReActAgentService:
    """Workflow-aware assistant using DSPy ReAct and internal service adapters."""

    def __init__(self, *, taxonomy_manager: TaxonomyManager, skill_service: SkillService):
        self._taxonomy_manager = taxonomy_manager
        self._skill_service = skill_service
        self._sessions: defaultdict[str, list[SessionMessage]] = defaultdict(list)
        self._workflow_sessions: defaultdict[str, SessionWorkflowState] = defaultdict(
            SessionWorkflowState
        )
        self._agent = dspy.ReAct(
            ReActAgentSignature,
            tools=[
                self._describe_skill_creation_workflow,
                self._list_available_skills,
            ],
        )

    def _describe_skill_creation_workflow(self) -> str:
        """Tool: explain the end-to-end skill workflow."""
        payload = {
            "workflow": "Understanding -> Generation -> Validation",
            "api_routes": {
                "create": "POST /api/v1/skills",
                "job_status": "GET /api/v1/jobs/{job_id}",
                "hitl_prompt": "GET /api/v1/hitl/{job_id}/prompt",
                "hitl_response": "POST /api/v1/hitl/{job_id}/response",
                "promote_draft": "POST /api/v1/drafts/{job_id}/promote",
            },
            "notes": [
                "Skill creation runs asynchronously and may suspend for HITL.",
                "This agent can orchestrate start/status/HITL/promote actions.",
            ],
        }
        return json.dumps(payload)

    def _list_available_skills(self, limit: int = 12) -> str:
        """Tool: return available skill IDs and names from taxonomy metadata."""
        try:
            safe_limit = max(int(limit), 1)
        except Exception:
            safe_limit = 12

        try:
            ensure_all_skills_loaded(
                self._taxonomy_manager.skills_root,
                self._taxonomy_manager.metadata_cache,
                self._taxonomy_manager._load_skill_dir_metadata,
            )
        except Exception as exc:  # pragma: no cover
            logger.debug("Skill discovery fallback: %s", exc)

        records = [
            {
                "skill_id": skill_id,
                "name": meta.name,
                "description": meta.description,
            }
            for skill_id, meta in list(self._taxonomy_manager.metadata_cache.items())[:safe_limit]
        ]
        return json.dumps({"skills": records, "total": len(records)})

    async def start_skill_creation(
        self,
        *,
        task_description: str,
        user_id: str,
        hitl_flags: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Adapter: start a skill creation job and run workflow in background."""
        flags = hitl_flags or {}
        job_id = await create_job(task_description=task_description, user_id=user_id)
        request = CreateSkillRequest(
            task_description=task_description,
            user_id=user_id,
            enable_hitl_confirm=bool(flags.get("enable_hitl_confirm", True)),
            enable_hitl_preview=bool(flags.get("enable_hitl_preview", True)),
            enable_hitl_review=bool(flags.get("enable_hitl_review", True)),
            enable_token_streaming=bool(flags.get("enable_token_streaming", False)),
            auto_save_draft_on_preview_confirm=bool(
                flags.get("auto_save_draft_on_preview_confirm", True)
            ),
        )

        async def run_workflow() -> None:
            try:
                result = await self._skill_service.create_skill(request, existing_job_id=job_id)
                if result.status in {"completed", "pending_review"}:
                    await update_job(
                        job_id,
                        {
                            "status": result.status,
                            "result": result,
                            "progress_percent": 100.0,
                            "progress_message": "Skill creation completed",
                        },
                    )
            except Exception as exc:
                logger.error("ReAct workflow execution failed for job=%s: %s", job_id, exc)
                await update_job(job_id, {"status": "failed", "error": str(exc)})

        asyncio.create_task(run_workflow())
        return await self.get_job_status(job_id=job_id)

    async def get_job_status(self, *, job_id: str) -> dict[str, Any]:
        """Adapter: inspect current job state."""
        manager = get_job_manager()
        job = await manager.get_job(job_id)
        if not job:
            return {"job_id": job_id, "found": False}

        phase = self._resolve_phase(
            current_phase=getattr(job, "current_phase", None),
            hitl_type=getattr(job, "hitl_type", None),
            status=getattr(job, "status", None),
        )
        return {
            "job_id": job.job_id,
            "found": True,
            "status": job.status,
            "phase": phase,
            "current_phase": getattr(job, "current_phase", None),
            "progress_message": getattr(job, "progress_message", None),
            "progress_percent": getattr(job, "progress_percent", None),
            "hitl_type": getattr(job, "hitl_type", None),
            "draft_path": getattr(job, "draft_path", None),
            "final_path": getattr(job, "final_path", None),
            "validation_passed": getattr(job, "validation_passed", None),
            "updated_at": job.updated_at.isoformat() if getattr(job, "updated_at", None) else None,
        }

    async def get_hitl_prompt(self, *, job_id: str, user_id: str) -> dict[str, Any]:
        """Adapter: retrieve current HITL prompt payload."""
        from skill_fleet.api.v1.hitl import get_prompt

        header_user = user_id if user_id != "default" else None
        try:
            manager = get_job_manager()
            prompt = await get_prompt(job_id=job_id, x_user_id=header_user, manager=manager)
            data = prompt.model_dump() if hasattr(prompt, "model_dump") else dict(prompt)
            return {"found": True, "prompt": data}
        except Exception:  # pragma: no cover
            logger.exception(
                "Failed to retrieve HITL prompt for job_id %s",
                sanitize_for_log(job_id),
            )
            return {
                "found": False,
                "error": "Failed to retrieve HITL prompt.",
                "job_id": job_id,
            }

    async def submit_hitl_response(
        self,
        *,
        job_id: str,
        payload: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        """Adapter: submit HITL response and return refreshed workflow state."""
        from skill_fleet.api.v1.hitl import post_response

        header_user = user_id if user_id != "default" else None
        manager = get_job_manager()
        result = await post_response(
            job_id=job_id,
            response=payload,
            skill_service=self._skill_service,
            x_user_id=header_user,
            manager=manager,
        )

        response_payload = (
            result.model_dump() if hasattr(result, "model_dump") else {"status": "ok"}
        )
        status_payload = await self.get_job_status(job_id=job_id)
        prompt_payload = await self.get_hitl_prompt(job_id=job_id, user_id=user_id)
        return {
            "response": response_payload,
            "status": status_payload,
            "prompt": prompt_payload.get("prompt"),
        }

    async def promote_draft(
        self,
        *,
        job_id: str,
        force: bool = False,
        delete_draft: bool = True,
    ) -> dict[str, Any]:
        """Adapter: promote draft to taxonomy."""
        from skill_fleet.api.v1.drafts import PromoteDraftRequest, promote_draft

        request = PromoteDraftRequest(
            overwrite=True,
            delete_draft=delete_draft,
            force=force,
        )
        response = await promote_draft(
            job_id=job_id,
            request=request,
            skills_root=self._skill_service.skills_root,
            taxonomy_manager=self._taxonomy_manager,
        )
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)

    def _append_turn(self, session_id: str, role: str, text: str) -> None:
        self._sessions[session_id].append(
            SessionMessage(role=role, text=text, timestamp=datetime.now(UTC))
        )
        if len(self._sessions[session_id]) > 24:
            self._sessions[session_id] = self._sessions[session_id][-24:]

    def _compose_context(
        self,
        session_id: str,
        runtime_context: dict[str, Any] | None,
        workflow_state: SessionWorkflowState,
    ) -> str:
        turns = self._sessions.get(session_id, [])[-10:]
        history = "\n".join(f"{turn.role}: {turn.text}" for turn in turns)
        workflow = {
            "active_job_id": workflow_state.active_job_id,
            "phase": workflow_state.current_phase,
            "awaiting_hitl": workflow_state.awaiting_hitl,
            "hitl_type": workflow_state.hitl_type,
            "job_status": workflow_state.job_status,
            "last_job_snapshot": workflow_state.last_job_snapshot,
        }
        context_blob = json.dumps(runtime_context or {}, ensure_ascii=False)
        workflow_blob = json.dumps(workflow, ensure_ascii=False)
        return (
            f"Recent conversation:\n{history}\n\n"
            f"Workflow state:\n{workflow_blob}\n\n"
            f"Runtime context:\n{context_blob}"
        )

    @staticmethod
    def _resolve_phase(
        *,
        current_phase: str | None,
        hitl_type: str | None,
        status: str | None,
    ) -> str | None:
        if isinstance(current_phase, str) and current_phase.strip():
            lower = current_phase.lower()
            if "understanding" in lower:
                return "understanding"
            if "generation" in lower:
                return "generation"
            if "validation" in lower:
                return "validation"
            return lower

        if hitl_type in {"clarify", "structure_fix", "confirm", "deep_understanding"}:
            return "understanding"
        if hitl_type in {"preview"}:
            return "generation"
        if hitl_type in {"validate"}:
            return "validation"

        if status in {"pending_review", "completed"}:
            return "validation"
        return None

    async def _refresh_workflow_state(
        self,
        *,
        session_state: SessionWorkflowState,
        user_id: str,
        machine_events: list[dict[str, Any]],
    ) -> None:
        if not session_state.active_job_id:
            return

        status_payload = await self.get_job_status(job_id=session_state.active_job_id)
        if not status_payload.get("found", False):
            session_state.active_job_id = None
            session_state.current_phase = None
            session_state.awaiting_hitl = False
            session_state.hitl_type = None
            session_state.job_status = None
            session_state.last_prompt_signature = None
            session_state.last_job_snapshot = {}
            return

        session_state.current_phase = status_payload.get("phase")
        session_state.hitl_type = status_payload.get("hitl_type")
        session_state.job_status = status_payload.get("status")
        session_state.awaiting_hitl = status_payload.get("status") in HITL_STATUSES
        session_state.last_job_snapshot = status_payload
        machine_events.append({"type": "workflow_status", "data": status_payload})

        if session_state.awaiting_hitl:
            prompt_payload = await self.get_hitl_prompt(
                job_id=session_state.active_job_id, user_id=user_id
            )
            prompt = prompt_payload.get("prompt")
            if isinstance(prompt, dict):
                signature = json.dumps(
                    {
                        "type": prompt.get("type"),
                        "summary": prompt.get("summary"),
                        "questions": prompt.get("questions"),
                        "highlights": prompt.get("highlights"),
                        "report": prompt.get("report"),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
                if signature != session_state.last_prompt_signature:
                    session_state.last_prompt_signature = signature
                    machine_events.append(
                        {
                            "type": "hitl_required",
                            "data": {
                                "job_id": session_state.active_job_id,
                                "hitl_type": session_state.hitl_type,
                                "prompt": prompt,
                            },
                        }
                    )
        else:
            session_state.last_prompt_signature = None

    def _resolve_workflow_intent(
        self,
        *,
        message: str,
        workflow_intent: str | None,
        ui_action: dict[str, Any] | None,
        session_state: SessionWorkflowState,
    ) -> str:
        if isinstance(ui_action, dict):
            action_type = str(ui_action.get("type") or "").strip().lower()
            mapped = {
                "start_skill_creation": "start_skill_creation",
                "check_status": "check_status",
                "submit_hitl": "submit_hitl",
                "submit_hitl_response": "submit_hitl",
                "promote_draft": "promote_draft",
            }.get(action_type)
            if mapped:
                return mapped

        if workflow_intent:
            return workflow_intent

        lower = message.lower().strip()
        if "promote" in lower and "draft" in lower:
            return "promote_draft"
        if any(token in lower for token in ("status", "progress", "where is job")):
            return "check_status"
        if session_state.awaiting_hitl:
            return "submit_hitl"
        if "create" in lower and "skill" in lower:
            return "start_skill_creation"
        return "chat"

    @staticmethod
    def _extract_task_description(message: str, ui_action: dict[str, Any] | None) -> str:
        if isinstance(ui_action, dict):
            payload = ui_action.get("payload")
            if isinstance(payload, dict):
                task = payload.get("task_description")
                if isinstance(task, str) and task.strip():
                    return task.strip()
        return message.strip()

    @staticmethod
    def _normalize_hitl_payload(
        *,
        message: str,
        hitl_type: str | None,
        ui_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if isinstance(ui_action, dict):
            payload = ui_action.get("payload")
            if isinstance(payload, dict) and payload:
                return payload

        lower = message.lower().strip()
        if hitl_type in {"confirm", "preview", "validate"}:
            if any(token in lower for token in ("cancel", "stop", "abort")):
                return {"action": "cancel"}
            if any(token in lower for token in ("revise", "refine", "change", "edit")):
                return {"action": "refine", "feedback": message}
            return {"action": "proceed", "feedback": message}

        if hitl_type == "structure_fix":
            if any(token in lower for token in ("accept", "use suggestion")):
                return {"accept_suggestions": True}
            return {"accept_suggestions": False, "description": message}

        if hitl_type in {"clarify", "deep_understanding"}:
            return {"answers": {"response": message}, "action": "proceed", "answer": message}

        return {"action": "proceed", "feedback": message}

    @staticmethod
    def _recommended_ui_actions(state: SessionWorkflowState) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        if not state.active_job_id:
            actions.append({"type": "start_skill_creation", "label": "Create skill"})
            return actions

        actions.append(
            {
                "type": "check_status",
                "label": "Refresh status",
                "payload": {"job_id": state.active_job_id},
            }
        )
        if state.awaiting_hitl:
            actions.extend(
                [
                    {
                        "type": "submit_hitl",
                        "label": "Proceed",
                        "payload": {"action": "proceed"},
                    },
                    {
                        "type": "submit_hitl",
                        "label": "Refine",
                        "payload": {"action": "refine"},
                    },
                    {
                        "type": "submit_hitl",
                        "label": "Cancel",
                        "payload": {"action": "cancel"},
                    },
                ]
            )
        if state.job_status in {"completed", "pending_review"}:
            actions.append(
                {
                    "type": "promote_draft",
                    "label": "Promote draft",
                    "payload": {"job_id": state.active_job_id},
                }
            )
        return actions

    async def send_message(
        self,
        *,
        message: str,
        session_id: str,
        user_id: str,
        context: dict[str, Any] | None,
        active_job_id: str | None = None,
        workflow_intent: str | None = None,
        ui_action: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process one agent turn and return structured workflow-aware response."""
        clean_message = sanitize_for_log(message)
        logger.info(
            "Processing ReAct agent message for session=%s user=%s msg=%s",
            sanitize_for_log(session_id),
            sanitize_for_log(user_id),
            clean_message,
        )

        self._append_turn(session_id, "user", message)
        workflow_state = self._workflow_sessions[session_id]
        if active_job_id:
            workflow_state.active_job_id = active_job_id

        machine_events: list[dict[str, Any]] = []
        await self._refresh_workflow_state(
            session_state=workflow_state, user_id=user_id, machine_events=machine_events
        )
        intent = self._resolve_workflow_intent(
            message=message,
            workflow_intent=workflow_intent,
            ui_action=ui_action,
            session_state=workflow_state,
        )

        response = ""
        reasoning: str | None = None
        suggested_actions: list[str] = []
        next_step: dict[str, Any] | None = None

        if intent == "start_skill_creation":
            task_description = self._extract_task_description(message, ui_action)
            if len(task_description) < 10:
                response = "Please provide a bit more detail so I can start the skill workflow."
                suggested_actions = ["Describe the skill goal and expected behavior."]
            else:
                start_payload = await self.start_skill_creation(
                    task_description=task_description,
                    user_id=user_id,
                    hitl_flags=(ui_action or {}).get("payload", {}) if ui_action else None,
                )
                workflow_state.active_job_id = str(start_payload.get("job_id"))
                await self._refresh_workflow_state(
                    session_state=workflow_state,
                    user_id=user_id,
                    machine_events=machine_events,
                )
                response = (
                    f"Started a new skill creation workflow. "
                    f"Job `{workflow_state.active_job_id}` is now running."
                )
                suggested_actions = [
                    "I can monitor phase progress and ask HITL questions when they appear.",
                    "You can also ask me to promote the draft when validation is done.",
                ]
                next_step = {"type": "check_status", "job_id": workflow_state.active_job_id}

        elif intent == "check_status":
            if not workflow_state.active_job_id:
                response = "No active workflow job is linked to this session yet."
                suggested_actions = ["Ask me to create a new skill to start a workflow."]
            else:
                await self._refresh_workflow_state(
                    session_state=workflow_state,
                    user_id=user_id,
                    machine_events=machine_events,
                )
                status = workflow_state.job_status or "unknown"
                phase = workflow_state.current_phase or "n/a"
                response = f"Workflow status is `{status}` (phase: `{phase}`)."
                if workflow_state.awaiting_hitl:
                    response += " I’m waiting for your HITL response to continue."
                elif status in TERMINAL_STATUSES:
                    response += " This run reached a terminal state."
                suggested_actions = ["Use the action buttons to continue."]
                next_step = {"type": "check_status", "job_id": workflow_state.active_job_id}

        elif intent == "submit_hitl":
            if not workflow_state.active_job_id:
                response = "There is no active job to submit HITL input for."
            else:
                payload = self._normalize_hitl_payload(
                    message=message,
                    hitl_type=workflow_state.hitl_type,
                    ui_action=ui_action,
                )
                submit_payload = await self.submit_hitl_response(
                    job_id=workflow_state.active_job_id,
                    payload=payload,
                    user_id=user_id,
                )
                machine_events.append(
                    {
                        "type": "hitl_submitted",
                        "data": {
                            "job_id": workflow_state.active_job_id,
                            "payload": payload,
                            "result": submit_payload.get("response"),
                        },
                    }
                )
                await self._refresh_workflow_state(
                    session_state=workflow_state,
                    user_id=user_id,
                    machine_events=machine_events,
                )
                response = "HITL response submitted. I’ll continue tracking the workflow."
                suggested_actions = ["Ask for status updates while phases continue."]
                next_step = {"type": "check_status", "job_id": workflow_state.active_job_id}

        elif intent == "promote_draft":
            target_job_id = workflow_state.active_job_id
            if isinstance(ui_action, dict):
                payload = ui_action.get("payload")
                if isinstance(payload, dict) and isinstance(payload.get("job_id"), str):
                    target_job_id = payload["job_id"]
            if not target_job_id:
                response = "I need an active job ID to promote a draft."
            else:
                result = await self.promote_draft(
                    job_id=target_job_id, force=True, delete_draft=True
                )
                machine_events.append(
                    {
                        "type": "workflow_complete",
                        "data": {
                            "job_id": target_job_id,
                            "status": "promoted",
                            "final_path": result.get("final_path"),
                        },
                    }
                )
                response = f"Draft promoted successfully to `{result.get('final_path', '')}`."
                suggested_actions = ["Start another skill workflow when ready."]

        else:
            conversation_context = self._compose_context(
                session_id=session_id,
                runtime_context=context,
                workflow_state=workflow_state,
            )
            with dspy_context():
                result = await self._agent.acall(
                    message=message,
                    conversation_context=conversation_context,
                )
            response = getattr(result, "response", "") or ""
            reasoning_value = getattr(result, "reasoning", None)
            reasoning = str(reasoning_value) if reasoning_value is not None else None
            raw_actions = getattr(result, "suggested_actions", [])
            if isinstance(raw_actions, list):
                suggested_actions = [str(item) for item in raw_actions]
            elif isinstance(raw_actions, str):
                suggested_actions = [raw_actions]

        self._append_turn(session_id, "assistant", response)

        if workflow_state.job_status in TERMINAL_STATUSES and workflow_state.active_job_id:
            machine_events.append(
                {
                    "type": "workflow_complete",
                    "data": {
                        "job_id": workflow_state.active_job_id,
                        "status": workflow_state.job_status,
                        "phase": workflow_state.current_phase,
                    },
                }
            )

        recommended_ui_actions = self._recommended_ui_actions(workflow_state)
        metadata = {
            "agent": "dspy-react",
            "tool_count": 2,
            "user_id": user_id,
            "events": machine_events,
            "active_job_id": workflow_state.active_job_id,
            "phase": workflow_state.current_phase,
            "awaiting_hitl": workflow_state.awaiting_hitl,
            "hitl_type": workflow_state.hitl_type,
            "job_status": workflow_state.job_status,
        }

        return {
            "response": response,
            "reasoning": reasoning,
            "suggested_actions": suggested_actions,
            "session_id": session_id,
            "active_job_id": workflow_state.active_job_id,
            "phase": workflow_state.current_phase,
            "awaiting_hitl": workflow_state.awaiting_hitl,
            "hitl_type": workflow_state.hitl_type,
            "job_status": workflow_state.job_status,
            "next_step": next_step,
            "recommended_ui_actions": recommended_ui_actions,
            "metadata": metadata,
        }

    async def stream_message(
        self,
        *,
        message: str,
        session_id: str,
        user_id: str,
        context: dict[str, Any] | None,
        active_job_id: str | None = None,
        workflow_intent: str | None = None,
        ui_action: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream response as SSE-compatible events with workflow metadata."""
        payload = await self.send_message(
            message=message,
            session_id=session_id,
            user_id=user_id,
            context=context,
            active_job_id=active_job_id,
            workflow_intent=workflow_intent,
            ui_action=ui_action,
        )

        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict):
            for event in metadata.get("events", []):
                if isinstance(event, dict) and isinstance(event.get("type"), str):
                    yield event

        response_text = payload.get("response", "")
        if isinstance(response_text, str):
            for token in response_text.split(" "):
                if not token:
                    continue
                yield {
                    "type": "stream",
                    "data": {
                        "field": "response",
                        "content": f"{token} ",
                    },
                }

        yield {
            "type": "agent_message",
            "data": {
                "response": payload.get("response", ""),
                "suggested_actions": payload.get("suggested_actions", []),
                "recommended_ui_actions": payload.get("recommended_ui_actions", []),
                "next_step": payload.get("next_step"),
            },
        }

        yield {
            "type": "prediction",
            "data": {
                "fields": {
                    "response": payload.get("response", ""),
                    "reasoning": payload.get("reasoning"),
                    "suggested_actions": payload.get("suggested_actions", []),
                    "active_job_id": payload.get("active_job_id"),
                    "phase": payload.get("phase"),
                    "awaiting_hitl": payload.get("awaiting_hitl"),
                    "hitl_type": payload.get("hitl_type"),
                    "job_status": payload.get("job_status"),
                    "next_step": payload.get("next_step"),
                    "recommended_ui_actions": payload.get("recommended_ui_actions", []),
                }
            },
        }
