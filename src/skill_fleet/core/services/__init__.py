"""
Services layer for skill-fleet.

This module provides the service classes that implement the core business
logic for skill creation, conversation management, and workflow orchestration.

Directory Structure:
- base.py: BaseService class with common dependencies and utilities
- models.py: Conversation-related Pydantic models

Import Guidelines:
- For base class: from skill_fleet.core.services import BaseService
- For models: from skill_fleet.core.services import ConversationSession, AgentResponse
- For errors: from skill_fleet.core.services import ServiceError, ConfigurationError
"""

from skill_fleet.core.services.base import (
    BaseService,
    ConfigurationError,
    ServiceError,
    ValidationError,
)
from skill_fleet.core.services.models import (
    AgentResponse,
    ConversationMessage,
    ConversationSession,
    ConversationState,
    MessageRole,
)

__all__ = [
    # Base
    "BaseService",
    "ConfigurationError",
    "ServiceError",
    "ValidationError",
    # Models
    "AgentResponse",
    "ConversationMessage",
    "ConversationSession",
    "ConversationState",
    "MessageRole",
]
