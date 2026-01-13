"""Unit tests for the reworked core layer.

Tests signatures, modules, and programs using mocks for DSPy calls.
"""

import unittest
from unittest.mock import MagicMock, patch

import dspy

from skill_fleet.core.dspy.modules import RequirementsGathererModule
from skill_fleet.core.dspy.signatures.phase1_understanding import GatherRequirements
from skill_fleet.core.models import SkillCreationResult, SkillMetadata


class TestCoreLayer(unittest.TestCase):
    """Test cases for the core layer components."""

    def setUp(self):
        """Set up test environment."""
        # Configure dummy LM for DSPy
        self.lm = dspy.LM("openai/gpt-4o-mini")
        dspy.settings.configure(lm=self.lm)

    def test_gather_requirements_signature(self):
        """Test GatherRequirements signature structure."""
        # Just verify fields exist
        self.assertIn("task_description", GatherRequirements.input_fields)
        self.assertIn("domain", GatherRequirements.output_fields)
        self.assertIn("ambiguities", GatherRequirements.output_fields)

    @patch("dspy.ChainOfThought.__call__")
    def test_requirements_gatherer_module(self, mock_call):
        """Test RequirementsGathererModule logic."""
        # Mock DSPy response
        mock_response = MagicMock()
        mock_response.domain = "technical"
        mock_response.category = "programming"
        mock_response.target_level = "intermediate"
        mock_response.topics = ["asyncio", "coroutines"]
        mock_response.constraints = []
        mock_response.ambiguities = ["Should we include networking?"]
        mock_response.rationale = "Task mentions async."
        mock_call.return_value = mock_response

        module = RequirementsGathererModule()
        result = module.forward("Create a Python async skill")

        self.assertEqual(result["domain"], "technical")
        self.assertEqual(result["category"], "programming")
        self.assertIn("networking", result["ambiguities"][0])

    def test_skill_creation_result_model(self):
        """Test SkillCreationResult Pydantic model."""
        metadata = SkillMetadata(
            skill_id="test/skill",
            name="test-skill",
            description="A test skill",
            type="technical",
            weight="lightweight",
            taxonomy_path="technical/test",
        )
        result = SkillCreationResult(
            status="completed", skill_content="# Test Content", metadata=metadata
        )
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.metadata.name, "test-skill")


if __name__ == "__main__":
    unittest.main()
