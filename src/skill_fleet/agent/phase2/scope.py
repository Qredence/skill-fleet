"""Phase 2: Scope & Boundaries - Decision module with reasoning trace capture.

This module implements Phase 2 of the skill creation workflow from
skill-creation-guidelines.md lines 240-353.

Phase 2 consists of 6 decision steps:
1. ConfirmSkillType - Re-validate Phase 1 classification
2. DetermineWeight - Lightweight/medium/heavyweight based on capability count
3. DecideLoadPriority - Always/task_specific/on_demand/dormant using decision tree
4. DesignCapabilities - 3-7 atomic capabilities
5. ValidateDependencies - 5 composition rules validation
6. GenerateSkillMetadata - Complete skill metadata

Each step uses DSPy ChainOfThought for flexible reasoning within
structured decision boundaries, with full reasoning trace capture.

Usage:
    >>> from skill_fleet.core.tracing import get_phase2_lm, ReasoningTracer
    >>>
    >>> # Create tracer and module
    >>> tracer = ReasoningTracer(mode="cli")
    >>> lm = get_phase2_lm()
    >>>
    >>> # Run Phase 2
    >>> phase2 = Phase2Scope(reasoning_tracer=tracer)
    >>> with dspy.context(lm=lm):
    ...     result = phase2(
    ...         phase1_output=phase1_result,
    ...         parent_skills=[],
    ...         existing_taxonomy={}
    ...     )
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import dspy

from ...core.tracing.tracer import ReasoningTracer
from .signatures import (
    VALID_PRIORITIES,
    VALID_WEIGHTS,
    ConfirmSkillType,
    DecideLoadPriority,
    DesignCapabilities,
    DetermineWeight,
    GenerateSkillMetadata,
    Phase2Checkpoint,
    ValidateDependencies,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Phase2Scope(dspy.Module):
    """Phase 2: Scope & Boundaries with explicit decision trees.

    This module implements the 6-step decision process from Phase 2:
    1. Confirm the skill type from Phase 1
    2. Determine weight (lightweight/medium/heavyweight)
    3. Decide load priority (always/task_specific/on_demand/dormant)
    4. Design 3-7 atomic capabilities
    5. Validate dependencies against 5 composition rules
    6. Generate complete skill metadata

    Each step is a separate DSPy ChainOfThought module, enabling:
    - Flexible reasoning within decision structure
    - Full reasoning trace capture for debugging
    - Iterative refinement with quality assurance

    Args:
        reasoning_tracer: Optional tracer for capturing reasoning
        quality_assured: Whether to use MultiChainComparison for critical decisions

    Attributes:
        confirm_type: Type confirmation module
        determine_weight: Weight determination module
        decide_load_priority: Load priority decision module
        design_capabilities: Capability design module
        validate_dependencies: Dependency validation module
        generate_metadata: Metadata generation module
        phase2_checkpoint: Checkpoint validation module
        tracer: Reasoning tracer instance
    """

    def __init__(
        self,
        reasoning_tracer: ReasoningTracer | None = None,
        quality_assured: bool = False,
    ) -> None:
        """Initialize Phase2Scope module.

        Args:
            reasoning_tracer: Optional tracer for capturing reasoning traces
            quality_assured: Whether to enable quality assurance wrappers
        """
        super().__init__()

        # Sub-modules - each is a DSPy ChainOfThought with reasoning
        self.confirm_type = dspy.ChainOfThought(ConfirmSkillType)
        self.determine_weight = dspy.ChainOfThought(DetermineWeight)
        self.decide_load_priority = dspy.ChainOfThought(DecideLoadPriority)
        self.design_capabilities = dspy.ChainOfThought(DesignCapabilities)
        self.validate_dependencies = dspy.ChainOfThought(ValidateDependencies)
        self.generate_metadata = dspy.ChainOfThought(GenerateSkillMetadata)
        self.phase2_checkpoint = dspy.ChainOfThought(Phase2Checkpoint)

        # Reasoning tracer
        self.tracer = reasoning_tracer or ReasoningTracer(mode="none")

        # Quality assurance flag (for future MultiChainComparison wrapper)
        self.quality_assured = quality_assured

    def forward(
        self,
        phase1_output: dict | str = "",
        parent_skills: list | str = "",
        existing_taxonomy: dict | str = "",
    ) -> dict[str, Any]:
        """Execute Phase 2 with reasoning capture.

        This method runs all 6 decision steps in sequence, capturing
        reasoning traces at each step.

        Args:
            phase1_output: Phase 1 output dict or JSON string
            parent_skills: Parent skills list or JSON string
            existing_taxonomy: Taxonomy structure dict or JSON string

        Returns:
            Dictionary containing:
            - confirmed_type: Confirmed skill type
            - weight: lightweight/medium/heavyweight
            - load_priority: always/task_specific/on_demand/dormant
            - capabilities: List of designed capabilities (3-7)
            - dependencies: Validated dependencies
            - skill_metadata: Complete skill metadata
            - checkpoint_passed: Whether Phase 2 checkpoint passed
            - checkpoint_score: Checkpoint score (0.0-1.0)

        Examples:
            >>> phase2 = Phase2Scope()
            >>> result = phase2(
            ...     phase1_output=phase1_result,
            ...     parent_skills=[],
            ...     existing_taxonomy={}
            ... )
            >>> print(result["weight"])  # e.g., "medium"
        """
        results = {}

        # Normalize inputs
        if isinstance(phase1_output, dict):
            phase1_json = json.dumps(phase1_output)
        else:
            phase1_json = phase1_output or "{}"

        if isinstance(existing_taxonomy, dict):
            taxonomy_json = json.dumps(existing_taxonomy)
        else:
            taxonomy_json = existing_taxonomy or "{}"

        # Extract key info from Phase 1
        if isinstance(phase1_output, dict):
            problem_statement = phase1_output.get("problem_statement", "")
            phase1_type = phase1_output.get("skill_type", "technical")
            phase1_rationale = phase1_output.get("type_rationale", "")
        else:
            problem_statement = ""
            phase1_type = "technical"
            phase1_rationale = ""

        # ========================================================================
        # Step 2.1: Confirm Skill Type
        # ========================================================================
        result = self.confirm_type(
            phase1_type=phase1_type,
            phase1_rationale=phase1_rationale,
            problem_statement=problem_statement,
        )
        results["confirmed_type"] = result.confirmed_type
        results["confirmation_confidence"] = result.confirmation_confidence

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="confirm_type",
            result=result,
            inputs={"phase1_type": phase1_type, "problem_statement": problem_statement},
        )

        # ========================================================================
        # Step 2.2: Determine Weight
        # ========================================================================
        # For now, use default values - will be updated after capabilities are designed
        result = self.determine_weight(
            proposed_capabilities=[],  # Will be updated after design_capabilities
            estimated_documentation_lines=500,
            planned_examples_count=2,
        )
        results["weight"] = result.weight
        results["weight_justification"] = getattr(result, "weight_justification", "")

        # Validate weight
        if results["weight"] not in VALID_WEIGHTS:
            logger.warning(f"Invalid weight '{results['weight']}', must be one of {VALID_WEIGHTS}")

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="determine_weight",
            result=result,
            inputs={"estimated_documentation_lines": 500},
        )

        # ========================================================================
        # Step 2.3: Decide Load Priority
        # ========================================================================
        # Use decision tree logic - start with defaults
        result = self.decide_load_priority(
            problem_statement=problem_statement,
            skill_type=results["confirmed_type"],
            is_core_foundation=False,  # Default to False
            is_commonly_used=True,  # Default to True
            is_experimental=False,  # Default to False
        )
        results["load_priority"] = result.load_priority
        results["priority_justification"] = getattr(result, "priority_justification", "")

        # Validate load priority
        if results["load_priority"] not in VALID_PRIORITIES:
            logger.warning(
                f"Invalid load_priority '{results['load_priority']}', "
                f"must be one of {VALID_PRIORITIES}"
            )

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="decide_load_priority",
            result=result,
            inputs={
                "problem_statement": problem_statement,
                "skill_type": results["confirmed_type"],
            },
        )

        # ========================================================================
        # Step 2.4: Design Capabilities
        # ========================================================================
        # Extract key requirements from Phase 1
        if isinstance(phase1_output, dict):
            key_requirements = phase1_output.get("key_requirements", [])
        else:
            key_requirements = []

        result = self.design_capabilities(
            problem_statement=problem_statement,
            phase1_requirements=key_requirements,
            target_count=5,  # Target 5 capabilities (middle of 3-7 range)
        )
        results["capabilities"] = list(getattr(result, "capabilities", []))
        results["capability_count"] = getattr(result, "capability_count", 0)
        results["atomicity_analysis"] = getattr(result, "atomicity_analysis", "")

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="design_capabilities",
            result=result,
            inputs={
                "problem_statement": problem_statement,
                "phase1_requirements": key_requirements,
            },
        )

        # ========================================================================
        # Step 2.5: Validate Dependencies
        # ========================================================================
        # Start with empty dependencies
        result = self.validate_dependencies(
            proposed_dependencies=[],
            existing_taxonomy=taxonomy_json,
        )
        results["dependencies_valid"] = result.dependencies_valid
        results["validation_details"] = list(getattr(result, "validation_details", []))
        results["suggested_revisions"] = list(getattr(result, "suggested_revisions", []))

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="validate_dependencies",
            result=result,
            inputs={"proposed_dependencies_count": 0},
        )

        # ========================================================================
        # Step 2.6: Generate Skill Metadata
        # ========================================================================
        result = self.generate_metadata(
            phase1_outputs=phase1_json,
            confirmed_type=results["confirmed_type"],
            weight=results["weight"],
            load_priority=results["load_priority"],
            capabilities=results["capabilities"],
            dependencies=[],  # Start with empty dependencies
        )
        results["skill_metadata"] = result.skill_metadata
        results["resource_requirements"] = result.resource_requirements
        results["compatibility_constraints"] = result.compatibility_constraints

        # Capture reasoning
        self.tracer.trace(
            phase="phase2",
            step="generate_metadata",
            result=result,
            inputs={
                "confirmed_type": results["confirmed_type"],
                "weight": results["weight"],
                "load_priority": results["load_priority"],
            },
        )

        # ========================================================================
        # Phase 2 Checkpoint
        # ========================================================================
        # Convert skill_metadata to dict for checkpoint
        if hasattr(results["skill_metadata"], "model_dump"):
            skill_metadata_dict = results["skill_metadata"].model_dump()
        else:
            skill_metadata_dict = results["skill_metadata"]

        result = self.phase2_checkpoint(
            skill_metadata=json.dumps(skill_metadata_dict),
            capabilities=results["capabilities"],
            dependencies=[],
            confirmed_type=results["confirmed_type"],
            weight=results["weight"],
            load_priority=results["load_priority"],
        )
        results["checkpoint_passed"] = result.checkpoint_passed
        results["checkpoint_score"] = result.checkpoint_score
        results["validation_errors"] = list(getattr(result, "validation_errors", []))
        results["readiness_for_phase3"] = result.readiness_for_phase3

        # Capture checkpoint reasoning
        self.tracer.trace(
            phase="phase2",
            step="checkpoint",
            result=result,
            inputs={"skill_metadata": skill_metadata_dict},
        )

        logger.info(
            f"Phase 2 complete: checkpoint_passed={results['checkpoint_passed']}, "
            f"score={results['checkpoint_score']:.2f}"
        )

        return results

    async def aforward(
        self,
        phase1_output: dict | str = "",
        parent_skills: list | str = "",
        existing_taxonomy: dict | str = "",
    ) -> dict[str, Any]:
        """Asynchronously execute Phase 2 with reasoning capture.

        Mirrors `forward()` but awaits DSPy sub-modules via `.acall()`.
        """
        results: dict[str, Any] = {}

        # Normalize inputs
        if isinstance(phase1_output, dict):
            phase1_json = json.dumps(phase1_output)
        else:
            phase1_json = phase1_output or "{}"

        if isinstance(existing_taxonomy, dict):
            taxonomy_json = json.dumps(existing_taxonomy)
        else:
            taxonomy_json = existing_taxonomy or "{}"

        # Extract key info from Phase 1
        if isinstance(phase1_output, dict):
            problem_statement = phase1_output.get("problem_statement", "")
            phase1_type = phase1_output.get("skill_type", "technical")
            phase1_rationale = phase1_output.get("type_rationale", "")
        else:
            problem_statement = ""
            phase1_type = "technical"
            phase1_rationale = ""

        # ====================================================================
        # Step 2.1: Confirm Skill Type
        # ====================================================================
        result = await self.confirm_type.acall(
            phase1_type=phase1_type,
            phase1_rationale=phase1_rationale,
            problem_statement=problem_statement,
        )
        results["confirmed_type"] = result.confirmed_type
        results["confirmation_confidence"] = result.confirmation_confidence

        self.tracer.trace(
            phase="phase2",
            step="confirm_type",
            result=result,
            inputs={"phase1_type": phase1_type, "problem_statement": problem_statement},
        )

        # ====================================================================
        # Step 2.2: Determine Weight
        # ====================================================================
        result = await self.determine_weight.acall(
            proposed_capabilities=[],
            estimated_documentation_lines=500,
            planned_examples_count=2,
        )
        results["weight"] = result.weight
        results["weight_justification"] = getattr(result, "weight_justification", "")

        if results["weight"] not in VALID_WEIGHTS:
            logger.warning(f"Invalid weight '{results['weight']}', must be one of {VALID_WEIGHTS}")

        self.tracer.trace(
            phase="phase2",
            step="determine_weight",
            result=result,
            inputs={"estimated_documentation_lines": 500},
        )

        # ====================================================================
        # Step 2.3: Decide Load Priority
        # ====================================================================
        result = await self.decide_load_priority.acall(
            problem_statement=problem_statement,
            skill_type=results["confirmed_type"],
            is_core_foundation=False,
            is_commonly_used=True,
            is_experimental=False,
        )
        results["load_priority"] = result.load_priority
        results["priority_justification"] = getattr(result, "priority_justification", "")

        if results["load_priority"] not in VALID_PRIORITIES:
            logger.warning(
                f"Invalid load_priority '{results['load_priority']}', "
                f"must be one of {VALID_PRIORITIES}"
            )

        self.tracer.trace(
            phase="phase2",
            step="decide_load_priority",
            result=result,
            inputs={
                "problem_statement": problem_statement,
                "skill_type": results["confirmed_type"],
            },
        )

        # ====================================================================
        # Step 2.4: Design Capabilities
        # ====================================================================
        if isinstance(phase1_output, dict):
            key_requirements = phase1_output.get("key_requirements", [])
        else:
            key_requirements = []

        result = await self.design_capabilities.acall(
            problem_statement=problem_statement,
            phase1_requirements=key_requirements,
            target_count=5,
        )
        results["capabilities"] = list(getattr(result, "capabilities", []))
        results["capability_count"] = getattr(result, "capability_count", 0)
        results["atomicity_analysis"] = getattr(result, "atomicity_analysis", "")

        self.tracer.trace(
            phase="phase2",
            step="design_capabilities",
            result=result,
            inputs={
                "problem_statement": problem_statement,
                "phase1_requirements": key_requirements,
            },
        )

        # ====================================================================
        # Step 2.5: Validate Dependencies
        # ====================================================================
        result = await self.validate_dependencies.acall(
            proposed_dependencies=[],
            existing_taxonomy=taxonomy_json,
        )
        results["dependencies_valid"] = result.dependencies_valid
        results["validation_details"] = list(getattr(result, "validation_details", []))
        results["suggested_revisions"] = list(getattr(result, "suggested_revisions", []))

        self.tracer.trace(
            phase="phase2",
            step="validate_dependencies",
            result=result,
            inputs={"proposed_dependencies_count": 0},
        )

        # ====================================================================
        # Step 2.6: Generate Skill Metadata
        # ====================================================================
        result = await self.generate_metadata.acall(
            phase1_outputs=phase1_json,
            confirmed_type=results["confirmed_type"],
            weight=results["weight"],
            load_priority=results["load_priority"],
            capabilities=results["capabilities"],
            dependencies=[],
        )
        results["skill_metadata"] = result.skill_metadata
        results["resource_requirements"] = result.resource_requirements
        results["compatibility_constraints"] = result.compatibility_constraints

        self.tracer.trace(
            phase="phase2",
            step="generate_metadata",
            result=result,
            inputs={
                "confirmed_type": results["confirmed_type"],
                "weight": results["weight"],
                "load_priority": results["load_priority"],
            },
        )

        # ====================================================================
        # Phase 2 Checkpoint
        # ====================================================================
        if hasattr(results["skill_metadata"], "model_dump"):
            skill_metadata_dict = results["skill_metadata"].model_dump()
        else:
            skill_metadata_dict = results["skill_metadata"]

        result = await self.phase2_checkpoint.acall(
            skill_metadata=json.dumps(skill_metadata_dict),
            capabilities=results["capabilities"],
            dependencies=[],
            confirmed_type=results["confirmed_type"],
            weight=results["weight"],
            load_priority=results["load_priority"],
        )
        results["checkpoint_passed"] = result.checkpoint_passed
        results["checkpoint_score"] = result.checkpoint_score
        results["validation_errors"] = list(getattr(result, "validation_errors", []))
        results["readiness_for_phase3"] = result.readiness_for_phase3

        self.tracer.trace(
            phase="phase2",
            step="checkpoint",
            result=result,
            inputs={"skill_metadata": skill_metadata_dict},
        )

        logger.info(
            f"Phase 2 complete: checkpoint_passed={results['checkpoint_passed']}, "
            f"score={results['checkpoint_score']:.2f}"
        )

        return results


__all__ = [
    "Phase2Scope",
]
