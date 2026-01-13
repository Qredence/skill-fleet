"""Unit tests for conversational modules using MultiChainComparison and Predict.

Tests the new conversational modules that use:
- dspy.MultiChainComparison for higher quality outputs
- dspy.Predict for straightforward predictions
- Dynamic question generation (no fallback defaults)
- Reasoning/thinking display
"""

import json
from unittest.mock import MagicMock, patch

import dspy
import pytest

from skill_fleet.core.dspy.conversational import (
    AssessReadinessModule,
    ConfirmUnderstandingModule,
    DeepUnderstandingModuleQA,
    DetectMultiSkillModuleQA,
    GenerateQuestionModuleQA,
    InterpretIntentModuleQA,
    PresentSkillModuleQA,
    ProcessFeedbackModule,
    SuggestTestsModuleQA,
    VerifyTDDModule,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_lm():
    """Create a mock DSPy LM."""
    lm = MagicMock(spec=dspy.LM)
    lm.history = []
    return lm


@pytest.fixture
def configured_dspy(mock_lm):
    """Configure DSPy with mock LM."""
    with dspy.context(lm=mock_lm):
        yield mock_lm


# =============================================================================
# InterpretIntentModuleQA Tests
# =============================================================================


class TestInterpretIntentModuleQA:
    """Tests for InterpretIntentModuleQA using MultiChainComparison."""

    def test_initialization_with_n_candidates(self):
        """Module should initialize with configurable n_candidates."""
        module = InterpretIntentModuleQA(n_candidates=5)
        # Verify module has interpret attribute (MultiChainComparison wraps signature internally)
        assert hasattr(module, "interpret")
        assert module.interpret is not None

    def test_forward_basic_case(self, configured_dspy):
        """Test basic intent interpretation."""
        # Create mock result
        mock_result = MagicMock()
        mock_result.intent_type = "create_skill"
        mock_result.extracted_task = "Create a skill for async testing"
        mock_result.confidence = 0.9

        # Patch the MultiChainComparison
        with patch.object(InterpretIntentModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = InterpretIntentModuleQA.__new__(InterpretIntentModuleQA)
            module.interpret = MagicMock(return_value=mock_result)

            result = module.forward(
                user_message="I want to create a skill",
                conversation_history=[],
                current_state="EXPLORING",
            )

            assert result["intent_type"] == "create_skill"
            assert result["extracted_task"] == "Create a skill for async testing"
            assert result["confidence"] == 0.9

    def test_forward_normalizes_intent_type(self, configured_dspy):
        """Test that intent type is normalized to lowercase."""
        mock_result = MagicMock()
        mock_result.intent_type = "CREATE_SKILL"  # Uppercase
        mock_result.extracted_task = "test"
        mock_result.confidence = 0.8

        with patch.object(InterpretIntentModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = InterpretIntentModuleQA.__new__(InterpretIntentModuleQA)
            module.interpret = MagicMock(return_value=mock_result)

            result = module.forward("test", [], "EXPLORING")

            assert result["intent_type"] == "create_skill"  # Normalized to lowercase

    def test_forward_with_list_conversation_history(self, configured_dspy):
        """Test handling list conversation history (converts to JSON string)."""
        mock_result = MagicMock()
        mock_result.intent_type = "clarify"
        mock_result.extracted_task = "test"
        mock_result.confidence = 0.7

        with patch.object(InterpretIntentModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = InterpretIntentModuleQA.__new__(InterpretIntentModuleQA)
            module.interpret = MagicMock(return_value=mock_result)

            history = [{"role": "user", "content": "hello"}]
            module.forward("test", history, "EXPLORING")

            # Should convert list to JSON string
            call_args = module.interpret.call_args
            assert '"role": "user"' in call_args.kwargs["conversation_history"]


# =============================================================================
# DetectMultiSkillModuleQA Tests
# =============================================================================


class TestDetectMultiSkillModuleQA:
    """Tests for DetectMultiSkillModuleQA using MultiChainComparison."""

    def test_initialization(self):
        """Module should initialize with configurable n_candidates."""
        module = DetectMultiSkillModuleQA(n_candidates=5)
        # Verify module has detect attribute
        assert hasattr(module, "detect")
        assert module.detect is not None

    def test_forward_single_skill(self, configured_dspy):
        """Test detection when single skill is sufficient."""
        mock_result = MagicMock()
        mock_result.requires_multiple_skills = False
        mock_result.skill_breakdown = []
        mock_result.reasoning = "Task is focused and single-purpose"
        mock_result.suggested_order = []

        with patch.object(DetectMultiSkillModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = DetectMultiSkillModuleQA.__new__(DetectMultiSkillModuleQA)
            module.detect = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create async testing skill",
                collected_examples=[],
                existing_skills=[],
            )

            assert result["requires_multiple_skills"] is False
            assert result["skill_breakdown"] == []
            assert result["reasoning"] == "Task is focused and single-purpose"

    def test_forward_multiple_skills(self, configured_dspy):
        """Test detection when multiple skills are needed."""
        mock_result = MagicMock()
        mock_result.requires_multiple_skills = True
        mock_result.skill_breakdown = ["async-setup", "async-assertions", "async-cleanup"]
        mock_result.reasoning = "Task has distinct phases that should be separate skills"
        mock_result.suggested_order = ["async-setup", "async-assertions", "async-cleanup"]

        with patch.object(DetectMultiSkillModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = DetectMultiSkillModuleQA.__new__(DetectMultiSkillModuleQA)
            module.detect = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create comprehensive async testing framework",
                collected_examples=[],
                existing_skills=[],
            )

            assert result["requires_multiple_skills"] is True
            assert result["skill_breakdown"] == ["async-setup", "async-assertions", "async-cleanup"]
            assert result["suggested_order"] == ["async-setup", "async-assertions", "async-cleanup"]


# =============================================================================
# GenerateQuestionModuleQA Tests
# =============================================================================


class TestGenerateQuestionModuleQA:
    """Tests for GenerateQuestionModuleQA using MultiChainComparison.

    Key requirement: NO fallback default questions - all questions must be
    dynamically generated based on context.
    """

    def test_initialization(self):
        """Module should initialize with configurable n_candidates."""
        module = GenerateQuestionModuleQA(n_candidates=3)
        # Verify module has generate attribute
        assert hasattr(module, "generate")
        assert module.generate is not None

    def test_forward_generates_contextual_question(self, configured_dspy):
        """Test that questions are dynamically generated based on context."""
        mock_result = MagicMock()
        mock_result.question = "What specific async patterns do you want to test?"
        mock_result.question_options = [
            "Event loop handling",
            "Task cancellation",
            "Timeouts",
            "All of the above",
        ]
        mock_result.reasoning = "Need to understand which async patterns are most relevant"

        with patch.object(GenerateQuestionModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = GenerateQuestionModuleQA.__new__(GenerateQuestionModuleQA)
            module.generate = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create async testing skill",
                collected_examples=[],
                conversation_context="User mentioned pytest and asyncio",
                previous_questions=["What testing framework do you use?"],
            )

            # Verify question is contextual (not a generic fallback)
            assert "async patterns" in result["question"].lower()
            assert result["reasoning"] != ""
            assert len(result["question_options"]) == 4

    def test_forward_avoids_repeating_questions(self, configured_dspy):
        """Test that previous_questions context prevents repetition."""
        mock_result = MagicMock()
        mock_result.question = "What specific timeout scenarios do you need?"
        mock_result.question_options = ["Network timeouts", "Computation timeouts", "Both"]
        mock_result.reasoning = "Already asked about testing framework, now focusing on timeouts"

        with patch.object(GenerateQuestionModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = GenerateQuestionModuleQA.__new__(GenerateQuestionModuleQA)
            module.generate = MagicMock(return_value=mock_result)

            previous_questions = [
                "What testing framework do you use?",
                "Do you need async support?",
            ]

            _ = module.forward(
                task_description="Create testing skill",
                collected_examples=[],
                conversation_context="",
                previous_questions=previous_questions,
            )

            # Verify the enhanced context includes previous questions
            call_args = module.generate.call_args
            context = call_args.kwargs["conversation_context"]
            assert "DO NOT repeat" in context
            assert "What testing framework do you use?" in context

    def test_no_fallback_default_questions(self, configured_dspy):
        """Verify that empty question is returned if generation fails (not a default)."""
        mock_result = MagicMock()
        mock_result.question = ""  # Empty indicates generation failure
        mock_result.question_options = []
        mock_result.reasoning = ""

        with patch.object(GenerateQuestionModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = GenerateQuestionModuleQA.__new__(GenerateQuestionModuleQA)
            module.generate = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create skill",
                collected_examples=[],
                conversation_context="",
            )

            # Should return empty strings, not fallback default questions
            assert result["question"] == ""
            assert result["question_options"] == []


# =============================================================================
# DeepUnderstandingModuleQA Tests
# =============================================================================


class TestDeepUnderstandingModuleQA:
    """Tests for DeepUnderstandingModuleQA using MultiChainComparison.

    Tests the generation of contextual multi-choice questions for understanding:
    - User's problem (WHY do they need this?)
    - User's goals (WHAT outcomes do they want?)
    - Context and constraints
    """

    def test_initialization(self):
        """Module should initialize with configurable n_candidates."""
        module = DeepUnderstandingModuleQA(n_candidates=3)
        # Verify module has understand attribute
        assert hasattr(module, "understand")
        assert module.understand is not None

    def test_forward_generates_contextual_question(self, configured_dspy):
        """Test generation of contextual multi-choice questions."""
        # Create mock next_question as JSON string
        question_json = json.dumps(
            {
                "id": "problem_identification",
                "question": "What problem are you trying to solve with async testing?",
                "context": "Understanding your use case",
                "options": [
                    {
                        "id": "flaky",
                        "label": "Flaky tests",
                        "description": "Tests that pass/fail randomly",
                    },
                    {"id": "slow", "label": "Slow tests", "description": "Tests taking too long"},
                    {
                        "id": "complexity",
                        "label": "Complex setup",
                        "description": "Hard to configure",
                    },
                ],
                "allows_multiple": False,
                "required": True,
            }
        )

        mock_result = MagicMock()
        mock_result.next_question = question_json
        mock_result.reasoning = (
            "Need to understand the user's core problem to design appropriate skill"
        )
        mock_result.research_needed = None
        mock_result.understanding_summary = "User needs help with async testing challenges"
        mock_result.readiness_score = 0.3
        mock_result.refined_task_description = "Create skill for async testing problem solving"
        mock_result.user_problem = "Flaky and slow async tests"
        mock_result.user_goals = ["Reliable tests", "Faster execution"]

        with patch.object(DeepUnderstandingModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = DeepUnderstandingModuleQA.__new__(DeepUnderstandingModuleQA)
            module.understand = MagicMock(return_value=mock_result)

            result = module.forward(
                initial_task="Create async testing skill",
                conversation_history=[],
                research_findings={},
                current_understanding="",
                previous_questions=[],
            )

            # Verify question parsing
            assert (
                result["next_question"]["question"]
                == "What problem are you trying to solve with async testing?"
            )
            assert result["reasoning"] != ""
            assert result["readiness_score"] == 0.3
            assert result["user_problem"] == "Flaky and slow async tests"
            assert result["user_goals"] == ["Reliable tests", "Faster execution"]

    def test_forward_with_research_needed(self, configured_dspy):
        """Test when research is needed to answer the question."""
        question_json = json.dumps(
            {
                "id": "research_q",
                "question": "What async testing best practices should we follow?",
                "options": [],
            }
        )

        research_json = json.dumps(
            {
                "type": "web",
                "query": "async testing best practices pytest",
                "reason": "Need current best practices for context",
            }
        )

        mock_result = MagicMock()
        mock_result.next_question = question_json
        mock_result.research_needed = research_json
        mock_result.reasoning = "Research would provide better context"
        mock_result.understanding_summary = ""
        mock_result.readiness_score = 0.5
        mock_result.refined_task_description = "Create async testing skill"
        mock_result.user_problem = ""
        mock_result.user_goals = []

        with patch.object(DeepUnderstandingModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = DeepUnderstandingModuleQA.__new__(DeepUnderstandingModuleQA)
            module.understand = MagicMock(return_value=mock_result)

            result = module.forward(
                initial_task="Create async testing skill",
                conversation_history=[],
                research_findings={},
            )

            # Verify research is parsed correctly
            assert result["research_needed"]["type"] == "web"
            assert result["research_needed"]["query"] == "async testing best practices pytest"

    def test_forward_ready_to_proceed(self, configured_dspy):
        """Test when readiness score >= 0.8 (ready to create skill)."""
        mock_result = MagicMock()
        mock_result.next_question = ""  # Empty when ready
        mock_result.reasoning = "Sufficient understanding gathered"
        mock_result.understanding_summary = "User needs reliable async tests for web applications"
        mock_result.readiness_score = 0.85
        mock_result.refined_task_description = "Create async testing skill for web apps"
        mock_result.user_problem = "Flaky async tests in web application testing"
        mock_result.user_goals = ["Reliable tests", "Better async patterns"]
        mock_result.research_needed = None

        with patch.object(DeepUnderstandingModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = DeepUnderstandingModuleQA.__new__(DeepUnderstandingModuleQA)
            module.understand = MagicMock(return_value=mock_result)

            result = module.forward(
                initial_task="Create async testing skill",
                conversation_history=[
                    {"question": "What's your problem?", "answer": "Flaky tests"},
                    {"question": "What framework?", "answer": "pytest"},
                ],
                research_findings={},
                current_understanding="User needs help with flaky tests",
            )

            # Should be ready to proceed
            assert result["readiness_score"] >= 0.8
            assert result["next_question"] is None  # No more questions needed


# =============================================================================
# AssessReadinessModule Tests
# =============================================================================


class TestAssessReadinessModule:
    """Tests for AssessReadinessModule using dspy.Predict."""

    def test_initialization(self):
        """Module should initialize with dspy.Predict."""
        module = AssessReadinessModule()
        assert isinstance(module.assess, dspy.Predict)

    def test_forward_ready_to_proceed(self, configured_dspy):
        """Test when sufficient information is gathered."""
        mock_result = MagicMock()
        mock_result.readiness_score = 0.85
        mock_result.readiness_reasoning = "Have 3 good examples and clear requirements"
        mock_result.should_proceed = True

        with patch.object(AssessReadinessModule, "__init__", lambda self: None):
            module = AssessReadinessModule.__new__(AssessReadinessModule)
            module.assess = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create async testing skill",
                examples=[{"input": "test async code", "output": "assertion"}],
                questions_asked=3,
            )

            assert result["readiness_score"] >= 0.8
            assert result["should_proceed"] is True

    def test_forward_not_ready(self, configured_dspy):
        """Test when more information is needed."""
        mock_result = MagicMock()
        mock_result.readiness_score = 0.5
        mock_result.readiness_reasoning = "Need more concrete examples of edge cases"
        mock_result.should_proceed = False

        with patch.object(AssessReadinessModule, "__init__", lambda self: None):
            module = AssessReadinessModule.__new__(AssessReadinessModule)
            module.assess = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create skill",
                examples=[],
                questions_asked=1,
            )

            assert result["readiness_score"] < 0.8
            assert result["should_proceed"] is False
            assert "edge cases" in result["readiness_reasoning"].lower()


# =============================================================================
# PresentSkillModuleQA Tests
# =============================================================================


class TestPresentSkillModuleQA:
    """Tests for PresentSkillModuleQA using MultiChainComparison."""

    def test_initialization(self):
        """Module should initialize with configurable n_candidates."""
        module = PresentSkillModuleQA(n_candidates=3)
        # Verify module has present attribute
        assert hasattr(module, "present")
        assert module.present is not None

    def test_forward_formats_conversationally(self, configured_dspy):
        """Test formatting skill results for conversational presentation."""
        mock_result = MagicMock()
        mock_result.conversational_summary = (
            "I've created an async testing skill that helps you write reliable tests."
        )
        mock_result.key_highlights = [
            "Supports pytest and asyncio",
            "Handles flaky tests",
            "Includes timeout patterns",
        ]
        mock_result.suggested_questions = [
            "Does this address your flaky test issues?",
            "Would you like more examples?",
        ]

        with patch.object(PresentSkillModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = PresentSkillModuleQA.__new__(PresentSkillModuleQA)
            module.present = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Async Testing Skill\n...",
                skill_metadata={"name": "async-testing"},
                validation_report={"passed": True},
            )

            assert "conversational_summary" in result
            assert len(result["key_highlights"]) == 3
            assert len(result["suggested_questions"]) == 2


# =============================================================================
# SuggestTestsModuleQA Tests
# =============================================================================


class TestSuggestTestsModuleQA:
    """Tests for SuggestTestsModuleQA using MultiChainComparison."""

    def test_initialization(self):
        """Module should initialize with configurable n_candidates."""
        module = SuggestTestsModuleQA(n_candidates=3)
        # Verify module has suggest attribute
        assert hasattr(module, "suggest")
        assert module.suggest is not None

    def test_forward_discipline_skill_scenarios(self, configured_dspy):
        """Test scenario generation for discipline skills."""
        mock_result = MagicMock()
        mock_result.test_scenarios = [
            "Time pressure + sunk cost + authority pressure",
            "Exhaustion + 'just this once' + complexity",
        ]
        mock_result.baseline_predictions = [
            "Agent skips testing and claims 'too simple to test'",
            "Agent rationalizes 'I'll test after' to avoid delay",
        ]
        mock_result.expected_rationalizations = [
            "'Just this once' exception",
            "'Too simple to test' claim",
        ]

        with patch.object(SuggestTestsModuleQA, "__init__", lambda self, n_candidates=3: None):
            module = SuggestTestsModuleQA.__new__(SuggestTestsModuleQA)
            module.suggest = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Test-Driven Development\n...",
                skill_type="discipline",
                skill_metadata={"name": "tdd-enforcement"},
            )

            assert len(result["test_scenarios"]) == 2
            assert len(result["baseline_predictions"]) == 2
            assert any("pressure" in s.lower() for s in result["test_scenarios"])


# =============================================================================
# VerifyTDDModule Tests
# =============================================================================


class TestVerifyTDDModule:
    """Tests for VerifyTDDModule using dspy.Predict."""

    def test_initialization(self):
        """Module should initialize with dspy.Predict."""
        module = VerifyTDDModule()
        assert isinstance(module.verify, dspy.Predict)

    def test_forward_all_passed(self, configured_dspy):
        """Test when TDD checklist is complete."""
        mock_result = MagicMock()
        mock_result.all_passed = True
        mock_result.missing_items = []
        mock_result.ready_to_save = True

        with patch.object(VerifyTDDModule, "__init__", lambda self: None):
            module = VerifyTDDModule.__new__(VerifyTDDModule)
            module.verify = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Complete skill\n...",
                checklist_state={
                    "red_scenarios_created": True,
                    "green_tests_run": True,
                    "refactor_complete": True,
                },
            )

            assert result["all_passed"] is True
            assert result["ready_to_save"] is True
            assert result["missing_items"] == []

    def test_forward_missing_items(self, configured_dspy):
        """Test when TDD checklist has missing items."""
        mock_result = MagicMock()
        mock_result.all_passed = False
        mock_result.missing_items = ["Baseline tests not run", "Rationalizations not identified"]
        mock_result.ready_to_save = False

        with patch.object(VerifyTDDModule, "__init__", lambda self: None):
            module = VerifyTDDModule.__new__(VerifyTDDModule)
            module.verify = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Incomplete skill\n...",
                checklist_state={
                    "red_scenarios_created": True,
                    "green_tests_run": False,
                    "refactor_complete": False,
                },
            )

            assert result["all_passed"] is False
            assert result["ready_to_save"] is False
            assert len(result["missing_items"]) == 2


# =============================================================================
# ConfirmUnderstandingModule Tests
# =============================================================================


class TestConfirmUnderstandingModule:
    """Tests for ConfirmUnderstandingModule using dspy.Predict."""

    def test_initialization(self):
        """Module should initialize with dspy.Predict."""
        module = ConfirmUnderstandingModule()
        assert isinstance(module.confirm, dspy.Predict)

    def test_forward_generates_confirmation(self, configured_dspy):
        """Test generation of confirmation message."""
        mock_result = MagicMock()
        mock_result.confirmation_summary = (
            "I'll create an async testing skill that helps with flaky tests."
        )
        mock_result.key_points = [
            "Skill name: async-testing-reliability",
            "Type: technique",
            "Main capability: Handles flaky async tests",
        ]
        mock_result.confirmation_question = "Does this look correct? (yes/no)"

        with patch.object(ConfirmUnderstandingModule, "__init__", lambda self: None):
            module = ConfirmUnderstandingModule.__new__(ConfirmUnderstandingModule)
            module.confirm = MagicMock(return_value=mock_result)

            result = module.forward(
                task_description="Create async testing skill",
                taxonomy_path="technical_skills/testing/async-testing",
                skill_metadata_draft={"name": "async-testing-reliability"},
                collected_examples=[],
            )

            assert result["confirmation_summary"] != ""
            assert len(result["key_points"]) == 3
            assert "correct" in result["confirmation_question"].lower()


# =============================================================================
# ProcessFeedbackModule Tests
# =============================================================================


class TestProcessFeedbackModule:
    """Tests for ProcessFeedbackModule using dspy.Predict."""

    def test_initialization(self):
        """Module should initialize with dspy.Predict."""
        module = ProcessFeedbackModule()
        assert isinstance(module.process, dspy.Predict)

    def test_forward_approve(self, configured_dspy):
        """Test processing approval feedback."""
        mock_result = MagicMock()
        mock_result.feedback_type = "approve"
        mock_result.revision_plan = ""
        mock_result.requires_regeneration = False

        with patch.object(ProcessFeedbackModule, "__init__", lambda self: None):
            module = ProcessFeedbackModule.__new__(ProcessFeedbackModule)
            module.process = MagicMock(return_value=mock_result)

            result = module.forward(
                user_feedback="Looks good, approve it",
                current_skill_content="# Skill content\n...",
                validation_errors=[],
            )

            assert result["feedback_type"] == "approve"
            assert result["requires_regeneration"] is False

    def test_forward_revision_request(self, configured_dspy):
        """Test processing revision request."""
        mock_result = MagicMock()
        mock_result.feedback_type = "revision_request"
        mock_result.revision_plan = "Add more examples for edge cases"
        mock_result.requires_regeneration = True

        with patch.object(ProcessFeedbackModule, "__init__", lambda self: None):
            module = ProcessFeedbackModule.__new__(ProcessFeedbackModule)
            module.process = MagicMock(return_value=mock_result)

            result = module.forward(
                user_feedback="Need more examples",
                current_skill_content="# Skill content\n...",
                validation_errors=[],
            )

            assert result["feedback_type"] == "revision_request"
            assert result["requires_regeneration"] is True
            assert "examples" in result["revision_plan"].lower()
