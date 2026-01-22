"""Conversation models and state definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ...models import ChecklistState


class ConversationState(StrEnum):
    """Conversation workflow states."""

    EXPLORING = "EXPLORING"  # Understanding user intent, asking clarifying questions
    DEEP_UNDERSTANDING = "DEEP_UNDERSTANDING"  # Asking WHY questions, researching context
    MULTI_SKILL_DETECTED = "MULTI_SKILL_DETECTED"  # Multiple skills needed, presenting breakdown
    CONFIRMING = "CONFIRMING"  # Presenting confirmation summary before creation (MANDATORY)
    READY = "READY"  # User confirmed, ready to create skill
    CREATING = "CREATING"  # Executing skill creation workflow
    TDD_RED_PHASE = "TDD_RED_PHASE"  # Running baseline tests without skill
    TDD_GREEN_PHASE = "TDD_GREEN_PHASE"  # Verifying skill works with tests
    TDD_REFACTOR_PHASE = "TDD_REFACTOR_PHASE"  # Closing loopholes, re-testing
    REVIEWING = "REVIEWING"  # Presenting skill for user feedback
    REVISING = "REVISING"  # Processing feedback and regenerating
    CHECKLIST_COMPLETE = "CHECKLIST_COMPLETE"  # TDD checklist fully complete
    COMPLETE = "COMPLETE"  # Skill approved, saved, ready for next (if multiple skills)


@dataclass
class ConversationSession:
    """Manages conversation session state."""

    # Message history
    messages: list[dict[str, Any]] = field(default_factory=list)
    # Collected examples
    collected_examples: list[dict[str, Any]] = field(default_factory=list)
    # Current workflow state
    state: ConversationState = ConversationState.EXPLORING
    # Current task description (refined)
    task_description: str = ""
    # Multi-skill queue (if multiple skills needed)
    multi_skill_queue: list[str] = field(default_factory=list)
    current_skill_index: int = 0
    # Skill draft (if in progress)
    skill_draft: dict[str, Any] | None = None
    # Checklist state
    checklist_state: ChecklistState = field(default_factory=ChecklistState)
    # Confirmation pending (if waiting for user confirmation)
    pending_confirmation: dict[str, Any] | None = None
    # Taxonomy path (proposed)
    taxonomy_path: str = ""
    # Skill metadata draft
    skill_metadata_draft: dict[str, Any] | None = None
    # Deep understanding phase state
    deep_understanding: dict[str, Any] | None = None
    user_problem: str | None = None
    user_goals: list[str] | None = None
    research_context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize session to dict for persistence."""
        return {
            "messages": self.messages,
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
    def from_dict(cls, data: dict[str, Any]) -> ConversationSession:
        """Deserialize session from dict."""
        session = cls()
        session.messages = data.get("messages", [])
        session.collected_examples = data.get("collected_examples", [])
        session.state = ConversationState(data.get("state", "EXPLORING"))
        session.task_description = data.get("task_description", "")
        session.multi_skill_queue = data.get("multi_skill_queue", [])
        session.current_skill_index = data.get("current_skill_index", 0)
        session.skill_draft = data.get("skill_draft")
        if "checklist_state" in data:
            session.checklist_state = ChecklistState(**data["checklist_state"])
        session.pending_confirmation = data.get("pending_confirmation")
        session.taxonomy_path = data.get("taxonomy_path", "")
        session.skill_metadata_draft = data.get("skill_metadata_draft")
        session.deep_understanding = data.get("deep_understanding")
        session.user_problem = data.get("user_problem")
        session.user_goals = data.get("user_goals")
        session.research_context = data.get("research_context")
        return session


@dataclass
class AgentResponse:
    """Response from conversational service."""

    message: str  # Main conversational message
    thinking_content: str = ""  # Gemini 3 thinking tokens (if available)
    state: ConversationState | None = None  # Updated state (if changed)
    action: str | None = (
        None  # Action taken (e.g., "ask_question", "create_skill", "wait_for_confirmation")
    )
    data: dict[str, Any] = field(default_factory=dict)  # Additional data (questions, options, etc.)
    requires_user_input: bool = True  # Whether agent is waiting for user response

    def to_dict(self) -> dict[str, Any]:
        """Serialize response to dict."""
        return {
            "message": self.message,
            "thinking_content": self.thinking_content,
            "state": self.state.value if self.state else None,
            "action": self.action,
            "data": self.data,
            "requires_user_input": self.requires_user_input,
        }
