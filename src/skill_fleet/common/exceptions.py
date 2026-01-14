"""Exception hierarchy for Skills Fleet.

This module defines specific exception types used throughout the Skills Fleet
codebase. Using specific exceptions improves error handling, debugging, and
provides better context when errors occur.
"""

from __future__ import annotations

# =============================================================================
# Base Exception
# =============================================================================


class SkillsFleetError(Exception):
    """Base exception for all Skills Fleet errors.

    All custom exceptions should inherit from this base class, allowing
    consumers to catch all Skills Fleet errors with a single except clause.
    """

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        """Initialize the exception with a message and optional details.

        Args:
            message: Human-readable error message
            details: Additional context about the error (e.g., skill_id, file_path)
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation including details if available."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


# =============================================================================
# Skill Creation Errors
# =============================================================================


class SkillError(SkillsFleetError):
    """Base exception for skill-related errors."""


class SkillCreationError(SkillError):
    """Raised when skill creation fails.

    This can occur due to:
    - Invalid skill metadata
    - Missing required fields
    - Failed validation checks
    - LLM generation failures
    """


class SkillValidationError(SkillError):
    """Raised when skill validation fails.

    This can occur when:
    - Skill doesn't comply with agentskills.io spec
    - YAML frontmatter is malformed
    - Required examples are missing
    - Test cases are invalid
    """


class SkillNotFoundError(SkillError):
    """Raised when a requested skill cannot be found.

    Attributes:
        skill_path: The path that was searched for
    """

    def __init__(self, message: str, *, skill_path: str) -> None:
        super().__init__(message, details={"skill_path": skill_path})
        self.skill_path = skill_path


class SkillRevisionError(SkillError):
    """Raised when skill revision fails.

    This can occur when:
    - Feedback cannot be applied
    - Revision workflow is interrupted
    - TDD checklist cannot be satisfied
    """


# =============================================================================
# Taxonomy Errors
# =============================================================================


class TaxonomyError(SkillsFleetError):
    """Base exception for taxonomy-related errors."""


class TaxonomyValidationError(TaxonomyError):
    """Raised when taxonomy structure is invalid.

    This can occur when:
    - Circular dependencies are detected
    - Invalid skill path format
    - Duplicate skill IDs
    - Invalid hierarchy depth
    """


class TaxonomyNotFoundError(TaxonomyError):
    """Raised when a taxonomy path cannot be resolved.

    Attributes:
        taxonomy_path: The path that was searched for
    """

    def __init__(self, message: str, *, taxonomy_path: str) -> None:
        super().__init__(message, details={"taxonomy_path": taxonomy_path})
        self.taxonomy_path = taxonomy_path


# =============================================================================
# DSPy Workflow Errors
# =============================================================================


class DSPyWorkflowError(SkillsFleetError):
    """Base exception for DSPy workflow errors."""


class DSPyConfigurationError(DSPyWorkflowError):
    """Raised when DSPy configuration is invalid or incomplete."""


class DSPyExecutionError(DSPyWorkflowError):
    """Raised when DSPy program execution fails.

    This can occur when:
    - LLM API calls fail
    - Timeout exceeded
    - Invalid response format
    - Optimization fails
    """


class DSPyOptimizationError(DSPyWorkflowError):
    """Raised when DSPy optimization (MIPROv2, GEPA) fails.

    Attributes:
        optimizer: The optimizer that failed (e.g., "miprov2", "gepa")
    """

    def __init__(self, message: str, *, optimizer: str) -> None:
        super().__init__(message, details={"optimizer": optimizer})
        self.optimizer = optimizer


# =============================================================================
# Conversation Agent Errors
# =============================================================================


class AgentError(SkillsFleetError):
    """Base exception for agent-related errors."""


class ConversationStateError(AgentError):
    """Raised when conversation state is invalid or transition fails.

    This can occur when:
    - Invalid state transition
    - State corruption
    - Missing required state data
    """


class AgentExecutionError(AgentError):
    """Raised when agent execution fails.

    This can occur when:
    - Message processing fails
    - Research phase errors
    - Workflow interruption
    """


class TDDWorkflowError(AgentError):
    """Raised when TDD (Test-Driven Development) workflow fails.

    This can occur when:
    - Red phase tests fail unexpectedly
    - Green phase validation fails
    - Refactor phase introduces issues
    - Checklist cannot be completed
    """


# =============================================================================
# API Errors
# =============================================================================


class APIError(SkillsFleetError):
    """Base exception for API-related errors."""


class APIValidationError(APIError):
    """Raised when API request validation fails.

    This can occur when:
    - Invalid request body
    - Missing required fields
    - Type validation failures
    """


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (if available)
    """

    def __init__(self, message: str, *, retry_after: int | None = None) -> None:
        super().__init__(message, details={"retry_after": retry_after})
        self.retry_after = retry_after


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(SkillsFleetError):
    """Raised when configuration is invalid or missing.

    This can occur when:
    - config.yaml is malformed
    - Required environment variables are missing
    - Invalid model configuration
    - LLM provider unreachable
    """

    def __init__(self, message: str, *, config_key: str | None = None) -> None:
        details = {"config_key": config_key} if config_key else None
        super().__init__(message, details=details)
        self.config_key = config_key


# =============================================================================
# Research Errors
# =============================================================================


class ResearchError(SkillsFleetError):
    """Base exception for research-related errors."""


class FileSystemResearchError(ResearchError):
    """Raised when filesystem research fails.

    This can occur when:
    - File not found
    - Permission denied
    - Invalid file format
    """


class WebSearchError(ResearchError):
    """Raised when web search research fails.

    This can occur when:
    - Search API unavailable
    - Network errors
    - Invalid search query
    """


# =============================================================================
# LLM Provider Errors
# =============================================================================


class LLMProviderError(SkillsFleetError):
    """Base exception for LLM provider errors."""


class LLMAuthenticationError(LLMProviderError):
    """Raised when LLM provider authentication fails.

    This typically indicates missing or invalid API keys.
    """


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM provider rate limit is exceeded.

    Attributes:
        provider: The LLM provider (e.g., "openai", "gemini")
        retry_after: Seconds to wait before retrying (if available)
    """

    def __init__(self, message: str, *, provider: str, retry_after: int | None = None) -> None:
        super().__init__(message, details={"provider": provider, "retry_after": retry_after})
        self.provider = provider
        self.retry_after = retry_after


class LLMResponseError(LLMProviderError):
    """Raised when LLM response is invalid or unexpected.

    This can occur when:
    - Malformed JSON response
    - Missing expected fields
    - Content filter triggered
    """


# =============================================================================
# Session Errors
# =============================================================================


class SessionError(SkillsFleetError):
    """Base exception for session-related errors."""


class SessionNotFoundError(SessionError):
    """Raised when a session cannot be found.

    Attributes:
        session_id: The session ID that was searched for
    """

    def __init__(self, message: str, *, session_id: str) -> None:
        super().__init__(message, details={"session_id": session_id})
        self.session_id = session_id


class SessionExpiredError(SessionError):
    """Raised when a session has expired."""


# =============================================================================
# Export convenience
# =============================================================================


__all__ = [
    # Base
    "SkillsFleetError",
    # Skill errors
    "SkillError",
    "SkillCreationError",
    "SkillValidationError",
    "SkillNotFoundError",
    "SkillRevisionError",
    # Taxonomy errors
    "TaxonomyError",
    "TaxonomyValidationError",
    "TaxonomyNotFoundError",
    # DSPy errors
    "DSPyWorkflowError",
    "DSPyConfigurationError",
    "DSPyExecutionError",
    "DSPyOptimizationError",
    # Agent errors
    "AgentError",
    "ConversationStateError",
    "AgentExecutionError",
    "TDDWorkflowError",
    # API errors
    "APIError",
    "APIValidationError",
    "APIAuthenticationError",
    "APIRateLimitError",
    # Configuration errors
    "ConfigurationError",
    # Research errors
    "ResearchError",
    "FileSystemResearchError",
    "WebSearchError",
    # LLM errors
    "LLMProviderError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMResponseError",
    # Session errors
    "SessionError",
    "SessionNotFoundError",
    "SessionExpiredError",
]
