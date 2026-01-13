"""Phase 1: Understanding the Need - Decision module with reasoning trace capture.

This module implements Phase 1 of the skill creation workflow from
skill-creation-guidelines.md lines 191-239.

Phase 1 consists of 5 decision steps:
1. ExtractProblemStatement - Clear problem formulation
2. DecideNovelty - New vs enhancement decision
3. DetectOverlap - Overlap detection with existing skills
4. ClassifyDomain - 8-type decision matrix classification
5. ProposeTaxonomyPath - Taxonomy placement

Each step uses DSPy ChainOfThought for flexible reasoning within
structured decision boundaries, with full reasoning trace capture.

Usage:
    >>> from skill_fleet.core.tracing import get_phase1_lm, ReasoningTracer
    >>>
    >>> # Create tracer and module
    >>> tracer = ReasoningTracer(mode="cli")
    >>> lm = get_phase1_lm()
    >>>
    >>> # Run Phase 1
    >>> phase1 = Phase1Understand(reasoning_tracer=tracer)
    >>> with dspy.context(lm=lm):
    ...     result = phase1(
    ...         task_description="Create async Python skill",
    ...         existing_skills=[],
    ...         taxonomy_structure={}
    ...     )
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import dspy

from ...core.tracing.tracer import ReasoningTracer
from .signatures import (
    VALID_SKILL_TYPES,
    ClassifyDomain,
    DecideNovelty,
    DetectOverlap,
    ExtractProblemStatement,
    Phase1Checkpoint,
    ProposeTaxonomyPath,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Phase1Understand(dspy.Module):
    """Phase 1: Understanding the Need with explicit decision modules.

    This module implements the 5-step decision process from Phase 1:
    1. Extract a clear problem statement
    2. Decide if this is new or an enhancement
    3. Detect overlaps with existing skills
    4. Classify into one of 8 skill types
    5. Propose taxonomy path

    Each step is a separate DSPy ChainOfThought module, enabling:
    - Flexible reasoning within decision structure
    - Full reasoning trace capture for debugging
    - Iterative refinement with quality assurance

    Args:
        reasoning_tracer: Optional tracer for capturing reasoning
        quality_assured: Whether to use Refine wrapper for iterative improvement

    Attributes:
        extract_problem: Problem statement extraction module
        decide_novelty: Novelty decision module
        detect_overlap: Overlap detection module
        classify_domain: Domain classification module
        propose_taxonomy_path: Taxonomy path proposal module
        phase1_checkpoint: Checkpoint validation module
        tracer: Reasoning tracer instance
    """

    def __init__(
        self,
        reasoning_tracer: ReasoningTracer | None = None,
        quality_assured: bool = False,
    ) -> None:
        """Initialize Phase1Understand module.

        Args:
            reasoning_tracer: Optional tracer for capturing reasoning traces
            quality_assured: Whether to enable quality assurance wrappers
        """
        super().__init__()

        # Sub-modules - each is a DSPy ChainOfThought with reasoning
        self.extract_problem = dspy.ChainOfThought(ExtractProblemStatement)
        self.decide_novelty = dspy.ChainOfThought(DecideNovelty)
        self.detect_overlap = dspy.ChainOfThought(DetectOverlap)
        self.classify_domain = dspy.ChainOfThought(ClassifyDomain)
        self.propose_taxonomy_path = dspy.ChainOfThought(ProposeTaxonomyPath)
        self.phase1_checkpoint = dspy.ChainOfThought(Phase1Checkpoint)

        # Reasoning tracer
        self.tracer = reasoning_tracer or ReasoningTracer(mode="none")

        # Quality assurance flag (for future Refine wrapper)
        self.quality_assured = quality_assured

    def forward(
        self,
        task_description: str,
        existing_skills: list | str = "",
        taxonomy_structure: dict | str = "",
    ) -> dict[str, Any]:
        """Execute Phase 1 with reasoning capture.

        This method runs all 5 decision steps in sequence, capturing
        reasoning traces at each step.

        Args:
            task_description: User's task description
            existing_skills: List of existing skill_ids or JSON string
            taxonomy_structure: Taxonomy structure dict or JSON string

        Returns:
            Dictionary containing:
            - problem_statement: Clear problem statement
            - key_requirements: List of key requirements
            - pain_points: List of pain points
            - is_new_skill: Whether this is a new skill
            - target_skill_id: Skill to enhance (if applicable)
            - overlapping_skills: List of overlapping skills
            - overlap_analysis: Analysis of overlaps
            - skill_type: One of 8 skill types
            - type_confidence: Confidence in classification
            - proposed_path: Taxonomy path
            - parent_skills: Parent skills for context
            - checkpoint_passed: Whether Phase 1 checkpoint passed
            - checkpoint_score: Checkpoint score (0.0-1.0)

        Examples:
            >>> phase1 = Phase1Understand()
            >>> result = phase1(
            ...     task_description="Create async Python skill",
            ...     existing_skills=[],
            ...     taxonomy_structure={}
            ... )
            >>> print(result["skill_type"])  # e.g., "technical"
        """
        results = {}

        # Normalize inputs
        if isinstance(existing_skills, list):
            existing_skills_json = json.dumps(existing_skills)
        else:
            existing_skills_json = existing_skills or "[]"

        if isinstance(taxonomy_structure, dict):
            taxonomy_json = json.dumps(taxonomy_structure)
        else:
            taxonomy_json = taxonomy_structure or "{}"

        # ========================================================================
        # Step 1.1: Extract Problem Statement
        # ========================================================================
        result = self.extract_problem(
            task_description=task_description,
            context="Skill creation request",
        )
        results["problem_statement"] = result.problem_statement
        results["key_requirements"] = list(getattr(result, "key_requirements", []))
        results["pain_points"] = list(getattr(result, "pain_points", []))

        # Capture reasoning
        self.tracer.trace(
            phase="phase1",
            step="extract_problem",
            result=result,
            inputs={"task_description": task_description},
        )

        # ========================================================================
        # Step 1.2: Decide Novelty
        # ========================================================================
        result = self.decide_novelty(
            problem_statement=results["problem_statement"],
            existing_skills=existing_skills_json,
            taxonomy_search_results="{}",  # Would be populated by taxonomy search
        )
        results["is_new_skill"] = result.is_new_skill
        results["target_skill_id"] = getattr(result, "target_skill_id", "")

        # Capture reasoning
        self.tracer.trace(
            phase="phase1",
            step="decide_novelty",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        # ========================================================================
        # Step 1.3: Detect Overlap
        # ========================================================================
        # Preliminary domain classification for overlap detection
        preliminary_type = self._preliminary_classify(results["problem_statement"])

        result = self.detect_overlap(
            problem_statement=results["problem_statement"],
            proposed_domain=preliminary_type,
            existing_skills_metadata="{}",  # Would be populated from skill metadata
        )
        results["overlapping_skills"] = list(getattr(result, "overlapping_skills", []))
        results["overlap_analysis"] = getattr(result, "overlap_analysis", "")
        results["confidence_no_overlap"] = getattr(result, "confidence_no_overlap", 0.0)

        # Capture reasoning
        self.tracer.trace(
            phase="phase1",
            step="detect_overlap",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        # ========================================================================
        # Step 1.4: Classify Domain
        # ========================================================================
        result = self.classify_domain(
            problem_statement=results["problem_statement"],
            key_characteristics=results["key_requirements"],
        )
        results["skill_type"] = result.skill_type
        results["type_confidence"] = result.type_confidence
        results["type_rationale"] = getattr(result, "type_rationale", "")

        # Validate skill type
        if results["skill_type"] not in VALID_SKILL_TYPES:
            logger.warning(
                f"Invalid skill_type '{results['skill_type']}', must be one of {VALID_SKILL_TYPES}"
            )

        # Capture reasoning
        self.tracer.trace(
            phase="phase1",
            step="classify_domain",
            result=result,
            inputs={
                "problem_statement": results["problem_statement"],
                "key_characteristics": results["key_requirements"],
            },
        )

        # ========================================================================
        # Step 1.5: Propose Taxonomy Path
        # ========================================================================
        result = self.propose_taxonomy_path(
            skill_type=results["skill_type"],
            problem_statement=results["problem_statement"],
            existing_taxonomy=taxonomy_json,
        )
        results["proposed_path"] = result.proposed_path
        results["parent_skills"] = list(getattr(result, "parent_skills", []))
        results["path_confidence"] = getattr(result, "path_confidence", 0.0)

        # Capture reasoning
        self.tracer.trace(
            phase="phase1",
            step="propose_taxonomy_path",
            result=result,
            inputs={
                "skill_type": results["skill_type"],
                "problem_statement": results["problem_statement"],
            },
        )

        # ========================================================================
        # Phase 1 Checkpoint
        # ========================================================================
        result = self.phase1_checkpoint(
            problem_statement=results["problem_statement"],
            is_new_skill=results["is_new_skill"],
            skill_type=results["skill_type"],
            proposed_path=results["proposed_path"],
            overlapping_skills=results["overlapping_skills"],
            key_requirements=results["key_requirements"],
        )
        results["checkpoint_passed"] = result.checkpoint_passed
        results["checkpoint_score"] = result.checkpoint_score
        results["validation_errors"] = list(getattr(result, "validation_errors", []))
        results["recommendations"] = list(getattr(result, "recommendations", []))

        # Capture checkpoint reasoning
        self.tracer.trace(
            phase="phase1",
            step="checkpoint",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        logger.info(
            f"Phase 1 complete: checkpoint_passed={results['checkpoint_passed']}, "
            f"score={results['checkpoint_score']:.2f}"
        )

        return results

    async def aforward(
        self,
        task_description: str,
        existing_skills: list | str = "",
        taxonomy_structure: dict | str = "",
    ) -> dict[str, Any]:
        """Asynchronously execute Phase 1 with reasoning capture.

        DSPy supports async execution via `.acall()` on modules (see dspy.ai
        async tutorial). This implementation mirrors `forward()` but awaits the
        internal DSPy sub-modules.
        """
        results: dict[str, Any] = {}

        # Normalize inputs
        if isinstance(existing_skills, list):
            existing_skills_json = json.dumps(existing_skills)
        else:
            existing_skills_json = existing_skills or "[]"

        if isinstance(taxonomy_structure, dict):
            taxonomy_json = json.dumps(taxonomy_structure)
        else:
            taxonomy_json = taxonomy_structure or "{}"

        # ====================================================================
        # Step 1.1: Extract Problem Statement
        # ====================================================================
        result = await self.extract_problem.acall(
            task_description=task_description,
            context="Skill creation request",
        )
        results["problem_statement"] = result.problem_statement
        results["key_requirements"] = list(getattr(result, "key_requirements", []))
        results["pain_points"] = list(getattr(result, "pain_points", []))

        self.tracer.trace(
            phase="phase1",
            step="extract_problem",
            result=result,
            inputs={"task_description": task_description},
        )

        # ====================================================================
        # Step 1.2: Decide Novelty
        # ====================================================================
        result = await self.decide_novelty.acall(
            problem_statement=results["problem_statement"],
            existing_skills=existing_skills_json,
            taxonomy_search_results="{}",
        )
        results["is_new_skill"] = result.is_new_skill
        results["target_skill_id"] = getattr(result, "target_skill_id", "")

        self.tracer.trace(
            phase="phase1",
            step="decide_novelty",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        # ====================================================================
        # Step 1.3: Detect Overlap
        # ====================================================================
        preliminary_type = self._preliminary_classify(results["problem_statement"])
        result = await self.detect_overlap.acall(
            problem_statement=results["problem_statement"],
            proposed_domain=preliminary_type,
            existing_skills_metadata="{}",
        )
        results["overlapping_skills"] = list(getattr(result, "overlapping_skills", []))
        results["overlap_analysis"] = getattr(result, "overlap_analysis", "")
        results["confidence_no_overlap"] = getattr(result, "confidence_no_overlap", 0.0)

        self.tracer.trace(
            phase="phase1",
            step="detect_overlap",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        # ====================================================================
        # Step 1.4: Classify Domain
        # ====================================================================
        result = await self.classify_domain.acall(
            problem_statement=results["problem_statement"],
            key_characteristics=results["key_requirements"],
        )
        results["skill_type"] = result.skill_type
        results["type_confidence"] = result.type_confidence
        results["type_rationale"] = getattr(result, "type_rationale", "")

        if results["skill_type"] not in VALID_SKILL_TYPES:
            logger.warning(
                f"Invalid skill_type '{results['skill_type']}', must be one of {VALID_SKILL_TYPES}"
            )

        self.tracer.trace(
            phase="phase1",
            step="classify_domain",
            result=result,
            inputs={
                "problem_statement": results["problem_statement"],
                "key_characteristics": results["key_requirements"],
            },
        )

        # ====================================================================
        # Step 1.5: Propose Taxonomy Path
        # ====================================================================
        result = await self.propose_taxonomy_path.acall(
            skill_type=results["skill_type"],
            problem_statement=results["problem_statement"],
            existing_taxonomy=taxonomy_json,
        )
        results["proposed_path"] = result.proposed_path
        results["parent_skills"] = list(getattr(result, "parent_skills", []))
        results["path_confidence"] = getattr(result, "path_confidence", 0.0)

        self.tracer.trace(
            phase="phase1",
            step="propose_taxonomy_path",
            result=result,
            inputs={
                "skill_type": results["skill_type"],
                "problem_statement": results["problem_statement"],
            },
        )

        # ====================================================================
        # Phase 1 Checkpoint
        # ====================================================================
        result = await self.phase1_checkpoint.acall(
            problem_statement=results["problem_statement"],
            is_new_skill=results["is_new_skill"],
            skill_type=results["skill_type"],
            proposed_path=results["proposed_path"],
            overlapping_skills=results["overlapping_skills"],
            key_requirements=results["key_requirements"],
        )
        results["checkpoint_passed"] = result.checkpoint_passed
        results["checkpoint_score"] = result.checkpoint_score
        results["validation_errors"] = list(getattr(result, "validation_errors", []))
        results["recommendations"] = list(getattr(result, "recommendations", []))

        self.tracer.trace(
            phase="phase1",
            step="checkpoint",
            result=result,
            inputs={"problem_statement": results["problem_statement"]},
        )

        logger.info(
            f"Phase 1 complete: checkpoint_passed={results['checkpoint_passed']}, "
            f"score={results['checkpoint_score']:.2f}"
        )

        return results

    def _preliminary_classify(self, problem_statement: str) -> str:
        """Quick preliminary classification for overlap detection.

        Args:
            problem_statement: Problem statement to classify

        Returns:
            Preliminary skill type
        """
        # Simple heuristic-based classification
        # This will be refined by the actual ClassifyDomain module
        statement_lower = problem_statement.lower()

        if any(word in statement_lower for word in ["code", "programming", "function", "api"]):
            return "technical"
        elif any(word in statement_lower for word in ["think", "decide", "reason"]):
            return "cognitive"
        elif any(word in statement_lower for word in ["tool", "service", "integration"]):
            return "tool"
        else:
            return "domain"


__all__ = [
    "Phase1Understand",
]
