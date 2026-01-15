"""Unit tests for common.exceptions module.

This module tests the exception hierarchy, initialization, message formatting,
details handling, and inheritance structure of all custom exceptions.
"""


from skill_fleet.common.exceptions import (
    # Agent errors
    AgentError,
    AgentExecutionError,
    # API errors
    APIAuthenticationError,
    APIError,
    APIRateLimitError,
    APIValidationError,
    # Configuration errors
    ConfigurationError,
    ConversationStateError,
    # DSPy errors
    DSPyConfigurationError,
    DSPyExecutionError,
    DSPyOptimizationError,
    DSPyWorkflowError,
    # Research errors
    FileSystemResearchError,
    # LLM errors
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMResponseError,
    ResearchError,
    # Session errors
    SessionError,
    SessionExpiredError,
    SessionNotFoundError,
    SkillCreationError,
    # Skill errors
    SkillError,
    SkillNotFoundError,
    SkillRevisionError,
    # Base
    SkillsFleetError,
    SkillValidationError,
    # Taxonomy errors
    TaxonomyError,
    TaxonomyNotFoundError,
    TaxonomyValidationError,
    TDDWorkflowError,
    WebSearchError,
)


class TestBaseException:
    """Test the base SkillsFleetError exception."""

    def test_basic_initialization(self):
        """Test basic exception initialization with message only."""
        error = SkillsFleetError("Test error message")
        assert error.message == "Test error message"
        assert error.details == {}
        assert str(error) == "Test error message"

    def test_initialization_with_details(self):
        """Test exception initialization with details dict."""
        details = {"skill_id": "test-skill", "path": "/test/path"}
        error = SkillsFleetError("Test error", details=details)
        assert error.message == "Test error"
        assert error.details == details
        assert "skill_id=test-skill" in str(error)
        assert "path=/test/path" in str(error)

    def test_string_representation_without_details(self):
        """Test __str__ method without details."""
        error = SkillsFleetError("Simple error")
        assert str(error) == "Simple error"

    def test_string_representation_with_details(self):
        """Test __str__ method with details."""
        error = SkillsFleetError("Error occurred", details={"key": "value", "count": 42})
        error_str = str(error)
        assert "Error occurred" in error_str
        assert "key=value" in error_str
        assert "count=42" in error_str

    def test_inheritance(self):
        """Test that SkillsFleetError inherits from Exception."""
        error = SkillsFleetError("Test")
        assert isinstance(error, Exception)


class TestSkillErrors:
    """Test skill-related exception classes."""

    def test_skill_error_inheritance(self):
        """Test SkillError inherits from SkillsFleetError."""
        error = SkillError("Test")
        assert isinstance(error, SkillsFleetError)
        assert isinstance(error, Exception)

    def test_skill_creation_error(self):
        """Test SkillCreationError initialization and inheritance."""
        error = SkillCreationError("Failed to create skill")
        assert isinstance(error, SkillError)
        assert error.message == "Failed to create skill"

    def test_skill_validation_error(self):
        """Test SkillValidationError initialization."""
        details = {"field": "name", "reason": "invalid format"}
        error = SkillValidationError("Validation failed", details=details)
        assert isinstance(error, SkillError)
        assert "field=name" in str(error)

    def test_skill_not_found_error(self):
        """Test SkillNotFoundError with skill_path attribute."""
        error = SkillNotFoundError("Skill not found", skill_path="/path/to/skill")
        assert isinstance(error, SkillError)
        assert error.skill_path == "/path/to/skill"
        assert error.details["skill_path"] == "/path/to/skill"
        assert "skill_path=/path/to/skill" in str(error)

    def test_skill_revision_error(self):
        """Test SkillRevisionError initialization."""
        error = SkillRevisionError("Revision failed")
        assert isinstance(error, SkillError)
        assert error.message == "Revision failed"


class TestTaxonomyErrors:
    """Test taxonomy-related exception classes."""

    def test_taxonomy_error_inheritance(self):
        """Test TaxonomyError inherits from SkillsFleetError."""
        error = TaxonomyError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_taxonomy_validation_error(self):
        """Test TaxonomyValidationError initialization."""
        error = TaxonomyValidationError("Invalid hierarchy")
        assert isinstance(error, TaxonomyError)
        assert error.message == "Invalid hierarchy"

    def test_taxonomy_not_found_error(self):
        """Test TaxonomyNotFoundError with taxonomy_path attribute."""
        error = TaxonomyNotFoundError("Path not found", taxonomy_path="skills/test/path")
        assert isinstance(error, TaxonomyError)
        assert error.taxonomy_path == "skills/test/path"
        assert error.details["taxonomy_path"] == "skills/test/path"


class TestDSPyErrors:
    """Test DSPy workflow exception classes."""

    def test_dspy_workflow_error_inheritance(self):
        """Test DSPyWorkflowError inherits from SkillsFleetError."""
        error = DSPyWorkflowError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_dspy_configuration_error(self):
        """Test DSPyConfigurationError initialization."""
        error = DSPyConfigurationError("Invalid config")
        assert isinstance(error, DSPyWorkflowError)

    def test_dspy_execution_error(self):
        """Test DSPyExecutionError initialization."""
        error = DSPyExecutionError("Execution failed")
        assert isinstance(error, DSPyWorkflowError)

    def test_dspy_optimization_error(self):
        """Test DSPyOptimizationError with optimizer attribute."""
        error = DSPyOptimizationError("Optimization failed", optimizer="miprov2")
        assert isinstance(error, DSPyWorkflowError)
        assert error.optimizer == "miprov2"
        assert error.details["optimizer"] == "miprov2"
        assert "optimizer=miprov2" in str(error)


class TestAgentErrors:
    """Test agent-related exception classes."""

    def test_agent_error_inheritance(self):
        """Test AgentError inherits from SkillsFleetError."""
        error = AgentError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_conversation_state_error(self):
        """Test ConversationStateError initialization."""
        error = ConversationStateError("Invalid state transition")
        assert isinstance(error, AgentError)

    def test_agent_execution_error(self):
        """Test AgentExecutionError initialization."""
        error = AgentExecutionError("Execution failed")
        assert isinstance(error, AgentError)

    def test_tdd_workflow_error(self):
        """Test TDDWorkflowError initialization."""
        error = TDDWorkflowError("TDD phase failed")
        assert isinstance(error, AgentError)


class TestAPIErrors:
    """Test API-related exception classes."""

    def test_api_error_inheritance(self):
        """Test APIError inherits from SkillsFleetError."""
        error = APIError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_api_validation_error(self):
        """Test APIValidationError initialization."""
        error = APIValidationError("Invalid request body")
        assert isinstance(error, APIError)

    def test_api_authentication_error(self):
        """Test APIAuthenticationError initialization."""
        error = APIAuthenticationError("Auth failed")
        assert isinstance(error, APIError)

    def test_api_rate_limit_error(self):
        """Test APIRateLimitError with retry_after attribute."""
        error = APIRateLimitError("Rate limit exceeded", retry_after=60)
        assert isinstance(error, APIError)
        assert error.retry_after == 60
        assert error.details["retry_after"] == 60
        assert "retry_after=60" in str(error)

    def test_api_rate_limit_error_without_retry(self):
        """Test APIRateLimitError without retry_after."""
        error = APIRateLimitError("Rate limit exceeded")
        assert error.retry_after is None


class TestConfigurationError:
    """Test configuration exception class."""

    def test_configuration_error_basic(self):
        """Test ConfigurationError basic initialization."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, SkillsFleetError)
        assert error.message == "Invalid config"
        assert error.config_key is None

    def test_configuration_error_with_key(self):
        """Test ConfigurationError with config_key."""
        error = ConfigurationError("Invalid value", config_key="models.default")
        assert error.config_key == "models.default"
        assert error.details["config_key"] == "models.default"


class TestResearchErrors:
    """Test research-related exception classes."""

    def test_research_error_inheritance(self):
        """Test ResearchError inherits from SkillsFleetError."""
        error = ResearchError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_filesystem_research_error(self):
        """Test FileSystemResearchError initialization."""
        error = FileSystemResearchError("File not found")
        assert isinstance(error, ResearchError)

    def test_web_search_error(self):
        """Test WebSearchError initialization."""
        error = WebSearchError("Search failed")
        assert isinstance(error, ResearchError)


class TestLLMProviderErrors:
    """Test LLM provider exception classes."""

    def test_llm_provider_error_inheritance(self):
        """Test LLMProviderError inherits from SkillsFleetError."""
        error = LLMProviderError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_llm_authentication_error(self):
        """Test LLMAuthenticationError initialization."""
        error = LLMAuthenticationError("Invalid API key")
        assert isinstance(error, LLMProviderError)

    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError with provider and retry_after."""
        error = LLMRateLimitError("Rate limited", provider="openai", retry_after=30)
        assert isinstance(error, LLMProviderError)
        assert error.provider == "openai"
        assert error.retry_after == 30
        assert error.details["provider"] == "openai"
        assert error.details["retry_after"] == 30

    def test_llm_rate_limit_error_without_retry(self):
        """Test LLMRateLimitError without retry_after."""
        error = LLMRateLimitError("Rate limited", provider="gemini")
        assert error.provider == "gemini"
        assert error.retry_after is None

    def test_llm_response_error(self):
        """Test LLMResponseError initialization."""
        error = LLMResponseError("Malformed response")
        assert isinstance(error, LLMProviderError)


class TestSessionErrors:
    """Test session-related exception classes."""

    def test_session_error_inheritance(self):
        """Test SessionError inherits from SkillsFleetError."""
        error = SessionError("Test")
        assert isinstance(error, SkillsFleetError)

    def test_session_not_found_error(self):
        """Test SessionNotFoundError with session_id attribute."""
        error = SessionNotFoundError("Session not found", session_id="abc123")
        assert isinstance(error, SessionError)
        assert error.session_id == "abc123"
        assert error.details["session_id"] == "abc123"

    def test_session_expired_error(self):
        """Test SessionExpiredError initialization."""
        error = SessionExpiredError("Session expired")
        assert isinstance(error, SessionError)


class TestExceptionHierarchy:
    """Test the overall exception hierarchy structure."""

    def test_all_custom_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from SkillsFleetError."""
        # Test exceptions that only need a message
        simple_exceptions = [
            SkillError,
            SkillCreationError,
            SkillValidationError,
            SkillRevisionError,
            TaxonomyError,
            TaxonomyValidationError,
            DSPyWorkflowError,
            DSPyConfigurationError,
            DSPyExecutionError,
            AgentError,
            ConversationStateError,
            AgentExecutionError,
            TDDWorkflowError,
            APIError,
            APIValidationError,
            APIAuthenticationError,
            ConfigurationError,
            ResearchError,
            FileSystemResearchError,
            WebSearchError,
            LLMProviderError,
            LLMAuthenticationError,
            LLMResponseError,
            SessionError,
            SessionExpiredError,
        ]

        for exc_class in simple_exceptions:
            exc = exc_class("Test message")
            assert isinstance(exc, SkillsFleetError)
            assert isinstance(exc, Exception)

        # Test exceptions that require additional arguments
        exc = SkillNotFoundError("Not found", skill_path="/test")
        assert isinstance(exc, SkillsFleetError)

        exc = TaxonomyNotFoundError("Not found", taxonomy_path="/test")
        assert isinstance(exc, SkillsFleetError)

        exc = DSPyOptimizationError("Failed", optimizer="miprov2")
        assert isinstance(exc, SkillsFleetError)

        exc = APIRateLimitError("Rate limited", retry_after=60)
        assert isinstance(exc, SkillsFleetError)

        exc = LLMRateLimitError("Rate limited", provider="openai", retry_after=30)
        assert isinstance(exc, SkillsFleetError)

        exc = SessionNotFoundError("Not found", session_id="abc123")
        assert isinstance(exc, SkillsFleetError)

    def test_catch_all_skillsfleet_errors(self):
        """Test that all custom exceptions can be caught with SkillsFleetError."""
        exceptions = [
            SkillCreationError("Test"),
            TaxonomyValidationError("Test"),
            DSPyExecutionError("Test"),
            APIRateLimitError("Test", retry_after=60),
            ConfigurationError("Test"),
            LLMAuthenticationError("Test"),
            SessionNotFoundError("Test", session_id="abc"),
        ]

        for exc in exceptions:
            try:
                raise exc
            except SkillsFleetError as e:
                assert isinstance(e, SkillsFleetError)


class TestExceptionDetails:
    """Test exception details handling."""

    def test_details_are_optional(self):
        """Test that details parameter is optional for all exceptions."""
        error = SkillsFleetError("Test")
        assert error.details == {}

    def test_details_are_preserved(self):
        """Test that provided details are preserved."""
        details = {"key1": "value1", "key2": 42, "key3": True}
        error = SkillsFleetError("Test", details=details)
        assert error.details == details

    def test_specialized_exceptions_add_details(self):
        """Test that specialized exceptions add their own details."""
        error = SkillNotFoundError("Not found", skill_path="/test/path")
        assert "skill_path" in error.details
        assert error.details["skill_path"] == "/test/path"

    def test_details_in_string_representation(self):
        """Test that details appear in string representation."""
        details = {"file": "config.yaml", "line": 42}
        error = SkillsFleetError("Parse error", details=details)
        error_str = str(error)
        assert "file=config.yaml" in error_str
        assert "line=42" in error_str
