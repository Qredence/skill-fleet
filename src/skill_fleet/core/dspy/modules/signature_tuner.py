"""
DSPy module for metric-driven signature tuning.

This module analyzes skill evaluation failures and proposes improved
signatures to boost quality scores. Uses DSPy optimization patterns
(COPRO/MIPROv2-inspired) to systematically improve prompt instructions.

Phase 1.2 of the DSPy quality improvement roadmap.

Usage:
    from skill_fleet.core.dspy.modules.signature_tuner import SignatureTuner

    tuner = SignatureTuner()
    result = tuner(
        current_signature="question -> answer",
        failure_analysis="Low quality score (0.65). Missing core principle.",
        metric_score=0.65,
        target_score=0.80,
    )
    print(result["improved_signature"])
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import dspy

from ....common.async_utils import run_async
from ....common.dspy_compat import coerce_reasoning_text
from ....common.utils import safe_float, safe_json_loads
from ..metrics import assess_skill_quality
from ..signatures.signature_tuning import (
    AnalyzeSignatureFailures,
    ProposeSignatureImprovement,
    ValidateSignatureImprovement,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Signature Version Tracking
# =============================================================================


@dataclass
class SignatureVersion:
    """Track a single version of a signature with its metadata."""

    version: int
    signature_text: str
    metric_score: float
    tuning_reason: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    improvement_from_previous: float = 0.0
    optimizer_used: str = "signature_tuner"
    hash: str = ""

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.sha256(self.signature_text.encode()).hexdigest()[:12]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert SignatureVersion to dictionary for serialization.

        Returns:
            Dictionary representation of this version.

        """
        return {
            "version": self.version,
            "signature_text": self.signature_text,
            "metric_score": self.metric_score,
            "tuning_reason": self.tuning_reason,
            "created_at": self.created_at,
            "improvement_from_previous": self.improvement_from_previous,
            "optimizer_used": self.optimizer_used,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignatureVersion:
        """
        Create SignatureVersion from dictionary.

        Args:
            data: Dictionary containing signature version data.

        Returns:
            SignatureVersion instance.

        """
        return cls(**data)


@dataclass
class SignatureVersionHistory:
    """Manage version history for a signature."""

    signature_id: str
    versions: list[SignatureVersion] = field(default_factory=list)
    current_version: int = 0

    def add_version(
        self,
        signature_text: str,
        metric_score: float,
        tuning_reason: str,
        optimizer_used: str = "signature_tuner",
    ) -> SignatureVersion:
        """Add a new version to the history."""
        previous_score = self.versions[-1].metric_score if self.versions else 0.0
        self.current_version += 1

        version = SignatureVersion(
            version=self.current_version,
            signature_text=signature_text,
            metric_score=metric_score,
            tuning_reason=tuning_reason,
            improvement_from_previous=metric_score - previous_score,
            optimizer_used=optimizer_used,
        )
        self.versions.append(version)
        return version

    def get_latest(self) -> SignatureVersion | None:
        """Get the latest version."""
        return self.versions[-1] if self.versions else None

    def get_best(self) -> SignatureVersion | None:
        """Get the version with the highest metric score."""
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.metric_score)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert SignatureVersionHistory to dictionary for serialization.

        Returns:
            Dictionary representation of the version history.

        """
        return {
            "signature_id": self.signature_id,
            "current_version": self.current_version,
            "versions": [v.to_dict() for v in self.versions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SignatureVersionHistory:
        """
        Create SignatureVersionHistory from dictionary.

        Args:
            data: Dictionary containing version history data.

        Returns:
            SignatureVersionHistory instance.

        """
        history = cls(
            signature_id=data["signature_id"],
            current_version=data.get("current_version", 0),
        )
        history.versions = [SignatureVersion.from_dict(v) for v in data.get("versions", [])]
        return history

    def save(self, path: Path) -> None:
        """Save version history to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> SignatureVersionHistory:
        """Load version history from JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))


# =============================================================================
# Signature Tuner Module
# =============================================================================


class FailureAnalyzerModule(dspy.Module):
    """Analyze why a signature/skill failed to meet quality thresholds."""

    def __init__(self):
        super().__init__()
        self.analyze = dspy.ChainOfThought(AnalyzeSignatureFailures)

    def forward(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float,
        quality_issues: list[str],
    ) -> dict[str, Any]:
        """
        Analyze signature failures and identify root causes.

        Args:
            skill_content: The generated skill content that scored poorly
            current_signature: The signature that generated this content
            metric_score: Current quality score (0.0-1.0)
            target_score: Target quality score to achieve
            quality_issues: List of specific quality issues identified

        Returns:
            dict: Failure analysis with root causes and improvement directions

        """
        result = self.analyze(
            skill_content=skill_content,
            current_signature=current_signature,
            metric_score=metric_score,
            target_score=target_score,
            quality_issues=json.dumps(quality_issues),
        )
        failure_categories = safe_json_loads(
            getattr(result, "failure_categories", []),
            default=[],
            field_name="failure_categories",
        )
        root_causes = safe_json_loads(
            getattr(result, "root_causes", []), default=[], field_name="root_causes"
        )
        missing_indicators = safe_json_loads(
            getattr(result, "missing_quality_indicators", []),
            default=[],
            field_name="missing_quality_indicators",
        )
        improvement_directions = safe_json_loads(
            getattr(result, "improvement_directions", []),
            default=[],
            field_name="improvement_directions",
        )
        priority_fixes = safe_json_loads(
            getattr(result, "priority_fixes", []),
            default=[],
            field_name="priority_fixes",
        )
        return {
            "failure_categories": failure_categories if isinstance(failure_categories, list) else [],
            "root_causes": root_causes if isinstance(root_causes, list) else [],
            "missing_quality_indicators": missing_indicators
            if isinstance(missing_indicators, list)
            else [],
            "improvement_directions": improvement_directions
            if isinstance(improvement_directions, list)
            else [],
            "priority_fixes": priority_fixes if isinstance(priority_fixes, list) else [],
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class SignatureProposerModule(dspy.Module):
    """Propose improved signature based on failure analysis."""

    def __init__(self):
        super().__init__()
        self.propose = dspy.ChainOfThought(ProposeSignatureImprovement)

    def forward(
        self,
        current_signature: str,
        failure_analysis: dict[str, Any],
        target_score: float,
        skill_type: str,
    ) -> dict[str, Any]:
        """
        Propose an improved signature to address failures.

        Args:
            current_signature: The current signature text
            failure_analysis: Analysis of why the current signature failed
            target_score: Target quality score to achieve
            skill_type: Type of skill (navigation_hub, comprehensive, minimal)

        Returns:
            dict: Proposed improved signature with reasoning

        """
        result = self.propose(
            current_signature=current_signature,
            failure_analysis=json.dumps(failure_analysis),
            target_score=target_score,
            skill_type=skill_type,
        )
        changes_made = safe_json_loads(
            getattr(result, "changes_made", []), default=[], field_name="changes_made"
        )
        return {
            "improved_signature": result.improved_signature,
            "improvement_reasoning": result.improvement_reasoning,
            "expected_impact": result.expected_impact,
            "changes_made": changes_made if isinstance(changes_made, list) else [],
            "confidence": safe_float(getattr(result, "confidence", 0.0), default=0.0),
            "rationale": coerce_reasoning_text(
                getattr(result, "reasoning", getattr(result, "rationale", ""))
            ),
        }


class SignatureValidatorModule(dspy.Module):
    """Validate that proposed signature improvement is valid and beneficial."""

    def __init__(self):
        super().__init__()
        self.validate = dspy.Predict(ValidateSignatureImprovement)

    def forward(
        self,
        original_signature: str,
        proposed_signature: str,
        improvement_reasoning: str,
    ) -> dict[str, Any]:
        """
        Validate a proposed signature improvement.

        Args:
            original_signature: The original signature text
            proposed_signature: The proposed improved signature
            improvement_reasoning: Why this improvement should help

        Returns:
            dict: Validation result with approval status

        """
        result = self.validate(
            original_signature=original_signature,
            proposed_signature=proposed_signature,
            improvement_reasoning=improvement_reasoning,
        )
        return {
            "is_valid": result.is_valid,
            "is_improvement": result.is_improvement,
            "validation_notes": result.validation_notes,
            "potential_issues": result.potential_issues,
            "recommendation": result.recommendation,
        }


class SignatureTuner(dspy.Module):
    """
    Metric-driven signature tuning orchestrator.

    Analyzes skill quality failures and proposes improved signatures
    to boost metric scores. Implements a feedback loop:
    1. Analyze failures (why score < threshold?)
    2. Propose improvements (how to fix?)
    3. Validate proposal (is it safe?)
    4. Track version history

    Inspired by DSPy's COPRO and GEPA optimizers.
    """

    def __init__(
        self,
        improvement_threshold: float = 0.05,
        max_iterations: int = 3,
        quality_threshold: float = 0.75,
    ):
        """
        Initialize the SignatureTuner.

        Args:
            improvement_threshold: Minimum improvement required to accept (default: 5%)
            max_iterations: Maximum tuning iterations per session
            quality_threshold: Score below which tuning is triggered

        """
        super().__init__()
        self.improvement_threshold = improvement_threshold
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold

        self.failure_analyzer = FailureAnalyzerModule()
        self.signature_proposer = SignatureProposerModule()
        self.signature_validator = SignatureValidatorModule()

        self._version_histories: dict[str, SignatureVersionHistory] = {}

    def _get_or_create_history(self, signature_id: str) -> SignatureVersionHistory:
        """Get or create version history for a signature."""
        if signature_id not in self._version_histories:
            self._version_histories[signature_id] = SignatureVersionHistory(
                signature_id=signature_id
            )
        return self._version_histories[signature_id]

    def _extract_quality_issues(self, skill_content: str) -> list[str]:
        """Extract quality issues from skill content using deterministic metrics."""
        try:
            scores = assess_skill_quality(skill_content)
            return scores.issues
        except Exception as e:
            logger.warning(f"Failed to extract quality issues: {e}")
            return []

    def forward(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float = 0.80,
        skill_type: Literal["navigation_hub", "comprehensive", "minimal"] = "comprehensive",
        signature_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Tune a signature to improve quality scores.

        Args:
            skill_content: The generated skill content
            current_signature: The signature that generated this content
            metric_score: Current quality score (0.0-1.0)
            target_score: Target quality score (default: 0.80)
            skill_type: Type of skill for context
            signature_id: Optional ID for version tracking

        Returns:
            dict: Tuning result with improved signature and metadata

        """
        signature_id = signature_id or hashlib.sha256(current_signature.encode()).hexdigest()[:16]
        history = self._get_or_create_history(signature_id)

        # Record initial version if this is first tuning
        if not history.versions:
            history.add_version(
                signature_text=current_signature,
                metric_score=metric_score,
                tuning_reason="Initial version",
            )

        # Check if tuning is needed
        if metric_score >= self.quality_threshold:
            return {
                "tuning_needed": False,
                "reason": f"Score {metric_score:.2f} meets threshold {self.quality_threshold:.2f}",
                "current_signature": current_signature,
                "metric_score": metric_score,
                "version_history": history.to_dict(),
            }

        # Extract quality issues
        quality_issues = self._extract_quality_issues(skill_content)

        # Step 1: Analyze failures
        failure_analysis = self.failure_analyzer(
            skill_content=skill_content,
            current_signature=current_signature,
            metric_score=metric_score,
            target_score=target_score,
            quality_issues=quality_issues,
        )

        # Step 2: Propose improvement
        proposal = self.signature_proposer(
            current_signature=current_signature,
            failure_analysis=failure_analysis,
            target_score=target_score,
            skill_type=skill_type,
        )

        # Step 3: Validate proposal
        validation = self.signature_validator(
            original_signature=current_signature,
            proposed_signature=proposal["improved_signature"],
            improvement_reasoning=proposal["improvement_reasoning"],
        )

        # Determine if we should accept the improvement
        accept_improvement = (
            validation["is_valid"]
            and validation["is_improvement"]
            and proposal["confidence"] >= 0.6
        )

        result = {
            "tuning_needed": True,
            "current_signature": current_signature,
            "metric_score": metric_score,
            "failure_analysis": failure_analysis,
            "proposed_signature": proposal["improved_signature"],
            "improvement_reasoning": proposal["improvement_reasoning"],
            "expected_impact": proposal["expected_impact"],
            "changes_made": proposal["changes_made"],
            "confidence": proposal["confidence"],
            "validation": validation,
            "accept_improvement": accept_improvement,
        }

        # Track version if accepted
        if accept_improvement:
            new_version = history.add_version(
                signature_text=proposal["improved_signature"],
                metric_score=metric_score,  # Will be updated after re-evaluation
                tuning_reason=f"Tuning to improve from {metric_score:.2f} to {target_score:.2f}",
                optimizer_used="signature_tuner",
            )
            result["new_version"] = new_version.to_dict()

        result["version_history"] = history.to_dict()
        return result

    async def aforward(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float = 0.80,
        skill_type: Literal["navigation_hub", "comprehensive", "minimal"] = "comprehensive",
        signature_id: str | None = None,
    ) -> dict[str, Any]:
        """Async version of signature tuning."""
        return await run_async(
            lambda: self.forward(
                skill_content=skill_content,
                current_signature=current_signature,
                metric_score=metric_score,
                target_score=target_score,
                skill_type=skill_type,
                signature_id=signature_id,
            )
        )

    def tune_iteratively(
        self,
        skill_content: str,
        current_signature: str,
        metric_score: float,
        target_score: float = 0.80,
        skill_type: Literal["navigation_hub", "comprehensive", "minimal"] = "comprehensive",
        re_evaluate_fn: Any | None = None,
    ) -> dict[str, Any]:
        """
        Iteratively tune signature until target score is reached or max iterations.

        Args:
            skill_content: The generated skill content
            current_signature: The signature that generated this content
            metric_score: Current quality score (0.0-1.0)
            target_score: Target quality score (default: 0.80)
            skill_type: Type of skill for context
            re_evaluate_fn: Optional function to re-evaluate after tuning
                           Signature: fn(signature: str) -> float (new score)

        Returns:
            dict: Final tuning result with iteration history

        """
        iterations = []
        current_sig = current_signature
        current_score = metric_score

        for i in range(self.max_iterations):
            result = self.forward(
                skill_content=skill_content,
                current_signature=current_sig,
                metric_score=current_score,
                target_score=target_score,
                skill_type=skill_type,
            )

            iterations.append(
                {
                    "iteration": i + 1,
                    "input_signature": current_sig,
                    "input_score": current_score,
                    "result": result,
                }
            )

            if not result.get("tuning_needed"):
                break

            if not result.get("accept_improvement"):
                logger.info(f"Iteration {i + 1}: Improvement rejected")
                break

            # Update for next iteration
            current_sig = result["proposed_signature"]

            # Re-evaluate if function provided
            if re_evaluate_fn:
                try:
                    new_score = re_evaluate_fn(current_sig)
                    improvement = new_score - current_score

                    if improvement < self.improvement_threshold:
                        logger.info(
                            f"Iteration {i + 1}: Improvement {improvement:.2f} below threshold"
                        )
                        break

                    current_score = new_score
                    iterations[-1]["new_score"] = new_score
                    iterations[-1]["improvement"] = improvement

                    if new_score >= target_score:
                        logger.info(f"Iteration {i + 1}: Target score reached!")
                        break
                except Exception as e:
                    logger.warning(f"Re-evaluation failed: {e}")

        return {
            "final_signature": current_sig,
            "final_score": current_score,
            "initial_signature": current_signature,
            "initial_score": metric_score,
            "total_improvement": current_score - metric_score,
            "iterations": iterations,
            "iterations_used": len(iterations),
            "target_reached": current_score >= target_score,
        }


__all__ = [
    "SignatureTuner",
    "SignatureVersion",
    "SignatureVersionHistory",
    "FailureAnalyzerModule",
    "SignatureProposerModule",
    "SignatureValidatorModule",
]
