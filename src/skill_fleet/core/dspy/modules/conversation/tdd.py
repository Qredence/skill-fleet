"""TDD workflow modules."""

from __future__ import annotations

import json
import logging

import dspy

from .....common.utils import safe_json_loads
from ...signatures.conversational_interface import (
    EnhanceSkillContent,
    SuggestTestScenarios,
    VerifyTDDPassed,
)

logger = logging.getLogger(__name__)


class SuggestTestsModule(dspy.Module):
    """Module for suggesting test scenarios using MultiChainComparison."""

    def __init__(self, n_candidates: int = 3):
        super().__init__()
        self.suggest = dspy.ChainOfThought(SuggestTestScenarios)

    def forward(
        self,
        skill_content: str,
        skill_type: str,
        skill_metadata: dict | str,
    ) -> dspy.Prediction:
        """Suggest test scenarios for a skill.

        Args:
            skill_content: The skill content to generate tests for.
            skill_type: The type of skill being tested.
            skill_metadata: Metadata about the skill.

        Returns:
            Prediction with test_scenarios, baseline_predictions, and expected_rationalizations.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )

        result = self.suggest(
            skill_content=skill_content,
            skill_type=skill_type,
            skill_metadata=metadata_str,
        )

        scenarios = safe_json_loads(
            getattr(result, "test_scenarios", []), default=[], field_name="test_scenarios"
        )
        if isinstance(scenarios, dict):
            scenarios = []
        if not isinstance(scenarios, list):
            scenarios = [str(scenarios)] if scenarios else []

        predictions = safe_json_loads(
            getattr(result, "baseline_predictions", []),
            default=[],
            field_name="baseline_predictions",
        )
        if isinstance(predictions, dict):
            predictions = []
        if not isinstance(predictions, list):
            predictions = [str(predictions)] if predictions else []

        rationalizations = safe_json_loads(
            getattr(result, "expected_rationalizations", []),
            default=[],
            field_name="expected_rationalizations",
        )
        if isinstance(rationalizations, dict):
            rationalizations = []
        if not isinstance(rationalizations, list):
            rationalizations = [str(rationalizations)] if rationalizations else []

        return dspy.Prediction(
            test_scenarios=scenarios,
            baseline_predictions=predictions,
            expected_rationalizations=rationalizations,
        )

    async def aforward(
        self,
        skill_content: str,
        skill_type: str,
        skill_metadata: dict | str,
    ) -> dspy.Prediction:
        """Async version of forward - suggest test scenarios for a skill.

        Args:
            skill_content: The skill content to generate tests for.
            skill_type: The type of skill being tested.
            skill_metadata: Metadata about the skill.

        Returns:
            Prediction with test_scenarios, baseline_predictions, and expected_rationalizations.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )

        result = await self.suggest.acall(
            skill_content=skill_content,
            skill_type=skill_type,
            skill_metadata=metadata_str,
        )

        scenarios = safe_json_loads(
            getattr(result, "test_scenarios", []), default=[], field_name="test_scenarios"
        )
        if isinstance(scenarios, dict):
            scenarios = []
        if not isinstance(scenarios, list):
            scenarios = [str(scenarios)] if scenarios else []

        predictions = safe_json_loads(
            getattr(result, "baseline_predictions", []),
            default=[],
            field_name="baseline_predictions",
        )
        if isinstance(predictions, dict):
            predictions = []
        if not isinstance(predictions, list):
            predictions = [str(predictions)] if predictions else []

        rationalizations = safe_json_loads(
            getattr(result, "expected_rationalizations", []),
            default=[],
            field_name="expected_rationalizations",
        )
        if isinstance(rationalizations, dict):
            rationalizations = []
        if not isinstance(rationalizations, list):
            rationalizations = [str(rationalizations)] if rationalizations else []

        return dspy.Prediction(
            test_scenarios=scenarios,
            baseline_predictions=predictions,
            expected_rationalizations=rationalizations,
        )


class VerifyTDDModule(dspy.Module):
    """Module for verifying TDD checklist completion using dspy.Predict."""

    def __init__(self):
        super().__init__()
        self.verify = dspy.Predict(VerifyTDDPassed)

    def forward(
        self,
        skill_content: str,
        checklist_state: dict | str,
    ) -> dspy.Prediction:
        """Verify TDD checklist completion.

        Args:
            skill_content: The skill content to verify.
            checklist_state: Current state of the TDD checklist.

        Returns:
            Prediction with all_passed, missing_items, and ready_to_save.
        """
        checklist_str = (
            json.dumps(checklist_state, indent=2)
            if isinstance(checklist_state, dict)
            else checklist_state
        )

        result = self.verify(
            skill_content=skill_content,
            checklist_state=checklist_str,
        )

        missing = safe_json_loads(
            getattr(result, "missing_items", []), default=[], field_name="missing_items"
        )
        if isinstance(missing, dict):
            missing = []
        if not isinstance(missing, list):
            missing = [str(missing)] if missing else []

        return dspy.Prediction(
            all_passed=bool(getattr(result, "all_passed", False)),
            missing_items=missing,
            ready_to_save=bool(getattr(result, "ready_to_save", False)),
        )

    async def aforward(
        self,
        skill_content: str,
        checklist_state: dict | str,
    ) -> dspy.Prediction:
        """Async version of forward - verify TDD checklist completion.

        Args:
            skill_content: The skill content to verify.
            checklist_state: Current state of the TDD checklist.

        Returns:
            Prediction with all_passed, missing_items, and ready_to_save.
        """
        checklist_str = (
            json.dumps(checklist_state, indent=2)
            if isinstance(checklist_state, dict)
            else checklist_state
        )

        result = await self.verify.acall(
            skill_content=skill_content,
            checklist_state=checklist_str,
        )

        missing = safe_json_loads(
            getattr(result, "missing_items", []), default=[], field_name="missing_items"
        )
        if isinstance(missing, dict):
            missing = []
        if not isinstance(missing, list):
            missing = [str(missing)] if missing else []

        return dspy.Prediction(
            all_passed=bool(getattr(result, "all_passed", False)),
            missing_items=missing,
            ready_to_save=bool(getattr(result, "ready_to_save", False)),
        )


class EnhanceSkillModule(dspy.Module):
    """Module for adding missing sections to skill content."""

    def __init__(self):
        super().__init__()
        self.enhance = dspy.ChainOfThought(EnhanceSkillContent)

    def forward(
        self,
        skill_content: str,
        missing_sections: list[str],
        skill_metadata: dict | str,
    ) -> dspy.Prediction:
        """Enhance skill content by adding missing sections.

        Args:
            skill_content: The current skill content.
            missing_sections: List of section names to add.
            skill_metadata: Metadata about the skill.

        Returns:
            Prediction with enhanced_content, sections_added, and enhancement_notes.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )

        result = self.enhance(
            skill_content=skill_content,
            missing_sections=missing_sections,
            skill_metadata=metadata_str,
        )

        sections_added = safe_json_loads(
            getattr(result, "sections_added", []), default=[], field_name="sections_added"
        )
        if isinstance(sections_added, dict):
            sections_added = []
        if not isinstance(sections_added, list):
            sections_added = [str(sections_added)] if sections_added else []

        return dspy.Prediction(
            enhanced_content=getattr(result, "enhanced_content", skill_content),
            sections_added=sections_added,
            enhancement_notes=getattr(result, "enhancement_notes", ""),
        )

    async def aforward(
        self,
        skill_content: str,
        missing_sections: list[str],
        skill_metadata: dict | str,
    ) -> dspy.Prediction:
        """Async version of forward - enhance skill content by adding missing sections.

        Args:
            skill_content: The current skill content.
            missing_sections: List of section names to add.
            skill_metadata: Metadata about the skill.

        Returns:
            Prediction with enhanced_content, sections_added, and enhancement_notes.
        """
        metadata_str = (
            json.dumps(skill_metadata, indent=2)
            if isinstance(skill_metadata, dict)
            else skill_metadata
        )

        result = await self.enhance.acall(
            skill_content=skill_content,
            missing_sections=missing_sections,
            skill_metadata=metadata_str,
        )

        sections_added = safe_json_loads(
            getattr(result, "sections_added", []), default=[], field_name="sections_added"
        )
        if isinstance(sections_added, dict):
            sections_added = []
        if not isinstance(sections_added, list):
            sections_added = [str(sections_added)] if sections_added else []

        return dspy.Prediction(
            enhanced_content=getattr(result, "enhanced_content", skill_content),
            sections_added=sections_added,
            enhancement_notes=getattr(result, "enhancement_notes", ""),
        )
