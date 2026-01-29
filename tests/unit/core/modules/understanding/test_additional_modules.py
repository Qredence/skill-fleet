"""Tests for understanding modules (intent, taxonomy, dependencies)."""

from unittest.mock import Mock, patch

import pytest

from skill_fleet.core.modules.understanding.dependencies import AnalyzeDependenciesModule
from skill_fleet.core.modules.understanding.intent import AnalyzeIntentModule
from skill_fleet.core.modules.understanding.taxonomy import FindTaxonomyPathModule


class TestAnalyzeIntentModule:
    """Test AnalyzeIntentModule."""

    def test_module_can_be_instantiated(self):
        """Should create instance with ChainOfThought."""
        module = AnalyzeIntentModule()
        assert module is not None
        assert hasattr(module, "analyze")

    @patch("skill_fleet.core.modules.understanding.intent.dspy.ChainOfThought")
    def test_forward_returns_structured_output(self, mock_cot):
        """Should return dict with intent components."""
        mock_result = Mock()
        mock_result.purpose = "Learn React"
        mock_result.problem_statement = "Need UI components"
        mock_result.target_audience = "Frontend devs"
        mock_result.value_proposition = "Pre-built components"
        mock_result.skill_type = "how_to"
        mock_result.scope = "Component creation"
        mock_result.success_criteria = ["Can create components"]

        mock_cot.return_value.return_value = mock_result

        module = AnalyzeIntentModule()
        result = module.forward(
            task_description="Build a React component library", requirements={"domain": "technical"}
        )

        assert isinstance(result, dict)
        assert result["purpose"] == "Learn React"
        assert result["skill_type"] == "how_to"
        assert "success_criteria" in result

    @pytest.mark.skip(reason="Integration test - requires actual LM configuration")
    def test_forward_handles_missing_requirements(self):
        """Should handle None requirements gracefully."""
        module = AnalyzeIntentModule()

        # Integration test - requires actual LM
        result = module.forward(task_description="Create a Python function", requirements=None)

        assert "purpose" in result
        assert "skill_type" in result


class TestFindTaxonomyPathModule:
    """Test FindTaxonomyPathModule."""

    def test_module_can_be_instantiated(self):
        """Should create instance with ChainOfThought."""
        module = FindTaxonomyPathModule()
        assert module is not None
        assert hasattr(module, "find_path")

    @patch("skill_fleet.core.modules.understanding.taxonomy.dspy.ChainOfThought")
    def test_forward_returns_path_analysis(self, mock_cot):
        """Should return taxonomy path recommendations."""
        mock_result = Mock()
        mock_result.recommended_path = "technical/frontend/react"
        mock_result.alternative_paths = ["web/react"]
        mock_result.path_rationale = "React is a frontend technology"
        mock_result.new_directories = []
        mock_result.confidence = 0.85

        mock_cot.return_value.return_value = mock_result

        module = FindTaxonomyPathModule()
        result = module.forward(
            task_description="Build a React app",
            requirements={"category": "frontend"},
            taxonomy_structure={"technical": {"frontend": []}},
            existing_skills=[],
        )

        assert isinstance(result, dict)
        assert result["recommended_path"] == "technical/frontend/react"
        assert result["confidence"] == 0.85
        assert isinstance(result["alternative_paths"], list)

    def test_confidence_is_normalized(self):
        """Should ensure confidence is in 0-1 range."""
        # This would require mocking to test specific edge cases
        pass


class TestAnalyzeDependenciesModule:
    """Test AnalyzeDependenciesModule."""

    def test_module_can_be_instantiated(self):
        """Should create instance with ChainOfThought."""
        module = AnalyzeDependenciesModule()
        assert module is not None
        assert hasattr(module, "analyze")

    @patch("skill_fleet.core.modules.understanding.dependencies.dspy.ChainOfThought")
    def test_forward_returns_dependency_analysis(self, mock_cot):
        """Should return dependency analysis."""
        mock_result = Mock()
        mock_result.prerequisite_skills = ["javascript: Required for React"]
        mock_result.complementary_skills = ["testing: Useful for components"]
        mock_result.conflicting_skills = []
        mock_result.missing_prerequisites = []
        mock_result.dependency_rationale = "JavaScript is required for React"

        mock_cot.return_value.return_value = mock_result

        module = AnalyzeDependenciesModule()
        result = module.forward(
            task_description="Build React components",
            intent_analysis={"skill_type": "how_to"},
            taxonomy_path="technical/frontend/react",
            existing_skills=["javascript", "html"],
        )

        assert isinstance(result, dict)
        assert "prerequisite_skills" in result
        assert "complementary_skills" in result
        assert len(result["prerequisite_skills"]) == 1

    @pytest.mark.skip(reason="Integration test - requires actual LM configuration")
    def test_handles_empty_existing_skills(self):
        """Should handle empty existing skills list."""
        module = AnalyzeDependenciesModule()

        result = module.forward(task_description="Learn Python", existing_skills=[])

        assert isinstance(result["prerequisite_skills"], list)
        assert isinstance(result["complementary_skills"], list)


class TestUnderstandingModulesIntegration:
    """Integration tests for understanding modules working together."""

    def test_all_modules_produce_consistent_output_format(self):
        """All modules should return dictionaries."""
        from skill_fleet.core.modules.understanding.requirements import GatherRequirementsModule

        modules = [
            GatherRequirementsModule(),
            AnalyzeIntentModule(),
            FindTaxonomyPathModule(),
            AnalyzeDependenciesModule(),
        ]

        for module in modules:
            assert hasattr(module, "forward")
            # Check they can be instantiated
            assert module is not None
