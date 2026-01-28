"""
Conversational Interface Workflow Orchestrator.

Orchestrates the multi-turn conversational workflow for skill creation.
This manages the complete conversation lifecycle from initial intent through
skill creation and refinement.

This provides a clean interface for conversational interactions that both
API and CLI can use.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from skill_fleet.infrastructure.tracing.mlflow import (
    end_mlflow_run,
    log_parameter,
    log_phase_metrics,
    setup_mlflow_experiment,
)

from .....common.async_utils import run_async
from ..conversation import (
    AssessReadinessModule,
    ConfirmUnderstandingModule,
    DeepUnderstandingModule,
    DetectMultiSkillModule,
    EnhanceSkillModule,
    GenerateQuestionModule,
    InterpretIntentModule,
    PresentSkillModule,
    ProcessFeedbackModule,
    SuggestTestsModule,
    UnderstandingSummaryModule,
    VerifyTDDModule,
)

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """
    States in the conversation workflow.

    These must match the database enum conversation_state_enum in
    migrations/003_add_conversation_sessions.sql
    """

    EXPLORING = "EXPLORING"  # Understanding user intent, asking clarifying questions
    DEEP_UNDERSTANDING = "DEEP_UNDERSTANDING"  # Asking WHY questions, researching context
    MULTI_SKILL_DETECTED = "MULTI_SKILL_DETECTED"  # Multiple skills needed, presenting breakdown
    CONFIRMING = "CONFIRMING"  # Presenting confirmation summary before creation
    READY = "READY"  # User confirmed, ready to create skill
    CREATING = "CREATING"  # Executing skill creation workflow
    TDD_RED_PHASE = "TDD_RED_PHASE"  # Running baseline tests without skill
    TDD_GREEN_PHASE = "TDD_GREEN_PHASE"  # Verifying skill works with tests
    TDD_REFACTOR_PHASE = "TDD_REFACTOR_PHASE"  # Closing loopholes, re-testing
    REVIEWING = "REVIEWING"  # Presenting skill for user feedback
    REVISING = "REVISING"  # Processing feedback and regenerating
    CHECKLIST_COMPLETE = "CHECKLIST_COMPLETE"  # TDD checklist fully complete
    COMPLETE = "COMPLETE"  # Skill approved, saved, ready for next


class IntentType(Enum):
    """Types of user intents."""

    CREATE_SKILL = "create_skill"
    CLARIFY = "clarify"
    REFINE = "refine"
    MULTI_SKILL = "multi_skill"
    UNKNOWN = "unknown"


@dataclass
class ConversationMessage:
    """A message in the conversation."""

    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


@dataclass
class ConversationContext:
    """Context for the conversation."""

    conversation_id: str
    state: ConversationState = ConversationState.EXPLORING
    messages: list[ConversationMessage] = field(default_factory=list)
    collected_examples: list[dict] = field(default_factory=list)
    current_understanding: str = ""
    task_description: str = ""
    user_confirmations: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "messages": [m.to_dict() for m in self.messages],
            "collected_examples": self.collected_examples,
            "current_understanding": self.current_understanding,
            "task_description": self.task_description,
            "user_confirmations": self.user_confirmations,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class ConversationalOrchestrator:
    """
    Orchestrator for the Conversational Interface workflow.

    This orchestrator manages multi-turn conversations for skill creation,
    including intent interpretation, clarification, understanding, feedback
    collection, and refinement.

    Example:
        orchestrator = ConversationalOrchestrator()
        context = await orchestrator.initialize_conversation()
        intent = await orchestrator.interpret_intent(user_message, context)

    """

    def __init__(self, task_lms: dict[str, dspy.LM] | None = None):
        """Initialize the orchestrator."""
        self.task_lms = task_lms or {}

        # Initialize conversation modules
        self.interpret_intent_module = InterpretIntentModule()
        self.detect_multi_skill_module = DetectMultiSkillModule()
        self.generate_question_module = GenerateQuestionModule()
        self.deep_understanding_module = DeepUnderstandingModule()
        self.understanding_summary_module = UnderstandingSummaryModule()
        self.confirm_understanding_module = ConfirmUnderstandingModule()
        self.assess_readiness_module = AssessReadinessModule()
        self.present_skill_module = PresentSkillModule()
        self.process_feedback_module = ProcessFeedbackModule()
        self.suggest_tests_module = SuggestTestsModule()
        self.verify_tdd_module = VerifyTDDModule()
        self.enhance_skill_module = EnhanceSkillModule()

    def _create_conversation_id(self) -> str:
        """Create a unique conversation ID."""
        import uuid

        return str(uuid.uuid4())[:12]

    async def initialize_conversation(
        self,
        initial_message: str = "",
        metadata: dict[str, Any] | None = None,
        enable_mlflow: bool = True,
    ) -> ConversationContext:
        """
        Initialize a new conversation context.

        Args:
            initial_message: Optional initial user message
            metadata: Optional metadata for the conversation
            enable_mlflow: Whether to track with MLflow

        Returns:
            New conversation context

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversational-interface")
            if initial_message:
                log_parameter("initial_message_length", len(initial_message))

        try:
            context = ConversationContext(
                conversation_id=self._create_conversation_id(),
                state=ConversationState.EXPLORING,
                metadata=metadata or {},
            )

            if initial_message:
                context.messages.append(
                    ConversationMessage(
                        role="user",
                        content=initial_message,
                    )
                )
                context.task_description = initial_message

            if enable_mlflow:
                log_phase_metrics(
                    "conversation_init",
                    {
                        "conversation_id": context.conversation_id,
                    },
                )

            return context

        except Exception as e:
            logger.exception(f"Error initializing conversation: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def interpret_intent(
        self,
        user_message: str,
        context: ConversationContext,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Interpret user intent from their message.

        Args:
            user_message: User's message
            context: Current conversation context
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with intent_type, extracted_task, confidence

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversational-interpret-intent")

        try:
            # Add user message to context
            context.messages.append(
                ConversationMessage(
                    role="user",
                    content=user_message,
                )
            )

            history_str = str([m.to_dict() for m in context.messages])

            result = await self.interpret_intent_module.acall(
                user_message=user_message,
                conversation_history=history_str,
                current_state=context.state.value,
            )

            # Update context state based on intent
            intent_type = result.get("intent_type", "unknown")
            if intent_type == "create_skill":
                context.state = ConversationState.EXPLORING
            elif intent_type == "refine":
                context.state = ConversationState.REVIEWING

            if enable_mlflow:
                log_phase_metrics(
                    "interpret_intent",
                    {
                        "intent_type": intent_type,
                        "confidence": result.get("confidence", 0.0),
                    },
                )

            return {
                "intent_type": intent_type,
                "extracted_task": result.get("extracted_task", user_message),
                "confidence": result.get("confidence", 0.5),
                "updated_state": context.state.value,
            }

        except Exception as e:
            logger.exception(f"Error interpreting intent: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def generate_clarifying_question(
        self,
        context: ConversationContext,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a clarifying question for the user.

        Args:
            context: Current conversation context
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with question and options

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversatorial-clarify")

        try:
            previous_questions = [
                m.metadata.get("question", "")
                for m in context.messages
                if m.metadata.get("type") == "clarifying_question"
            ]

            result = await self.generate_question_module.acall(
                task_description=context.task_description,
                collected_examples=context.collected_examples,
                conversation_context=str([m.to_dict() for m in context.messages[-10:]]),
                previous_questions=previous_questions,
            )

            question = result.get("question", "")
            options = result.get("question_options", [])

            # Add to context as assistant message
            context.messages.append(
                ConversationMessage(
                    role="assistant",
                    content=question,
                    metadata={
                        "type": "clarifying_question",
                        "question": question,
                        "options": options,
                    },
                )
            )

            if enable_mlflow:
                log_phase_metrics(
                    "clarifying_question",
                    {
                        "has_options": len(options) > 0,
                    },
                )

            return {
                "question": question,
                "question_options": options,
                "reasoning": result.get("reasoning", ""),
            }

        except Exception as e:
            logger.exception(f"Error generating clarifying question: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def deep_understanding(
        self,
        context: ConversationContext,
        research_findings: dict[str, Any] | None = None,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Perform deep understanding of user requirements.

        Args:
            context: Current conversation context
            research_findings: Optional research findings
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with enhanced understanding

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversatorial-deep-understanding")

        try:
            context.state = ConversationState.DEEP_UNDERSTANDING

            previous_questions = [
                m.metadata.get("question", "")
                for m in context.messages
                if m.metadata.get("type") == "clarifying_question"
            ]

            result = await self.deep_understanding_module.acall(
                initial_task=context.task_description,
                conversation_history=str([m.to_dict() for m in context.messages]),
                research_findings=str(research_findings or {}),
                current_understanding=context.current_understanding,
                previous_questions=previous_questions,
                questions_asked_count=len(previous_questions),
            )

            # Update understanding
            context.current_understanding = result.get("enhanced_understanding", "")

            if enable_mlflow:
                log_phase_metrics(
                    "deep_understanding",
                    {
                        "questions_asked": len(previous_questions),
                        "understanding_quality": result.get("understanding_quality", 0.0),
                    },
                )

            return {
                "enhanced_understanding": context.current_understanding,
                "understanding_quality": result.get("understanding_quality", 0.0),
                "sufficient": result.get("sufficient", False),
                "additional_queries": result.get("additional_queries_needed", []),
            }

        except Exception as e:
            logger.exception(f"Error in deep understanding: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def confirm_understanding(
        self,
        context: ConversationContext,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Generate confirmation summary for user.

        Args:
            context: Current conversation context
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with confirmation summary

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversatorial-confirm-understanding")

        try:
            context.state = ConversationState.CONFIRMING

            result = await self.confirm_understanding_module.acall(
                task_description=context.task_description,
                taxonomy_path=context.metadata.get("taxonomy_path", ""),
                skill_metadata_draft=context.current_understanding,
                collected_examples=context.collected_examples,
            )

            summary = result.get("confirmation_summary", "")

            # Add to context
            context.messages.append(
                ConversationMessage(
                    role="assistant",
                    content=summary,
                    metadata={"type": "confirmation_summary"},
                )
            )

            if enable_mlflow:
                log_phase_metrics(
                    "confirm_understanding",
                    {
                        "completeness": result.get("completeness_score", 0.0),
                    },
                )

            return {
                "confirmation_summary": summary,
                "key_points": result.get("key_points", []),
                "completeness_score": result.get("completeness_score", 0.0),
            }

        except Exception as e:
            logger.exception(f"Error confirming understanding: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def process_feedback(
        self,
        user_feedback: str,
        skill_content: str,
        context: ConversationContext,
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Process user feedback on skill content.

        Args:
            user_feedback: User's feedback
            skill_content: Current skill content
            context: Current conversation context
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with processed feedback and changes

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversatorial-process-feedback")

        try:
            context.state = ConversationState.REVIEWING
            context.messages.append(
                ConversationMessage(
                    role="user",
                    content=user_feedback,
                    metadata={"type": "feedback"},
                )
            )

            result = await self.process_feedback_module.acall(
                user_feedback=user_feedback,
                skill_content=skill_content,
                conversation_history=str([m.to_dict() for m in context.messages[-5:]]),
            )

            if enable_mlflow:
                log_phase_metrics(
                    "process_feedback",
                    {
                        "actionable_changes": len(result.get("actionable_changes", [])),
                    },
                )

            return {
                "actionable_changes": result.get("actionable_changes", []),
                "sentiment": result.get("feedback_sentiment", ""),
                "requires_refinement": result.get("requires_refinement", False),
            }

        except Exception as e:
            logger.exception(f"Error processing feedback: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    async def suggest_tests(
        self,
        skill_content: str,
        skill_metadata: dict[str, Any],
        enable_mlflow: bool = True,
    ) -> dict[str, Any]:
        """
        Suggest tests for the skill.

        Args:
            skill_content: Skill content
            skill_metadata: Skill metadata
            enable_mlflow: Whether to track with MLflow

        Returns:
            Dictionary with suggested tests

        """
        if enable_mlflow:
            setup_mlflow_experiment("conversatorial-suggest-tests")

        try:
            result = await self.suggest_tests_module.acall(
                skill_content=skill_content,
                skill_metadata=str(skill_metadata),
            )

            if enable_mlflow:
                log_phase_metrics(
                    "suggest_tests",
                    {
                        "test_count": len(result.get("test_suggestions", [])),
                    },
                )

            return {
                "test_suggestions": result.get("test_suggestions", []),
                "coverage_areas": result.get("coverage_areas", []),
            }

        except Exception as e:
            logger.exception(f"Error suggesting tests: {e}")
            raise

        finally:
            if enable_mlflow:
                end_mlflow_run()

    # Synchronous wrappers
    def initialize_conversation_sync(self, *args, **kwargs) -> ConversationContext:
        """Synchronous wrapper for initialize_conversation."""
        return run_async(lambda: self.initialize_conversation(*args, **kwargs))

    def interpret_intent_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for interpret_intent."""
        return run_async(lambda: self.interpret_intent(*args, **kwargs))

    def generate_clarifying_question_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for generate_clarifying_question."""
        return run_async(lambda: self.generate_clarifying_question(*args, **kwargs))

    def deep_understanding_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for deep_understanding."""
        return run_async(lambda: self.deep_understanding(*args, **kwargs))

    def confirm_understanding_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for confirm_understanding."""
        return run_async(lambda: self.confirm_understanding(*args, **kwargs))

    def process_feedback_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for process_feedback."""
        return run_async(lambda: self.process_feedback(*args, **kwargs))

    def suggest_tests_sync(self, *args, **kwargs) -> dict[str, Any]:
        """Synchronous wrapper for suggest_tests."""
        return run_async(lambda: self.suggest_tests(*args, **kwargs))


__all__ = [
    "ConversationalOrchestrator",
    "ConversationState",
    "IntentType",
    "ConversationMessage",
    "ConversationContext",
]
