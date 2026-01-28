"""Tests for multi-select clarification questions."""

from skill_fleet.api.schemas.hitl import (
    StructuredQuestion,
    _dict_to_structured_question,
    normalize_questions,
)
from skill_fleet.core.dspy.utils.question_options import generate_smart_options


class TestGenerateSmartOptions:
    """Test smart options generation utility."""

    def test_programming_language_options(self):
        """Test domain-specific options for programming questions."""
        options, refined = generate_smart_options("Which programming language?")
        assert len(options) >= 3
        assert "Python" in options
        assert "Other" in options

    def test_typescript_programming_options(self):
        """Test TypeScript-specific options."""
        options, _ = generate_smart_options("Create a TypeScript skill")
        assert "TypeScript" in options
        assert "Other" in options

    def test_project_state_options(self):
        """Test domain-specific options for project questions."""
        options, _ = generate_smart_options("What is your project state?")
        text = " ".join(options).lower()
        assert "new" in text or "greenfield" in text
        assert "Other" in options

    def test_team_size_options(self):
        """Test domain-specific options for team questions."""
        options, _ = generate_smart_options("What is your team size?")
        assert len(options) >= 3
        assert any("solo" in o.lower() for o in options)
        assert "Other" in options

    def test_priority_options(self):
        """Test domain-specific options for priority questions."""
        options, _ = generate_smart_options("What is the priority?")
        assert len(options) >= 3
        assert any("high" in o.lower() for o in options)
        assert "Other" in options

    def test_experience_options(self):
        """Test domain-specific options for experience questions."""
        options, _ = generate_smart_options("What is your experience level?")
        assert len(options) >= 3
        assert any("beginner" in o.lower() or "learning" in o.lower() for o in options)
        assert "Other" in options

    def test_ci_cd_options(self):
        """Test domain-specific options for CI/CD questions."""
        options, _ = generate_smart_options("What CI/CD platform?")
        assert len(options) >= 3
        assert "GitHub Actions" in options or "GitHub" in " ".join(options)
        assert "Other" in options

    def test_fallback_options(self):
        """Test generic fallback for unknown domains."""
        options, _ = generate_smart_options("Some unknown question xyz?")
        assert len(options) >= 2
        assert "Other" in options

    def test_options_limit_to_5(self):
        """Test that options are limited to 2-5 items."""
        options, _ = generate_smart_options("What is your experience level?")
        assert 2 <= len(options) <= 5

    def test_refined_question_returned(self):
        """Test that refined question is returned for known domains."""
        options, refined = generate_smart_options("Which language?")
        # For programming questions, a refined question should be returned
        # This is optional but may be provided
        assert isinstance(refined, (str, type(None)))


class TestStructuredQuestionDefaults:
    """Test StructuredQuestion multi-select defaults."""

    def test_allows_multiple_defaults_to_true(self):
        """Test that allows_multiple defaults to True."""
        q = StructuredQuestion(text="Test question")
        assert q.allows_multiple is True

    def test_explicit_false_respected(self):
        """Test that explicit False is respected."""
        q = StructuredQuestion(text="Test", allows_multiple=False)
        assert q.allows_multiple is False

    def test_explicit_true_respected(self):
        """Test that explicit True is respected."""
        q = StructuredQuestion(text="Test", allows_multiple=True)
        assert q.allows_multiple is True


class TestSchemaNormalization:
    """Test schema normalization with multi-select."""

    def test_dict_without_allows_multiple_defaults_true(self):
        """Test that missing allows_multiple defaults to True."""
        data = {"text": "Test question", "options": [{"id": "a", "label": "A"}]}
        q = _dict_to_structured_question(data)
        assert q.allows_multiple is True

    def test_dict_with_explicit_false(self):
        """Test explicit allows_multiple=False is preserved."""
        data = {"text": "Test", "allows_multiple": False}
        q = _dict_to_structured_question(data)
        assert q.allows_multiple is False

    def test_dict_with_explicit_true(self):
        """Test explicit allows_multiple=True is preserved."""
        data = {"text": "Test", "allows_multiple": True}
        q = _dict_to_structured_question(data)
        assert q.allows_multiple is True

    def test_dict_with_options_and_allows_multiple(self):
        """Test full structured question with options."""
        data = {
            "text": "Select your options",
            "options": [
                {"id": "1", "label": "Option 1"},
                {"id": "2", "label": "Option 2"},
                {"id": "3", "label": "Other"},
            ],
            "allows_multiple": True,
        }
        q = _dict_to_structured_question(data)
        assert q.text == "Select your options"
        assert q.allows_multiple is True
        assert q.options is not None
        assert len(q.options) == 3
        assert q.options[0].label == "Option 1"

    def test_string_question_normalized(self):
        """Test that string questions are normalized with default multi-select."""
        result = normalize_questions("Single question?")
        assert len(result) == 1
        assert result[0].allows_multiple is True

    def test_list_of_string_questions_normalized(self):
        """Test that list of string questions are normalized."""
        result = normalize_questions(["Question 1?", "Question 2?"])
        assert len(result) == 2
        assert all(q.allows_multiple is True for q in result)

    def test_list_of_dict_questions_normalized(self):
        """Test that list of dict questions are normalized."""
        data = [
            {"text": "Q1", "allows_multiple": False},
            {"text": "Q2"},  # Should default to True
        ]
        result = normalize_questions(data)
        assert len(result) == 2
        assert result[0].allows_multiple is False
        assert result[1].allows_multiple is True


class TestMultiSelectEdgeCases:
    """Test edge cases for multi-select questions."""

    def test_empty_options_list(self):
        """Test question with empty options list."""
        q = StructuredQuestion(text="Test", options=[])
        assert q.options == []
        assert q.allows_multiple is True

    def test_none_options(self):
        """Test question with None options."""
        q = StructuredQuestion(text="Test", options=None)
        assert q.options is None
        assert q.allows_multiple is True

    def test_options_with_other(self):
        """Test that 'Other' option is included in generated options."""
        options, _ = generate_smart_options("What is your experience?")
        assert "Other" in options

    def test_single_option_fallback(self):
        """Test that single option is expanded with 'Other'."""
        # This is handled by generate_smart_options internally
        options, _ = generate_smart_options("Some question")
        # If the logic returns fewer than 2 options, it adds "Other"
        assert len(options) >= 2
