"""Tests for HITL signatures."""

from skill_fleet.core.signatures.hitl.questions import GenerateClarifyingQuestions


class TestGenerateClarifyingQuestions:
    """Test GenerateClarifyingQuestions signature."""

    def test_signature_has_correct_docstring(self):
        """Should describe the HITL question generation purpose."""
        assert GenerateClarifyingQuestions.__doc__ is not None
        assert "clarifying" in GenerateClarifyingQuestions.__doc__.lower()

    def test_input_fields(self):
        """Should have correct input fields."""
        fields = GenerateClarifyingQuestions.fields
        assert "task_description" in fields
        assert "ambiguities" in fields
        assert "initial_analysis" in fields
        assert "previous_answers" in fields

    def test_output_fields(self):
        """Should output questions with metadata."""
        fields = GenerateClarifyingQuestions.fields
        assert "questions" in fields
        assert "priority" in fields
        assert "rationale" in fields

    def test_questions_field_is_list_of_dicts(self):
        """Questions should be a list of structured question dicts."""
        field = GenerateClarifyingQuestions.fields["questions"]
        # Should be list[dict] type
        assert "list" in str(field.annotation)
        assert "dict" in str(field.annotation)

    def test_priority_has_expected_values(self):
        """Priority field should describe level enum."""
        field = GenerateClarifyingQuestions.fields["priority"]
        json_extra = getattr(field, "json_schema_extra", None)
        desc = ""
        if isinstance(json_extra, dict):
            desc = str(json_extra.get("desc", "")).lower()
        if not desc:
            desc = str(field).lower()
        assert "critical" in desc or "important" in desc or "optional" in desc


class TestHITLSignatureConsistency:
    """Test HITL signatures follow conventions."""

    def test_hitl_signatures_focus_on_interaction(self):
        """HITL signatures should focus on user interaction."""
        # This test ensures we're creating the right type of signatures
        sig = GenerateClarifyingQuestions
        desc = (sig.__doc__ or "").lower()
        assert any(word in desc for word in ["question", "clarify", "user", "interaction"])
