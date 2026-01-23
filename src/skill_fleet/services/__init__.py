"""
Cross-cutting services for Skills Fleet.

This is the SINGLE services directory consolidating all service logic:

- llm/: LLM service layer (clients, routing, fallback)
- cache/: Caching service
- monitoring/: Observability (traces, metrics, logging)
- tools/: External tool integrations (filesystem, web, git)
- conversation/: Conversation service (from core/services/)

Import Guidelines:
    from skill_fleet.services import BaseService
    from skill_fleet.services.llm import LLMClient
    from skill_fleet.services.conversation import ConversationEngine
"""

from __future__ import annotations

# Re-export from existing core.services during migration
from skill_fleet.core.services import (
    AgentResponse,
    BaseService,
    ConfigurationError,
    ConversationMessage,
    ConversationSession,
    ConversationState,
    MessageRole,
    ServiceError,
    ValidationError,
)

__all__ = [
    "AgentResponse",
    "BaseService",
    "ConfigurationError",
    "ConversationMessage",
    "ConversationSession",
    "ConversationState",
    "MessageRole",
    "ServiceError",
    "ValidationError",
]
