"""Unit tests for SignatureTuner module.

Tests for metric-driven signature tuning system including:
- SignatureVersion and SignatureVersionHistory dataclasses
- FailureAnalyzerModule (analyzes quality failures)
- SignatureProposerModule (proposes improvements)
- SignatureValidatorModule (validates proposals)
- SignatureTuner (main orchestrator)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import dspy
import pytest

from skill_fleet.core.dspy.modules.signature_tuner import (
    FailureAnalyzerModule,
    SignatureProposerModule,
    SignatureTuner,
    SignatureValidatorModule,
    SignatureVersion,
    SignatureVersionHistory,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_lm() -> MagicMock:
    """Create a mock DSPy LM."""
    lm = MagicMock(spec=dspy.LM)
    lm.history = []
    return lm


@pytest.fixture
def configured_dspy(mock_lm: MagicMock) -> MagicMock:
    """Configure DSPy with mock LM."""
    with dspy.context(lm=mock_lm):
        yield mock_lm


@pytest.fixture
def sample_skill_content() -> str:
    """Sample skill content for testing."""
    return """# Example Skill

## Core Principle
This is the main idea.

## Examples
- Example 1
- Example 2
"""


@pytest.fixture
def sample_failure_analysis() -> dict[str, object]:
    """Sample failure analysis dict."""
    return {
        "failure_categories": ["missing_structure"],
        "root_causes": ["No clear sections"],
        "missing_quality_indicators": ["iron_law"],
        "improvement_directions": ["Add sections"],
        "priority_fixes": ["Fix structure"],
    }


@pytest.fixture
def sample_proposal() -> dict[str, object]:
    """Sample proposal result."""
    return {
        "improved_signature": "question -> rationale, answer",
        "improvement_reasoning": "Added rationale field",
        "expected_impact": "+0.10 to +0.15",
        "changes_made": ["Added rationale constraint"],
        "confidence": 0.85,
    }


@pytest.fixture
def sample_validation() -> dict[str, object]:
    """Sample validation result."""
    return {
        "is_valid": True,
        "is_improvement": True,
        "validation_notes": "Looks good",
        "potential_issues": [],
        "recommendation": "approve",
    }


# =============================================================================
# Test SignatureVersion
# =============================================================================


class TestSignatureVersion:
    """Test SignatureVersion dataclass."""

    def test_initialization(self) -> None:
        """Verify all fields set correctly."""
        version = SignatureVersion(
            version=1,
            signature_text="question -> answer",
            metric_score=0.75,
            tuning_reason="Initial",
        )
        assert version.version == 1
        assert version.signature_text == "question -> answer"
        assert version.metric_score == 0.75
        assert version.tuning_reason == "Initial"
        assert version.improvement_from_previous == 0.0
        assert version.optimizer_used == "signature_tuner"

    def test_hash_generation(self) -> None:
        """Verify SHA256 hash generated from signature_text."""
        version = SignatureVersion(
            version=1,
            signature_text="question -> answer",
            metric_score=0.75,
            tuning_reason="Initial",
        )
        assert len(version.hash) == 12  # First 12 chars of SHA256
        assert version.hash  # Not empty

    def test_to_dict(self) -> None:
        """Verify serialization includes all fields."""
        version = SignatureVersion(
            version=2,
            signature_text="question -> answer",
            metric_score=0.80,
            tuning_reason="Improved",
            improvement_from_previous=0.05,
        )
        d = version.to_dict()
        assert d["version"] == 2
        assert d["signature_text"] == "question -> answer"
        assert d["metric_score"] == 0.80
        assert d["tuning_reason"] == "Improved"
        assert d["improvement_from_previous"] == 0.05

    def test_from_dict(self) -> None:
        """Verify deserialization reconstructs object."""
        data = {
            "version": 1,
            "signature_text": "question -> answer",
            "metric_score": 0.75,
            "tuning_reason": "Initial",
            "created_at": "2025-01-21T12:00:00+00:00",
            "improvement_from_previous": 0.0,
            "optimizer_used": "signature_tuner",
            "hash": "abc123",
        }
        version = SignatureVersion.from_dict(data)
        assert version.version == 1
        assert version.signature_text == "question -> answer"
        assert version.metric_score == 0.75
        assert version.tuning_reason == "Initial"

    def test_improvement_calculation(self) -> None:
        """Verify improvement_from_previous can be set."""
        version = SignatureVersion(
            version=2,
            signature_text="question -> answer",
            metric_score=0.85,
            tuning_reason="Improved",
            improvement_from_previous=0.10,
        )
        assert version.improvement_from_previous == 0.10


# =============================================================================
# Test SignatureVersionHistory
# =============================================================================


class TestSignatureVersionHistory:
    """Test version history management."""

    def test_initialization(self) -> None:
        """Verify empty history starts correctly."""
        history = SignatureVersionHistory(signature_id="test_sig")
        assert history.signature_id == "test_sig"
        assert history.versions == []
        assert history.current_version == 0

    def test_add_version_first(self) -> None:
        """First version gets v=1."""
        history = SignatureVersionHistory(signature_id="test_sig")
        version = history.add_version(
            signature_text="sig",
            metric_score=0.7,
            tuning_reason="test",
        )
        assert version.version == 1
        assert history.current_version == 1
        assert len(history.versions) == 1

    def test_add_version_incremental(self) -> None:
        """Subsequent versions increment correctly."""
        history = SignatureVersionHistory(signature_id="test_sig")
        history.add_version("sig1", 0.7, "test")
        history.add_version("sig2", 0.8, "test2")
        history.add_version("sig3", 0.9, "test3")
        assert history.current_version == 3
        assert len(history.versions) == 3

    def test_get_latest(self) -> None:
        """Returns most recent version."""
        history = SignatureVersionHistory(signature_id="test")
        history.add_version("sig1", 0.7, "test")
        history.add_version("sig2", 0.8, "test")
        latest = history.get_latest()
        assert latest is not None
        assert latest.version == 2
        assert latest.signature_text == "sig2"

    def test_get_best(self) -> None:
        """Returns version with highest metric_score."""
        history = SignatureVersionHistory(signature_id="test")
        history.add_version("sig1", 0.7, "test")
        history.add_version("sig2", 0.9, "test")
        history.add_version("sig3", 0.8, "test")
        best = history.get_best()
        assert best is not None
        assert best.metric_score == 0.9
        assert best.signature_text == "sig2"

    def test_save_and_load(self, tmp_path: Path) -> None:
        """JSON persistence works."""
        history = SignatureVersionHistory(signature_id="test")
        history.add_version("sig1", 0.7, "test")
        history.add_version("sig2", 0.8, "test")

        save_path = tmp_path / "history.json"
        history.save(save_path)

        loaded = SignatureVersionHistory.load(save_path)
        assert loaded.signature_id == "test"
        assert len(loaded.versions) == 2

    def test_to_dict_from_dict(self) -> None:
        """Round-trip serialization."""
        history = SignatureVersionHistory(signature_id="test")
        history.add_version("sig1", 0.7, "test")

        d = history.to_dict()
        assert d["signature_id"] == "test"
        assert d["current_version"] == 1
        assert len(d["versions"]) == 1

        restored = SignatureVersionHistory.from_dict(d)
        assert restored.signature_id == "test"
        assert len(restored.versions) == 1


# =============================================================================
# Test FailureAnalyzerModule
# =============================================================================


class TestFailureAnalyzerModule:
    """Tests for FailureAnalyzerModule using ChainOfThought."""

    def test_initialization(self) -> None:
        """Verifies ChainOfThought module initialized."""
        module = FailureAnalyzerModule()
        assert hasattr(module, "analyze")
        # Note: We don't check the exact type to avoid triggering DSPy initialization

    def test_forward_basic_case(self, configured_dspy: MagicMock) -> None:
        """Returns dict with all expected keys."""
        mock_result = MagicMock()
        mock_result.failure_categories = ["missing_structure", "weak_guidance"]
        mock_result.root_causes = ["Signature lacks instruction..."]
        mock_result.missing_quality_indicators = ["core_principle"]
        mock_result.improvement_directions = ["Add core principle constraint"]
        mock_result.priority_fixes = ["Fix 1", "Fix 2"]
        mock_result.rationale = "Analysis complete"

        with patch.object(FailureAnalyzerModule, "__init__", lambda self: None):
            module = FailureAnalyzerModule.__new__(FailureAnalyzerModule)
            module.analyze = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
                quality_issues=["Missing core principle"],
            )

            assert "failure_categories" in result
            assert result["failure_categories"] == ["missing_structure", "weak_guidance"]
            assert result["root_causes"] == ["Signature lacks instruction..."]

    def test_forward_with_empty_issues(self, configured_dspy: MagicMock) -> None:
        """Handles empty quality_issues list."""
        mock_result = MagicMock()
        mock_result.failure_categories = []
        mock_result.root_causes = []
        mock_result.missing_quality_indicators = []
        mock_result.improvement_directions = []
        mock_result.priority_fixes = []

        with patch.object(FailureAnalyzerModule, "__init__", lambda self: None):
            module = FailureAnalyzerModule.__new__(FailureAnalyzerModule)
            module.analyze = MagicMock(return_value=mock_result)

            result = module.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
                quality_issues=[],
            )

            assert result["failure_categories"] == []
            assert result["root_causes"] == []

    def test_forward_calls_analyze(self, configured_dspy: MagicMock) -> None:
        """Verify underlying DSPy module called correctly."""
        mock_result = MagicMock()
        mock_result.failure_categories = ["missing_structure"]
        mock_result.root_causes = ["Test"]
        mock_result.missing_quality_indicators = []
        mock_result.improvement_directions = []
        mock_result.priority_fixes = []

        with patch.object(FailureAnalyzerModule, "__init__", lambda self: None):
            module = FailureAnalyzerModule.__new__(FailureAnalyzerModule)
            module.analyze = MagicMock(return_value=mock_result)

            module.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
                quality_issues=["Issue"],
            )

            module.analyze.assert_called_once()
            call_kwargs = module.analyze.call_args.kwargs
            assert call_kwargs["skill_content"] == "# Skill"
            assert call_kwargs["metric_score"] == 0.65


# =============================================================================
# Test SignatureProposerModule
# =============================================================================


class TestSignatureProposerModule:
    """Tests for SignatureProposerModule using ChainOfThought."""

    def test_initialization(self) -> None:
        """Verifies ChainOfThought module initialized."""
        module = SignatureProposerModule()
        assert hasattr(module, "propose")

    def test_forward_basic_case(self, configured_dspy: MagicMock) -> None:
        """Returns improved_signature with metadata."""
        mock_result = MagicMock()
        mock_result.improved_signature = "question -> rationale, answer"
        mock_result.improvement_reasoning = "Added rationale"
        mock_result.expected_impact = "+0.10"
        mock_result.changes_made = ["Added rationale"]
        mock_result.confidence = 0.85
        mock_result.rationale = "Proposed"

        with patch.object(SignatureProposerModule, "__init__", lambda self: None):
            module = SignatureProposerModule.__new__(SignatureProposerModule)
            module.propose = MagicMock(return_value=mock_result)

            result = module.forward(
                current_signature="question -> answer",
                failure_analysis={"failure_categories": ["missing_structure"]},
                target_score=0.80,
                skill_type="comprehensive",
            )

            assert result["improved_signature"] == "question -> rationale, answer"
            assert result["confidence"] == 0.85

    def test_forward_all_skill_types(self, configured_dspy: MagicMock) -> None:
        """Works with navigation_hub, comprehensive, minimal."""
        mock_result = MagicMock()
        mock_result.improved_signature = "question -> answer"
        mock_result.improvement_reasoning = "test"
        mock_result.expected_impact = "+0.05"
        mock_result.changes_made = []
        mock_result.confidence = 0.7
        mock_result.rationale = "test"

        with patch.object(SignatureProposerModule, "__init__", lambda self: None):
            module = SignatureProposerModule.__new__(SignatureProposerModule)
            module.propose = MagicMock(return_value=mock_result)

            for skill_type in ["navigation_hub", "comprehensive", "minimal"]:
                result = module.forward(
                    current_signature="question -> answer",
                    failure_analysis={},
                    target_score=0.80,
                    skill_type=skill_type,  # type: ignore
                )
                assert result["improved_signature"] == "question -> answer"

    def test_forward_json_serialization(self, configured_dspy: MagicMock) -> None:
        """Handles JSON failure_analysis input."""
        mock_result = MagicMock()
        mock_result.improved_signature = "question -> answer"
        mock_result.improvement_reasoning = "test"
        mock_result.expected_impact = "+0.05"
        mock_result.changes_made = []
        mock_result.confidence = 0.7
        mock_result.rationale = "test"

        with patch.object(SignatureProposerModule, "__init__", lambda self: None):
            module = SignatureProposerModule.__new__(SignatureProposerModule)
            module.propose = MagicMock(return_value=mock_result)

            failure_analysis = {"categories": ["missing"]}
            module.forward(
                current_signature="question -> answer",
                failure_analysis=failure_analysis,
                target_score=0.80,
                skill_type="comprehensive",
            )

            # Verify the call was made with JSON-serialized analysis
            module.propose.assert_called_once()
            call_kwargs = module.propose.call_args.kwargs
            # The failure_analysis should be JSON-serialized
            assert "failure_analysis" in call_kwargs


# =============================================================================
# Test SignatureValidatorModule
# =============================================================================


class TestSignatureValidatorModule:
    """Tests for SignatureValidatorModule using Predict."""

    def test_initialization(self) -> None:
        """Verifies Predict module (not ChainOfThought)."""
        module = SignatureValidatorModule()
        assert hasattr(module, "validate")

    def test_forward_approve(self, configured_dspy: MagicMock) -> None:
        """Returns recommendation='approve' for good proposal."""
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.is_improvement = True
        mock_result.validation_notes = "Looks good"
        mock_result.potential_issues = []
        mock_result.recommendation = "approve"

        with patch.object(SignatureValidatorModule, "__init__", lambda self: None):
            module = SignatureValidatorModule.__new__(SignatureValidatorModule)
            module.validate = MagicMock(return_value=mock_result)

            result = module.forward(
                original_signature="question -> answer",
                proposed_signature="question -> rationale, answer",
                improvement_reasoning="Added rationale",
            )

            assert result["is_valid"] is True
            assert result["recommendation"] == "approve"

    def test_forward_reject(self, configured_dspy: MagicMock) -> None:
        """Returns recommendation='reject' for bad proposal."""
        mock_result = MagicMock()
        mock_result.is_valid = False
        mock_result.is_improvement = False
        mock_result.validation_notes = "Invalid syntax"
        mock_result.potential_issues = ["Syntax error"]
        mock_result.recommendation = "reject"

        with patch.object(SignatureValidatorModule, "__init__", lambda self: None):
            module = SignatureValidatorModule.__new__(SignatureValidatorModule)
            module.validate = MagicMock(return_value=mock_result)

            result = module.forward(
                original_signature="question -> answer",
                proposed_signature="invalid signature",
                improvement_reasoning="Test",
            )

            assert result["is_valid"] is False
            assert result["recommendation"] == "reject"

    def test_forward_caution(self, configured_dspy: MagicMock) -> None:
        """Returns 'approve_with_caution' for uncertain."""
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.is_improvement = True
        mock_result.validation_notes = "Minor concern"
        mock_result.potential_issues = ["May affect compatibility"]
        mock_result.recommendation = "approve_with_caution"

        with patch.object(SignatureValidatorModule, "__init__", lambda self: None):
            module = SignatureValidatorModule.__new__(SignatureValidatorModule)
            module.validate = MagicMock(return_value=mock_result)

            result = module.forward(
                original_signature="question -> answer",
                proposed_signature="question -> answer",
                improvement_reasoning="Minor change",
            )

            assert result["recommendation"] == "approve_with_caution"


# =============================================================================
# Test SignatureTuner
# =============================================================================


class TestSignatureTuner:
    """Tests for SignatureTuner orchestrator."""

    def test_initialization_defaults(self) -> None:
        """Default parameters set correctly."""
        tuner = SignatureTuner()
        assert tuner.improvement_threshold == 0.05
        assert tuner.max_iterations == 3
        assert tuner.quality_threshold == 0.75

    def test_initialization_custom_params(self) -> None:
        """Custom parameters override defaults."""
        tuner = SignatureTuner(
            improvement_threshold=0.10,
            max_iterations=5,
            quality_threshold=0.80,
        )
        assert tuner.improvement_threshold == 0.10
        assert tuner.max_iterations == 5
        assert tuner.quality_threshold == 0.80

    def test_forward_no_tuning_needed(self, configured_dspy: MagicMock) -> None:
        """Score >= quality_threshold returns early."""
        tuner = SignatureTuner(quality_threshold=0.75)

        result = tuner.forward(
            skill_content="# Good skill",
            current_signature="question -> answer",
            metric_score=0.80,
        )

        assert result["tuning_needed"] is False
        assert "meets threshold" in result["reason"]

    def test_forward_quality_extraction_fallback(self, configured_dspy: MagicMock) -> None:
        """Handles assess_skill_quality failure gracefully."""
        # Mock the modules
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Mock assess_skill_quality to raise exception
            with patch(
                "skill_fleet.core.dspy.modules.signature_tuner.assess_skill_quality",
                side_effect=Exception("Quality assessment failed"),
            ):
                # Mock the sub-modules with proper return values
                mock_analysis = {"root_causes": ["test"], "failure_categories": []}
                mock_proposal = {
                    "improved_signature": "question -> answer",
                    "improvement_reasoning": "test",
                    "expected_impact": "+0.05",
                    "changes_made": [],
                    "confidence": 0.7,  # Must be a number, not MagicMock
                }
                mock_validation = {
                    "is_valid": True,
                    "is_improvement": True,
                    "validation_notes": "Good",
                    "potential_issues": [],
                    "recommendation": "approve",
                }

                tuner.failure_analyzer = MagicMock(return_value=mock_analysis)
                tuner.signature_proposer = MagicMock(return_value=mock_proposal)
                tuner.signature_validator = MagicMock(return_value=mock_validation)

                tuner.forward(
                    skill_content="# Skill",
                    current_signature="question -> answer",
                    metric_score=0.65,
                )

                # Should proceed with empty quality_issues (logged warning)
                tuner.failure_analyzer.assert_called_once()

    def test_forward_accept_improvement(
        self, configured_dspy: MagicMock, sample_proposal: dict[str, object]
    ) -> None:
        """Accepts when valid+improvement+confidence>=0.6."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Setup mocks for acceptance
            mock_analysis = {"root_causes": ["test"]}
            tuner.failure_analyzer = MagicMock(return_value=mock_analysis)
            tuner.signature_proposer = MagicMock(return_value=sample_proposal)
            tuner.signature_validator = MagicMock(
                return_value={
                    "is_valid": True,
                    "is_improvement": True,
                    "validation_notes": "Good",
                    "potential_issues": [],
                    "recommendation": "approve",
                }
            )

            result = tuner.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
            )

            assert result["accept_improvement"] is True
            assert "new_version" in result

    def test_forward_reject_improvement(self, configured_dspy: MagicMock) -> None:
        """Rejects when confidence < 0.6."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            mock_analysis = {"root_causes": ["test"]}
            low_confidence_proposal = {
                "improved_signature": "question -> answer",
                "improvement_reasoning": "test",
                "expected_impact": "+0.02",
                "changes_made": [],
                "confidence": 0.5,  # Below threshold
            }

            tuner.failure_analyzer = MagicMock(return_value=mock_analysis)
            tuner.signature_proposer = MagicMock(return_value=low_confidence_proposal)
            tuner.signature_validator = MagicMock(
                return_value={
                    "is_valid": True,
                    "is_improvement": True,
                    "validation_notes": "Low confidence",
                    "potential_issues": [],
                    "recommendation": "approve",
                }
            )

            result = tuner.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
            )

            assert result["accept_improvement"] is False

    def test_forward_version_tracking(
        self, configured_dspy: MagicMock, sample_proposal: dict[str, object]
    ) -> None:
        """New version added when improvement accepted."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            mock_analysis = {"root_causes": ["test"]}
            tuner.failure_analyzer = MagicMock(return_value=mock_analysis)
            tuner.signature_proposer = MagicMock(return_value=sample_proposal)
            tuner.signature_validator = MagicMock(
                return_value={
                    "is_valid": True,
                    "is_improvement": True,
                    "validation_notes": "Good",
                    "potential_issues": [],
                    "recommendation": "approve",
                }
            )

            result = tuner.forward(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                signature_id="test_sig",
            )

            assert "new_version" in result
            assert result["new_version"]["version"] == 2  # Initial + 1
            assert result["new_version"]["signature_text"] == sample_proposal["improved_signature"]

    def test_tune_iteratively_single_iteration(self, configured_dspy: MagicMock) -> None:
        """Single iteration when target reached."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Return no tuning needed (score already high)
            tuner.forward = MagicMock(
                return_value={
                    "tuning_needed": False,
                    "current_signature": "question -> answer",
                    "metric_score": 0.85,
                }
            )

            result = tuner.tune_iteratively(
                skill_content="# Good skill",
                current_signature="question -> answer",
                metric_score=0.85,
                target_score=0.80,
            )

            assert result["iterations_used"] == 1
            assert result["target_reached"] is True

    def test_tune_iteratively_max_iterations(self, configured_dspy: MagicMock) -> None:
        """Stops at max_iterations."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 2
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Always need tuning but reject improvements
            tuner.forward = MagicMock(
                return_value={
                    "tuning_needed": True,
                    "accept_improvement": False,
                    "current_signature": "question -> answer",
                    "metric_score": 0.65,
                }
            )

            result = tuner.tune_iteratively(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
            )

            # Should stop after first iteration since improvement rejected
            assert result["iterations_used"] == 1

    def test_tune_iteratively_with_re_evaluate(self, configured_dspy: MagicMock) -> None:
        """Uses re_evaluate_fn when provided."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            call_count = [0]

            def mock_re_evaluate(signature: str) -> float:
                call_count[0] += 1
                return 0.70  # Improved from 0.65

            tuner.forward = MagicMock(
                return_value={
                    "tuning_needed": True,
                    "accept_improvement": True,
                    "proposed_signature": "question -> answer",
                    "current_signature": "question -> answer",
                    "metric_score": 0.65,
                }
            )

            tuner.tune_iteratively(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
                re_evaluate_fn=mock_re_evaluate,
            )

            # re_evaluate_fn should have been called
            assert call_count[0] > 0


# =============================================================================
# Test Integration
# =============================================================================


class TestIntegration:
    """Integration tests for full workflows."""

    def test_full_tuning_workflow(self, configured_dspy: MagicMock) -> None:
        """End-to-end: analyze -> propose -> validate -> accept."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Mock the complete workflow
            mock_analysis = {
                "failure_categories": ["missing_structure"],
                "root_causes": ["No clear sections"],
                "missing_quality_indicators": ["iron_law"],
                "improvement_directions": ["Add sections"],
                "priority_fixes": ["Fix structure"],
            }

            mock_proposal = {
                "improved_signature": "question -> rationale, answer",
                "improvement_reasoning": "Added rationale field",
                "expected_impact": "+0.10",
                "changes_made": ["Added rationale constraint"],
                "confidence": 0.85,
            }

            mock_validation = {
                "is_valid": True,
                "is_improvement": True,
                "validation_notes": "Looks good",
                "potential_issues": [],
                "recommendation": "approve",
            }

            tuner.failure_analyzer = MagicMock(return_value=mock_analysis)
            tuner.signature_proposer = MagicMock(return_value=mock_proposal)
            tuner.signature_validator = MagicMock(return_value=mock_validation)

            result = tuner.forward(
                skill_content="# Poor skill content",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
            )

            # Verify workflow completed
            assert result["tuning_needed"] is True
            assert result["accept_improvement"] is True
            assert "proposed_signature" in result
            assert result["proposed_signature"] == "question -> rationale, answer"

            # Verify all sub-modules were called
            tuner.failure_analyzer.assert_called_once()
            tuner.signature_proposer.assert_called_once()
            tuner.signature_validator.assert_called_once()

    def test_iterative_tuning_workflow(self, configured_dspy: MagicMock) -> None:
        """Multiple iterations with score improvement."""
        with patch.object(SignatureTuner, "__init__", lambda self, **kwargs: None):
            tuner = SignatureTuner.__new__(SignatureTuner)
            tuner.improvement_threshold = 0.05
            tuner.max_iterations = 3
            tuner.quality_threshold = 0.75
            tuner._version_histories = {}

            # Provide re_evaluate_fn that returns improving scores
            # First call: 0.75 (below target of 0.80)
            # Second call: 0.85 (above target)
            re_evaluate_call_count = [0]

            def mock_re_evaluate(signature: str) -> float:
                re_evaluate_call_count[0] += 1
                if re_evaluate_call_count[0] == 1:
                    return 0.75  # First iteration: below target
                else:
                    return 0.85  # Second iteration: above target

            iteration_count = [0]

            def mock_forward(
                skill_content: str,
                current_signature: str,
                metric_score: float,
                **kwargs: object,
            ) -> dict[str, object]:
                iteration_count[0] += 1
                if iteration_count[0] == 1:
                    # First iteration: need tuning
                    return {
                        "tuning_needed": True,
                        "accept_improvement": True,
                        "proposed_signature": "question -> answer",
                        "current_signature": current_signature,
                        "metric_score": metric_score,
                    }
                else:
                    # Second iteration: need more tuning
                    return {
                        "tuning_needed": True,
                        "accept_improvement": True,
                        "proposed_signature": "question -> answer",
                        "current_signature": current_signature,
                        "metric_score": metric_score,
                    }

            tuner.forward = MagicMock(side_effect=mock_forward)

            result = tuner.tune_iteratively(
                skill_content="# Skill",
                current_signature="question -> answer",
                metric_score=0.65,
                target_score=0.80,
                re_evaluate_fn=mock_re_evaluate,
            )

            # Should run 2 iterations:
            # 1. First iteration improves to 0.75 (below target, continue)
            # 2. Second iteration improves to 0.85 (above target, stop)
            assert result["iterations_used"] == 2
            assert result["final_score"] == 0.85
            assert result["target_reached"] is True
