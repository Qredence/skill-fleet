from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skill_fleet.core.services.conversation.engine import ConversationService
from skill_fleet.core.services.conversation.models import (
    AgentResponse,
    ConversationSession,
    ConversationState,
)


@pytest.fixture
def mock_taxonomy():
    taxonomy = MagicMock()
    taxonomy.get_mounted_skills.return_value = []
    taxonomy.get_relevant_branches.return_value = {}
    return taxonomy


@pytest.fixture
def service(mock_taxonomy):
    return ConversationService(taxonomy_manager=mock_taxonomy)


@pytest.mark.asyncio
async def test_handle_exploring_create_skill(service):
    # Mock _execute_with_streaming to simulate InterpretIntent returning "create_skill"
    # and AssessReadiness returning False (ask question)

    session = ConversationSession()

    # We need to mock the sequence of calls to _execute_with_streaming
    # 1. interpret_intent -> create_skill
    # 2. detect_multi_skill -> False
    # 3. assess_readiness -> False
    # 4. generate_question -> "What language?"

    async def side_effect(module, thinking_callback=None, **kwargs):
        if module == service.interpret_intent:
            return {
                "intent_type": "create_skill",
                "extracted_task": "Create python skill",
                "confidence": 0.9,
            }, "Thinking about intent..."
        elif module == service.detect_multi_skill:
            return {
                "requires_multiple_skills": False,
                "skill_breakdown": [],
                "reasoning": "Single skill",
                "suggested_order": [],
            }, "Checking multi skill..."
        elif module == service.assess_readiness:
            return {
                "readiness_score": 0.5,
                "should_proceed": False,
                "readiness_reasoning": "Need more info",
            }, "Checking readiness..."
        elif module == service.generate_question:
            return {
                "question": "What language?",
                "question_options": ["Python", "Rust"],
                "reasoning": "Need language",
            }, "Generating question..."
        elif module == service.deep_understanding_module:
            # Should not be called if we mock readiness to fail immediately?
            # Or handle_exploring calls it?
            # If deep_understanding not complete, it calls it.
            return {
                "readiness_score": 0.5,
                "next_question": {
                    "id": "q1",
                    "question": "Why?",
                    "options": [{"id": "a", "label": "A", "description": "desc"}],
                },
            }, "Deep understanding..."

        return {}, ""

    with patch.object(service, "_execute_with_streaming", side_effect=side_effect):
        response = await service.handle_exploring("Create python skill", session, None)

        # Should transition to DEEP_UNDERSTANDING because session.deep_understanding is empty
        # and handle_exploring calls handle_deep_understanding

        assert response.state == ConversationState.DEEP_UNDERSTANDING
        assert response.action == "ask_understanding_question"
        assert session.task_description == "Create python skill"


@pytest.mark.asyncio
async def test_respond_updates_session_state(service):
    session = ConversationSession()
    session.state = ConversationState.DEEP_UNDERSTANDING

    response = AgentResponse(
        message="Done",
        state=ConversationState.EXPLORING,
        action="deep_understanding_complete",
        requires_user_input=False,
    )

    with patch.object(service, "handle_deep_understanding", AsyncMock(return_value=response)):
        await service.respond("continue", session, None)

    assert session.state == ConversationState.EXPLORING


@pytest.mark.asyncio
async def test_handle_exploring_skips_multi_skill_when_scoping_complete(service):
    session = ConversationSession(
        task_description="Modular Multi-Skill Breakdown",
        deep_understanding={"complete": True, "scoping_complete": True},
    )

    async def side_effect(module, thinking_callback=None, **kwargs):
        if module == service.interpret_intent:
            return {
                "intent_type": "create_skill",
                "extracted_task": "Modular Multi-Skill Breakdown",
                "confidence": 0.9,
            }, ""
        if module == service.detect_multi_skill:
            raise AssertionError("detect_multi_skill should be skipped when scoping_complete")
        if module == service.assess_readiness:
            return {
                "readiness_score": 0.6,
                "should_proceed": False,
                "readiness_reasoning": "Need more info",
            }, ""
        if module == service.generate_question:
            return {
                "question": "Which components matter most?",
                "question_options": ["Discovery", "Retrieval", "Analysis"],
                "reasoning": "Clarify scope",
            }, ""
        return {}, ""

    with patch.object(service, "_execute_with_streaming", side_effect=side_effect):
        response = await service.handle_exploring("Continue", session, None)

    assert response.action == "ask_question"
    assert response.data.get("readiness_score") == 0.6


@pytest.mark.asyncio
async def test_plan_selection_locks_scoping_and_prevents_reprompt(service):
    """
    Regression test for the "scoping loop":

    - agent proposes alternative approaches (MULTI_SKILL_DETECTED)
    - user selects a plan
    - agent must not re-run DetectMultiSkill and re-prompt for a plan again
    """
    session = ConversationSession(
        state=ConversationState.MULTI_SKILL_DETECTED,
        multi_skill_queue=["Plan A", "Plan B"],
        task_description="Original task",
    )

    # User selects a plan from the alternatives list.
    resp = service.handle_multi_skill("Plan A", session)
    assert resp.action == "plan_selected"
    assert session.task_description == "Plan A"
    assert session.deep_understanding and session.deep_understanding.get("scoping_complete") is True

    # Simulate deep-understanding completion and returning to exploring.
    session.state = ConversationState.EXPLORING
    session.deep_understanding["complete"] = True

    async def side_effect(module, thinking_callback=None, **kwargs):
        if module == service.detect_multi_skill:
            raise AssertionError("detect_multi_skill should be skipped after plan selection")
        if module == service.assess_readiness:
            return {
                "readiness_score": 0.6,
                "should_proceed": False,
                "readiness_reasoning": "Need more info",
            }, ""
        if module == service.generate_question:
            return {
                "question": "Clarify details?",
                "question_options": [],
                "reasoning": "Missing info",
            }, ""
        return {}, ""

    with patch.object(service, "_execute_with_streaming", side_effect=side_effect):
        response = await service.handle_exploring("continue", session, None)

    assert response.action == "ask_question"
    assert response.data.get("readiness_score") == 0.6
