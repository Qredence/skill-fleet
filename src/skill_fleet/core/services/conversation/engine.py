"""Core conversation service orchestration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import dspy

from ....common.streaming import create_streaming_module
from ....taxonomy.manager import TaxonomyManager
from ...dspy.modules.conversation import (
    AssessReadinessModule,
    ConfirmUnderstandingModule,
    DeepUnderstandingModule,
    DetectMultiSkillModule,
    GenerateQuestionModule,
    InterpretIntentModule,
    PresentSkillModule,
    ProcessFeedbackModule,
    SuggestTestsModule,
    UnderstandingSummaryModule,
    VerifyTDDModule,
)
from ...dspy.modules.phase1_understanding import Phase1UnderstandingModule
from ...dspy.modules.phase2_generation import Phase2GenerationModule
from ...dspy.modules.phase3_validation import Phase3ValidationModule
from .handlers import ConversationHandlers
from .models import AgentResponse, ConversationSession, ConversationState

logger = logging.getLogger(__name__)


class ConversationService(ConversationHandlers):
    """
    Service for orchestrating conversational skill creation.

    Manages state, DSPy module execution, and business logic for the
    interactive skill creation workflow.
    """

    def __init__(
        self,
        taxonomy_manager: TaxonomyManager,
        skills_root: Path | None = None,
    ):
        """
        Initialize conversation service.

        Args:
            taxonomy_manager: Taxonomy management instance
            skills_root: Skills root directory (optional)
        """
        self.taxonomy = taxonomy_manager
        self.skills_root = skills_root

        # Initialize conversational modules
        self.interpret_intent = InterpretIntentModule()
        self.detect_multi_skill = DetectMultiSkillModule()
        self.generate_question = GenerateQuestionModule()
        self.assess_readiness = AssessReadinessModule()
        self.deep_understanding_module = DeepUnderstandingModule()
        self.understanding_summary = UnderstandingSummaryModule()
        self.confirm_understanding = ConfirmUnderstandingModule()
        self.present_skill = PresentSkillModule()
        self.process_feedback = ProcessFeedbackModule()
        self.suggest_tests = SuggestTestsModule()
        self.verify_tdd = VerifyTDDModule()

        # Initialize Phase modules for creation workflow
        self.phase1 = Phase1UnderstandingModule()
        self.phase2 = Phase2GenerationModule()
        self.phase3 = Phase3ValidationModule()

    async def _execute_with_streaming(
        self,
        module: dspy.Module,
        thinking_callback: Callable[[str], None] | None = None,
        **kwargs,
    ) -> tuple[dict[str, Any], str]:
        """
        Execute a DSPy module with async streaming support.

        Args:
            module: DSPy module to execute
            thinking_callback: Optional callback for streaming thinking chunks
            **kwargs: Arguments to pass to the module

        Returns:
            Tuple of (prediction result, thinking content string)
        """
        # Create streaming wrapper in async mode
        streaming_module = create_streaming_module(
            module,
            reasoning_field="reasoning",
            async_mode=True,
        )

        thinking_parts: list[str] = []
        prediction: Any = None

        async for chunk in streaming_module(**kwargs):
            if isinstance(chunk, dspy.streaming.StreamResponse):
                # Collect thinking tokens
                content = chunk.chunk
                thinking_parts.append(content)
                if thinking_callback:
                    thinking_callback(content)
            elif isinstance(chunk, dspy.streaming.StatusMessage):
                logger.debug(f"Status: {chunk.message}")
            elif isinstance(chunk, dspy.Prediction):
                prediction = chunk

        thinking_content = "".join(thinking_parts)

        # Handle different return types from DSPy modules
        if isinstance(prediction, dspy.Prediction):
            # If labels() is available (Prediction object), use it
            if hasattr(prediction, "labels"):
                try:
                    result = dict(prediction)
                except (ValueError, TypeError):
                    # Fallback if iteration fails
                    result = {
                        k: getattr(prediction, k)
                        for k in dir(prediction)
                        if not k.startswith("_") and k != "labels"
                    }
            else:
                result = {
                    k: getattr(prediction, k) for k in dir(prediction) if not k.startswith("_")
                }
        elif isinstance(prediction, dict):
            result = prediction
        elif prediction is None:
            result = {}
        else:
            result = {"value": prediction}

        return result, thinking_content

    async def respond(
        self,
        user_message: str,
        session: ConversationSession,
        thinking_callback: Callable[[str], None] | None = None,
    ) -> AgentResponse:
        """
        Generate conversational response to user message.

        Args:
            user_message: User's message
            session: Current conversation session
            thinking_callback: Optional callback for real-time thinking

        Returns:
            AgentResponse with message and state updates
        """
        try:
            # Handle empty/continue messages for automatic progression
            user_message_trimmed = user_message.strip().lower() if user_message else ""
            is_continue = user_message_trimmed in ("", "continue", "proceed", "next")

            # Don't add empty messages to history
            if user_message.strip():
                session.messages.append({"role": "user", "content": user_message})

            # Route based on current state
            if session.state == ConversationState.EXPLORING:
                response = await self.handle_exploring(user_message, session, thinking_callback)
            elif session.state == ConversationState.DEEP_UNDERSTANDING:
                response = await self.handle_deep_understanding(
                    user_message, session, thinking_callback
                )
            elif session.state == ConversationState.MULTI_SKILL_DETECTED:
                response = self.handle_multi_skill(user_message, session)
            elif session.state == ConversationState.CONFIRMING:
                response = await self.handle_confirmation(user_message, session, thinking_callback)
            elif session.state == ConversationState.CREATING:
                response = self.handle_creating(user_message, session)
            elif session.state == ConversationState.TDD_RED_PHASE:
                if is_continue:
                    response = await self.execute_tdd_red_phase(session, thinking_callback)
                else:
                    response = await self.handle_tdd_red(user_message, session, thinking_callback)
            elif session.state == ConversationState.TDD_GREEN_PHASE:
                if is_continue:
                    response = await self.execute_tdd_green_phase(session, thinking_callback)
                else:
                    response = await self.handle_tdd_green(user_message, session, thinking_callback)
            elif session.state == ConversationState.TDD_REFACTOR_PHASE:
                response = await self.handle_tdd_refactor(user_message, session, thinking_callback)
            elif session.state == ConversationState.REVIEWING:
                response = await self.handle_reviewing(user_message, session, thinking_callback)
            elif session.state == ConversationState.REVISING:
                response = await self.handle_revising(user_message, session, thinking_callback)
            elif session.state == ConversationState.CHECKLIST_COMPLETE:
                response = await self.handle_checklist_complete(
                    user_message, session, thinking_callback
                )
            else:
                response = AgentResponse(
                    message="I'm ready to help you create a skill. What would you like to create?",
                    state=ConversationState.EXPLORING,
                    action="greet",
                )

            # Add agent response to history
            if response.state is not None:
                session.state = response.state
            session.messages.append({"role": "assistant", "content": response.message})
            if response.thinking_content:
                session.messages.append({"role": "thinking", "content": response.thinking_content})

            return response

        except Exception as e:
            logger.exception("Error in conversation service")
            import traceback

            tb = traceback.format_exc()
            return AgentResponse(
                message=f"I encountered an error: {str(e)}\n\nTraceback:\n{tb}",
                state=session.state,
                action="error",
                requires_user_input=True,
            )
