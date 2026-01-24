"""
Unit tests for ConversationalOrchestrator.

Tests the multi-turn conversational workflow orchestrator that handles
intent interpretation, clarification, deep understanding, and feedback processing.
"""

import pytest

from skill_fleet.workflows.conversational_interface import (
    ConversationalOrchestrator,
    ConversationState,
    IntentType,
    ConversationMessage,
    ConversationContext,
)


@pytest.fixture
def orchestrator() -> ConversationalOrchestrator:
    """Create a ConversationalOrchestrator fixture."""
    return ConversationalOrchestrator()


def test_initialization(orchestrator: ConversationalOrchestrator) -> None:
    """Test orchestrator can be initialized."""
    assert orchestrator is not None
    assert hasattr(orchestrator, 'initialize_conversation')
    assert hasattr(orchestrator, 'interpret_intent')
    assert hasattr(orchestrator, 'generate_clarifying_question')
    assert hasattr(orchestrator, 'deep_understanding')
    assert hasattr(orchestrator, 'confirm_understanding')
    assert hasattr(orchestrator, 'process_feedback')
    assert hasattr(orchestrator, 'suggest_tests')


def test_orchestrator_has_expected_modules(orchestrator: ConversationalOrchestrator) -> None:
    """Test that orchestrator has all expected DSPy modules."""
    expected_modules = [
        'interpret_intent_module',
        'detect_multi_skill_module',
        'generate_question_module',
        'deep_understanding_module',
        'understanding_summary_module',
        'confirm_understanding_module',
        'assess_readiness_module',
        'present_skill_module',
        'process_feedback_module',
        'suggest_tests_module',
        'verify_tdd_module',
        'enhance_skill_module',
    ]

    for module_name in expected_modules:
        assert hasattr(orchestrator, module_name), f"Missing module: {module_name}"


def test_orchestrator_has_sync_wrappers(orchestrator: ConversationalOrchestrator) -> None:
    """Test that orchestrator has synchronous wrappers for async methods."""
    expected_sync_methods = [
        'initialize_conversation_sync',
        'interpret_intent_sync',
        'generate_clarifying_question_sync',
        'deep_understanding_sync',
        'confirm_understanding_sync',
        'process_feedback_sync',
        'suggest_tests_sync',
    ]

    for method_name in expected_sync_methods:
        assert hasattr(orchestrator, method_name), f"Missing sync wrapper: {method_name}"
        assert callable(getattr(orchestrator, method_name)), f"{method_name} is not callable"


def test_conversation_message_to_dict() -> None:
    """Test converting conversation message to dictionary."""
    message = ConversationMessage(
        role="user",
        content="Test message",
        metadata={"type": "test"},
    )

    message_dict = message.to_dict()
    assert isinstance(message_dict, dict)
    assert message_dict["role"] == "user"
    assert message_dict["content"] == "Test message"
    assert message_dict["metadata"]["type"] == "test"


def test_conversation_context_to_dict() -> None:
    """Test converting conversation context to dictionary."""
    context = ConversationContext(
        conversation_id="test123",
        state=ConversationState.CLARIFYING,
        messages=[
            ConversationMessage(role="user", content="Test"),
        ],
    )

    context_dict = context.to_dict()
    assert isinstance(context_dict, dict)
    assert context_dict["conversation_id"] == "test123"
    assert context_dict["state"] == "clarifying"
    assert len(context_dict["messages"]) == 1


def test_conversation_state_enum() -> None:
    """Test ConversationState enum values."""
    assert ConversationState.INITIALIZING.value == "initializing"
    assert ConversationState.INTERPRETING_INTENT.value == "interpreting_intent"
    assert ConversationState.CLARIFYING.value == "clarifying"
    assert ConversationState.COMPLETED.value == "completed"


def test_intent_type_enum() -> None:
    """Test IntentType enum values."""
    assert IntentType.CREATE_SKILL.value == "create_skill"
    assert IntentType.CLARIFY.value == "clarify"
    assert IntentType.REFINE.value == "refine"
    assert IntentType.MULTI_SKILL.value == "multi_skill"
    assert IntentType.UNKNOWN.value == "unknown"


def test_conversation_id_generation(orchestrator: ConversationalOrchestrator) -> None:
    """Test that conversation IDs are generated uniquely."""
    context1 = orchestrator.initialize_conversation_sync(enable_mlflow=False)
    context2 = orchestrator.initialize_conversation_sync(enable_mlflow=False)

    assert context1.conversation_id != context2.conversation_id
    assert len(context1.conversation_id) == 12  # UUID truncated to 12 chars


def test_initialize_conversation_signature(orchestrator: ConversationalOrchestrator) -> None:
    """Test that initialize_conversation has the expected signature."""
    import inspect

    sig = inspect.signature(orchestrator.initialize_conversation)
    params = list(sig.parameters.keys())

    # Check for expected parameters
    expected_params = [
        'initial_message',
        'metadata',
        'enable_mlflow',
    ]

    for param in expected_params:
        assert param in params, f"Missing parameter: {param}"


def test_conversation_context_defaults() -> None:
    """Test that ConversationContext has appropriate default values."""
    context = ConversationContext(
        conversation_id="test",
    )

    assert context.state == ConversationState.INITIALIZING
    assert context.messages == []
    assert context.collected_examples == []
    assert context.current_understanding == ""
    assert context.task_description == ""
    assert context.user_confirmations == {}
