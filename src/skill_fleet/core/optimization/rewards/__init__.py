"""Reward functions and metrics for DSPy optimization.

This package provides:
- Phase 1 completeness reward function
- Phase 2 validity metric function
- Step-specific reward functions for DSPy Refine/BestOfN wrappers

These are used for:
- DSPy Refine wrapper iterative improvement
- DSPy BestOfN multi-attempt selection
- MIPROv2 optimization metrics
- Checkpoint validation scoring
"""

from .phase1_rewards import phase1_checkpoint_score, phase1_completeness_reward
from .phase2_rewards import phase2_checkpoint_score, phase2_validity_metric
from .step_rewards import (
    capabilities_reward,
    combined_edit_reward,
    combined_package_reward,
    combined_plan_reward,
    metadata_completeness_reward,
    quality_score_reward,
    skill_content_reward,
    taxonomy_path_reward,
    usage_examples_reward,
    validation_report_reward,
)

__all__ = [
    # Step rewards from step_rewards.py
    "taxonomy_path_reward",
    "metadata_completeness_reward",
    "capabilities_reward",
    "skill_content_reward",
    "usage_examples_reward",
    "validation_report_reward",
    "quality_score_reward",
    "combined_plan_reward",
    "combined_edit_reward",
    "combined_package_reward",
    # Phase-specific rewards
    "phase1_completeness_reward",
    "phase1_checkpoint_score",
    "phase2_validity_metric",
    "phase2_checkpoint_score",
]
