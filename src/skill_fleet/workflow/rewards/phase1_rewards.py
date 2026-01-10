"""Reward functions for Phase 1: Understanding the Need.

These reward functions are used for:
- DSPy Refine wrapper iterative improvement
- Checkpoint validation scoring
- MIPROv2 optimization

From guidelines lines 1018-1024, Phase 1 validation criteria:
1. Problem statement is clear and specific
2. No existing skill covers this
3. Capabilities are atomic and testable
4. Dependencies are identified
5. Taxonomy path is determined
6. Domain is classified using 8-type matrix

The phase1_completeness_reward function returns a 0.0-1.0 score based on
how well the Phase 1 outputs meet these criteria.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

# Valid skill types from phase1_signatures
VALID_SKILL_TYPES = [
    "cognitive",
    "technical",
    "domain",
    "tool",
    "mcp",
    "specialization",
    "task_focus",
    "memory",
]


def phase1_completeness_reward(args: Mapping[str, Any], pred: Any) -> float:
    """Reward function for Phase 1 completeness.

    This function evaluates Phase 1 outputs against the validation criteria
    from guidelines lines 1018-1024 and returns a score from 0.0 to 1.0.

    Checks:
    1. Problem statement is clear and specific (guidelines line 1018)
    2. No existing skill covers this (line 1019)
    3. Taxonomy path is determined (line 1023)
    4. Domain is classified (line 1024)

    Each check contributes 0.25 to the total score.

    Args:
        args: Input arguments (not used in current implementation)
        pred: Prediction object with Phase 1 outputs

    Returns:
        Float score from 0.0 to 1.0

    Examples:
        >>> # A perfect Phase 1 result
        >>> result = {
        ...     "problem_statement": "Clear problem statement here",
        ...     "is_new_skill": True,
        ...     "skill_type": "technical",
        ...     "proposed_path": "technical/programming/python/async"
        ... }
        >>> score = phase1_completeness_reward({}, result)
        >>> print(score)  # Should be 1.0
    """
    score = 0.0

    # Convert pred to dict if it's not already
    if hasattr(pred, "model_dump"):
        pred_dict = pred.model_dump()
    elif isinstance(pred, dict):
        pred_dict = pred
    else:
        pred_dict = dict(pred)

    # ========================================================================
    # Check 1: Problem statement is clear and specific
    # From guidelines line 1018
    # ========================================================================
    problem_statement = pred_dict.get("problem_statement", "")
    if problem_statement and len(str(problem_statement)) > 20:
        score += 0.25
        logger.debug("✓ Problem statement is clear and specific")
    else:
        logger.debug("✗ Problem statement is missing or too short")

    # ========================================================================
    # Check 2: Novelty decision made
    # From guidelines line 1019
    # ========================================================================
    is_new_skill = pred_dict.get("is_new_skill")
    if is_new_skill is not None:
        score += 0.25
        logger.debug(f"✓ Novelty decision made: is_new_skill={is_new_skill}")
    else:
        logger.debug("✗ Novelty decision not made")

    # ========================================================================
    # Check 3: Domain classified using 8-type matrix
    # From guidelines line 1024
    # ========================================================================
    skill_type = pred_dict.get("skill_type", "")
    if skill_type in VALID_SKILL_TYPES:
        score += 0.25
        logger.debug(f"✓ Domain classified: {skill_type}")
    else:
        logger.debug(f"✗ Invalid or missing skill_type: {skill_type}")

    # ========================================================================
    # Check 4: Taxonomy path is determined
    # From guidelines line 1023
    # ========================================================================
    proposed_path = pred_dict.get("proposed_path", "")
    if proposed_path and "/" in str(proposed_path):
        score += 0.25
        logger.debug(f"✓ Taxonomy path determined: {proposed_path}")
    else:
        logger.debug("✗ Taxonomy path not determined")

    logger.info(f"Phase 1 completeness score: {score:.2f}")

    return score


def phase1_checkpoint_score(
    problem_statement: str,
    is_new_skill: bool | None,
    skill_type: str,
    proposed_path: str,
    overlapping_skills: list | None = None,
) -> float:
    """Calculate Phase 1 checkpoint score.

    This is a convenience function for calculating the checkpoint score
    directly from Phase 1 outputs, without requiring a Prediction object.

    Args:
        problem_statement: Problem statement
        is_new_skill: Whether this is a new skill
        skill_type: Skill type
        proposed_path: Taxonomy path
        overlapping_skills: List of overlapping skills (optional)

    Returns:
        Float score from 0.0 to 1.0

    Examples:
        >>> score = phase1_checkpoint_score(
        ...     problem_statement="Clear problem here",
        ...     is_new_skill=True,
        ...     skill_type="technical",
        ...     proposed_path="technical/programming/python"
        ... )
        >>> print(score)  # Should be 1.0
    """
    pred = {
        "problem_statement": problem_statement,
        "is_new_skill": is_new_skill,
        "skill_type": skill_type,
        "proposed_path": proposed_path,
        "overlapping_skills": overlapping_skills or [],
    }

    return phase1_completeness_reward({}, pred)


__all__ = [
    "phase1_completeness_reward",
    "phase1_checkpoint_score",
    "VALID_SKILL_TYPES",
]
