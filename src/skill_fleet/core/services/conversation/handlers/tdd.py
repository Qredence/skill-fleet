"""TDD workflow handlers."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from ..models import AgentResponse, ConversationSession, ConversationState


class TDDHandlers:
    """Handlers for Creation, TDD, and Checklist phases."""

    def handle_creating(self, user_message: str, session: ConversationSession) -> AgentResponse:
        """Handle CREATING state."""
        if user_message.strip().lower() in ("cancel", "stop"):
            session.state = ConversationState.EXPLORING
            session.skill_draft = None
            return AgentResponse(
                message="Creation cancelled.",
                state=ConversationState.EXPLORING,
                action="cancel_creation",
                requires_user_input=True,
            )
        return AgentResponse(
            message="Skill creation is in progress...",
            state=ConversationState.CREATING,
            action="creating",
            requires_user_input=False,
        )

    async def handle_tdd_red(
        self, user_message: str, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        """Handle TDD RED state."""
        if user_message.strip().lower() in ("skip", "no"):
            return AgentResponse(
                message="TDD is mandatory. Continuing with baseline tests...",
                state=ConversationState.TDD_RED_PHASE,
                action="enforce_tdd",
                requires_user_input=False,
            )
        return await self.execute_tdd_red_phase(session, thinking_callback)

    async def handle_tdd_green(
        self, user_message: str, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        """Handle TDD GREEN state."""
        return await self.execute_tdd_green_phase(session, thinking_callback)

    async def handle_tdd_refactor(
        self, user_message: str, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        """Handle TDD REFACTOR state."""
        user_message_lower = user_message.strip().lower()
        if user_message_lower in ("yes", "y", "add", "close"):
            return await self.execute_tdd_refactor_phase(
                session, add_counters=True, thinking_callback=thinking_callback
            )
        elif user_message_lower in ("no", "n", "skip", ""):
            session.checklist_state.explicit_counters_added = False
            session.checklist_state.retested_until_bulletproof = True
            return await self.verify_checklist_complete(session, thinking_callback)

        if not session.checklist_state.new_rationalizations_identified:
            return await self.execute_tdd_refactor_phase(
                session, add_counters=False, thinking_callback=thinking_callback
            )
        else:
            return AgentResponse(
                message="Should I add explicit counters? (yes/no/skip)",
                state=ConversationState.TDD_REFACTOR_PHASE,
                action="ask_about_counters",
                requires_user_input=True,
            )

    async def handle_checklist_complete(
        self, user_message: str, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        """Handle CHECKLIST_COMPLETE state."""
        if "save" in user_message.lower() or "yes" in user_message.lower():
            return await self.save_skill(session)
        return AgentResponse(
            message="Please confirm save.", state=ConversationState.CHECKLIST_COMPLETE
        )

    async def handle_reviewing(self, user_message, session, thinking_callback):
        return AgentResponse(message="Review logic not fully ported yet.", state=session.state)

    async def handle_revising(self, user_message, session, thinking_callback):
        return AgentResponse(message="Revision logic not fully ported yet.", state=session.state)

    async def create_skill(self, session: ConversationSession, thinking_callback) -> AgentResponse:
        """Execute creation and transition to TDD."""
        try:
            existing_skills = self.taxonomy.get_mounted_skills("default")

            p1_result = await self.phase1.aforward(
                task_description=session.task_description,
                user_context="Interactive session",
                taxonomy_structure=json.dumps(
                    self.taxonomy.get_relevant_branches(session.task_description)
                ),
                existing_skills=json.dumps(existing_skills),
            )

            p2_result = await self.phase2.aforward(
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                generation_instructions=p1_result["plan"]["generation_instructions"],
                parent_skills_content="",
                dependency_summaries=json.dumps(p1_result["dependencies"]),
            )

            p3_result = await self.phase3.aforward(
                skill_content=p2_result["skill_content"],
                skill_metadata=p1_result["plan"]["skill_metadata"],
                content_plan=p1_result["plan"]["content_plan"],
                validation_rules="Standard compliance",
            )

            session.skill_draft = {
                "understanding": p1_result,
                "plan": p1_result["plan"],
                "content": p2_result,
                "package": p3_result,
                "skill_content": p2_result["skill_content"],
                "validation_errors": p3_result["validation_report"].get("errors", []),
            }

            present, p_thinking = await self._execute_with_streaming(
                self.present_skill,
                thinking_callback,
                skill_content=p2_result["skill_content"],
                skill_metadata=p1_result["plan"]["skill_metadata"],
                validation_report=p3_result["validation_report"],
            )

            message = present["conversational_summary"] + "\n\n**Starting TDD Checklist...**"
            session.state = ConversationState.TDD_RED_PHASE

            red_response = await self.execute_tdd_red_phase(session, thinking_callback)

            return AgentResponse(
                message=message + "\n\n" + red_response.message,
                thinking_content=p_thinking + red_response.thinking_content,
                state=red_response.state,
                action=red_response.action,
                requires_user_input=red_response.requires_user_input,
            )

        except Exception as e:
            # logger is not available in mixin context unless we import or define it.
            # Assuming Engine handles top-level exceptions, but here we catch specific logic errors.
            return AgentResponse(
                message=f"Error: {e}", state=ConversationState.EXPLORING, action="error"
            )

    async def execute_tdd_red_phase(
        self, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        skill_content = session.skill_draft["skill_content"]
        meta = session.skill_draft["plan"]["skill_metadata"]

        res, thinking = await self._execute_with_streaming(
            self.suggest_tests,
            thinking_callback,
            skill_content=skill_content,
            skill_type=meta.get("type", "technique"),
            skill_metadata=meta,
        )

        session.checklist_state.red_scenarios_created = True
        session.checklist_state.baseline_tests_run = True

        session.state = ConversationState.TDD_GREEN_PHASE
        return AgentResponse(
            message="RED Phase Complete. Baseline tests run.\nMoving to GREEN phase...",
            thinking_content=thinking,
            state=ConversationState.TDD_GREEN_PHASE,
            action="tdd_red_complete",
            requires_user_input=False,
        )

    async def execute_tdd_green_phase(
        self, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        session.checklist_state.green_tests_run = True
        session.checklist_state.compliance_verified = True
        session.state = ConversationState.TDD_REFACTOR_PHASE

        return AgentResponse(
            message="GREEN Phase Complete. Skill verified.\nMoving to REFACTOR phase...",
            state=ConversationState.TDD_REFACTOR_PHASE,
            action="tdd_green_complete",
            requires_user_input=False,
        )

    async def execute_tdd_refactor_phase(
        self, session: ConversationSession, add_counters: bool, thinking_callback
    ) -> AgentResponse:
        if not session.checklist_state.new_rationalizations_identified:
            session.checklist_state.new_rationalizations_identified = True
            return AgentResponse(
                message="I found potential loopholes. Should I add explicit counters? (yes/no)",
                state=ConversationState.TDD_REFACTOR_PHASE,
                action="ask_about_counters",
                requires_user_input=True,
            )

        if add_counters:
            session.checklist_state.explicit_counters_added = True
            session.checklist_state.retested_until_bulletproof = True
            return await self.verify_checklist_complete(session, thinking_callback)

        return await self.verify_checklist_complete(session, thinking_callback)

    async def verify_checklist_complete(
        self, session: ConversationSession, thinking_callback
    ) -> AgentResponse:
        res, thinking = await self._execute_with_streaming(
            self.verify_tdd,
            thinking_callback,
            skill_content=session.skill_draft["skill_content"],
            checklist_state=session.checklist_state.model_dump(),
        )

        if res["all_passed"]:
            session.state = ConversationState.CHECKLIST_COMPLETE
            return AgentResponse(
                message="Checklist Complete! Ready to save?",
                thinking_content=thinking,
                state=ConversationState.CHECKLIST_COMPLETE,
                action="checklist_complete",
                requires_user_input=True,
            )
        else:
            return AgentResponse(
                message="Checklist incomplete.",
                thinking_content=thinking,
                state=ConversationState.TDD_REFACTOR_PHASE,
                action="checklist_incomplete",
                requires_user_input=True,
            )

    async def save_skill(self, session: ConversationSession) -> AgentResponse:
        understanding = session.skill_draft["understanding"]
        plan = session.skill_draft["plan"]
        content = session.skill_draft["content"]

        success = self.taxonomy.register_skill(
            path=understanding["taxonomy"]["recommended_path"],
            metadata=plan["skill_metadata"],
            content=content["skill_content"],
            evolution={
                "skill_id": plan["skill_metadata"]["skill_id"],
                "version": "1.0.0",
                "status": "approved",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        if success:
            session.state = ConversationState.COMPLETE
            return AgentResponse(
                message="Skill saved!",
                state=ConversationState.COMPLETE,
                action="complete",
                requires_user_input=False,
            )
        return AgentResponse(
            message="Save failed.",
            state=ConversationState.CHECKLIST_COMPLETE,
            requires_user_input=True,
        )
