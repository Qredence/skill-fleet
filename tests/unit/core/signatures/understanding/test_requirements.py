"""Tests for understanding signatures."""

from skill_fleet.core.signatures.understanding.dependencies import AnalyzeDependencies
from skill_fleet.core.signatures.understanding.intent import AnalyzeIntent
from skill_fleet.core.signatures.understanding.requirements import GatherRequirements
from skill_fleet.core.signatures.understanding.taxonomy import FindTaxonomyPath


class TestGatherRequirements:
    """Test GatherRequirements signature."""

    def test_signature_has_correct_docstring(self):
        """Signature should have descriptive docstring."""
        assert GatherRequirements.__doc__ is not None
        assert "requirements" in GatherRequirements.__doc__.lower()

    def test_input_fields(self):
        """Should have task_description and user_context inputs."""
        fields = GatherRequirements.fields
        assert "task_description" in fields
        assert "user_context" in fields

    def test_output_fields(self):
        """Should have all required output fields."""
        fields = GatherRequirements.fields
        required_outputs = [
            "domain",
            "category",
            "target_level",
            "topics",
            "constraints",
            "ambiguities",
        ]
        for field in required_outputs:
            assert field in fields, f"Missing field: {field}"

    def test_domain_field_has_literal_type(self):
        """Domain field should be constrained to valid values."""
        field = GatherRequirements.fields["domain"]
        # Should be a Literal type with specific values
        assert "technical" in str(field.annotation)
        assert "cognitive" in str(field.annotation)


class TestAnalyzeIntent:
    """Test AnalyzeIntent signature."""

    def test_signature_structure(self):
        """Should have correct input/output structure."""
        assert "AnalyzeIntent" in AnalyzeIntent.__name__

        inputs = ["task_description", "requirements"]
        for inp in inputs:
            assert inp in AnalyzeIntent.fields

    def test_outputs_include_intent_components(self):
        """Should output intent analysis components."""
        outputs = [
            "purpose",
            "problem_statement",
            "target_audience",
            "value_proposition",
            "skill_type",
            "scope",
            "success_criteria",
        ]
        for output in outputs:
            assert output in AnalyzeIntent.fields


class TestFindTaxonomyPath:
    """Test FindTaxonomyPath signature."""

    def test_inputs_include_taxonomy_data(self):
        """Should require taxonomy structure and existing skills."""
        assert "taxonomy_structure" in FindTaxonomyPath.fields
        assert "existing_skills" in FindTaxonomyPath.fields

    def test_outputs_include_path_recommendations(self):
        """Should output path recommendations with confidence."""
        outputs = [
            "recommended_path",
            "alternative_paths",
            "path_rationale",
            "new_directories",
            "confidence",
        ]
        for output in outputs:
            assert output in FindTaxonomyPath.fields

    def test_confidence_is_float(self):
        """Confidence should be a float between 0 and 1."""
        field = FindTaxonomyPath.fields["confidence"]
        assert "float" in str(field.annotation)


class TestAnalyzeDependencies:
    """Test AnalyzeDependencies signature."""

    def test_inputs_require_intent_and_taxonomy(self):
        """Should require intent analysis and taxonomy path."""
        assert "intent_analysis" in AnalyzeDependencies.fields
        assert "taxonomy_path" in AnalyzeDependencies.fields

    def test_outputs_include_dependency_types(self):
        """Should output different types of dependencies."""
        outputs = [
            "prerequisite_skills",
            "complementary_skills",
            "conflicting_skills",
            "missing_prerequisites",
            "dependency_rationale",
        ]
        for output in outputs:
            assert output in AnalyzeDependencies.fields


class TestSignatureConsistency:
    """Test consistency across all understanding signatures."""

    def test_all_have_docstrings(self):
        """All signatures should have docstrings."""
        signatures = [GatherRequirements, AnalyzeIntent, FindTaxonomyPath, AnalyzeDependencies]
        for sig in signatures:
            assert sig.__doc__ is not None, f"{sig.__name__} missing docstring"

    def test_all_have_task_description_input(self):
        """All understanding signatures should take task_description."""
        signatures = [GatherRequirements, AnalyzeIntent, FindTaxonomyPath, AnalyzeDependencies]
        for sig in signatures:
            assert "task_description" in sig.fields, f"{sig.__name__} missing task_description"
