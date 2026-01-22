"""
Conversation-related models for skill-fleet services.

Extracted from agent/agent.py to support the unified service architecture.
These models track conversation state, sessions, and responses for the
conversational skill creation workflow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from skill_fleet.core.models import ChecklistState


class ConversationState(StrEnum):
    """
    Conversation workflow states.

    Tracks the progression through the skill creation conversation,
    from initial exploration through TDD verification to completion.
    """

    EXPLORING = "EXPLORING"
    """Understanding user intent, asking clarifying questions."""

    DEEP_UNDERSTANDING = "DEEP_UNDERSTANDING"
    """Asking WHY questions, researching context."""

    MULTI_SKILL_DETECTED = "MULTI_SKILL_DETECTED"
    """Multiple skills needed, presenting breakdown."""

    CONFIRMING = "CONFIRMING"
    """Presenting confirmation summary before creation (MANDATORY)."""

    READY = "READY"
    """User confirmed, ready to create skill."""

    CREATING = "CREATING"
    """Executing skill creation workflow."""

    TDD_RED_PHASE = "TDD_RED_PHASE"
    """Running baseline tests without skill."""

    TDD_GREEN_PHASE = "TDD_GREEN_PHASE"
    """Verifying skill works with tests."""

    TDD_REFACTOR_PHASE = "TDD_REFACTOR_PHASE"
    """Closing loopholes, re-testing."""

    REVIEWING = "REVIEWING"
    """Presenting skill for user feedback."""

    REVISING = "REVISING"
    """Processing feedback and regenerating."""

    CHECKLIST_COMPLETE = "CHECKLIST_COMPLETE"
    """TDD checklist fully complete."""

    COMPLETE = "COMPLETE"
    """Skill approved, saved, ready for next (if multiple skills)."""


class MessageRole(StrEnum):
    """Role of message sender in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """
    A single message in conversation history.

    Represents a message exchanged between user and agent during
    the skill creation conversation.
    """

    role: MessageRole = Field(description="Who sent this message")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the message was sent",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (e.g., thinking content, action taken)",
    )

    class Config:
        """Pydantic config."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class ConversationSession(BaseModel):
    """
    Manages conversation session state.

    Tracks the full state of a skill creation conversation, including
    message history, collected examples, workflow state, and TDD checklist.
    """

    messages: list[ConversationMessage] = Field(
        default_factory=list,
        description="Full message history",
    )
    collected_examples: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Examples collected from user",
    )
    state: ConversationState = Field(
        default=ConversationState.EXPLORING,
        description="Current workflow state",
    )
    task_description: str = Field(
        default="",
        description="Refined task description",
    )
    multi_skill_queue: list[str] = Field(
        default_factory=list,
        description="Queue of skills to create (if multiple detected)",
    )
    current_skill_index: int = Field(
        default=0,
        description="Index of current skill being created",
    )
    skill_draft: dict[str, Any] | None = Field(
        default=None,
        description="Current skill draft (if in progress)",
    )
    checklist_state: ChecklistState = Field(
        default_factory=ChecklistState,
        description="TDD checklist completion state",
    )
    pending_confirmation: dict[str, Any] | None = Field(
        default=None,
        description="Pending confirmation data (if waiting for user)",
    )
    taxonomy_path: str = Field(
        default="",
        description="Proposed taxonomy path for skill",
    )
    skill_metadata_draft: dict[str, Any] | None = Field(
        default=None,
        description="Draft skill metadata",
    )
    deep_understanding: dict[str, Any] | None = Field(
        default=None,
        description="Deep understanding phase state",
    )
    user_problem: str | None = Field(
        default=None,
        description="User's stated problem",
    )
    user_goals: list[str] | None = Field(
        default=None,
        description="User's stated goals",
    )
    research_context: dict[str, Any] | None = Field(
        default=None,
        description="Research context gathered during understanding",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the session was created",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the session was last updated",
    )

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        """
        Add a message to the conversation history.

        Args:
            role: Who sent the message
            content: Message content
            metadata: Optional metadata

        Returns:
            The created message

        """
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)
        return message

    def get_message_history(
        self,
        limit: int | None = None,
        roles: list[MessageRole] | None = None,
    ) -> list[ConversationMessage]:
        """
        Get message history with optional filtering.

        Args:
            limit: Maximum number of messages to return (from end)
            roles: Filter to specific roles

        Returns:
            Filtered message list

        """
        messages = self.messages
        if roles:
            messages = [m for m in messages if m.role in roles]
        if limit:
            messages = messages[-limit:]
        return messages

    def to_legacy_dict(self) -> dict[str, Any]:
        """
        Serialize to dict format compatible with legacy agent.py.

        Returns:
            Dict matching the original dataclass format

        """
        return {
            "messages": [
                {"role": m.role.value, "content": m.content, **m.metadata}
                for m in self.messages
            ],
            "collected_examples": self.collected_examples,
            "state": self.state.value,
            "task_description": self.task_description,
            "multi_skill_queue": self.multi_skill_queue,
            "current_skill_index": self.current_skill_index,
            "skill_draft": self.skill_draft,
            "checklist_state": self.checklist_state.model_dump(),
            "pending_confirmation": self.pending_confirmation,
            "taxonomy_path": self.taxonomy_path,
            "skill_metadata_draft": self.skill_metadata_draft,
            "deep_understanding": self.deep_understanding,
            "user_problem": self.user_problem,
            "user_goals": self.user_goals,
            "research_context": self.research_context,
        }

    @classmethod
    def from_legacy_dict(cls, data: dict[str, Any]) -> ConversationSession:
        """
        Deserialize from legacy dict format.

        Args:
            data: Dict in legacy agent.py format

        Returns:
            ConversationSession instance

        """
        messages = []
        for msg in data.get("messages", []):
            role = MessageRole(msg.get("role", "user"))
            content = msg.get("content", "")
            metadata = {k: v for k, v in msg.items() if k not in ("role", "content")}
            messages.append(
                ConversationMessage(role=role, content=content, metadata=metadata)
            )

        checklist_data = data.get("checklist_state", {})
        checklist = (
            ChecklistState(**checklist_data) if checklist_data else ChecklistState()
        )

        return cls(
            messages=messages,
            collected_examples=data.get("collected_examples", []),
            state=ConversationState(data.get("state", "EXPLORING")),
            task_description=data.get("task_description", ""),
            multi_skill_queue=data.get("multi_skill_queue", []),
            current_skill_index=data.get("current_skill_index", 0),
            skill_draft=data.get("skill_draft"),
            checklist_state=checklist,
            pending_confirmation=data.get("pending_confirmation"),
            taxonomy_path=data.get("taxonomy_path", ""),
            skill_metadata_draft=data.get("skill_metadata_draft"),
            deep_understanding=data.get("deep_understanding"),
            user_problem=data.get("user_problem"),
            user_goals=data.get("user_goals"),
            research_context=data.get("research_context"),
        )


class AgentResponse(BaseModel):
    """
    Response from conversational agent.

    Contains the agent's message, state updates, and metadata about
    the action taken and whether user input is required.
    """

    message: str = Field(description="Main conversational message")
    thinking_content: str = Field(
        default="",
        description="Gemini 3 thinking tokens (if available)",
    )
    state: ConversationState | None = Field(
        default=None,
        description="Updated state (if changed)",
    )
    action: str | None = Field(
        default=None,
        description="Action taken (e.g., 'ask_question', 'create_skill')",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional data (questions, options, etc.)",
    )
    requires_user_input: bool = Field(
        default=True,
        description="Whether agent is waiting for user response",
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize response to dict.

        Returns:
            Dict representation for API responses

        """
        return {
            "message": self.message,
            "thinking_content": self.thinking_content,
            "state": self.state.value if self.state else None,
            "action": self.action,
            "data": self.data,
            "requires_user_input": self.requires_user_input,
        }
