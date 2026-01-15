"""Skill quality metrics for DSPy evaluation and optimization.

This module provides quality assessment functions for evaluating generated skills.

Usage:
    from skill_fleet.core.dspy.metrics import assess_skill_quality, skill_quality_metric

    # Standalone quality assessment
    scores = assess_skill_quality(skill_content)
    print(f"Overall score: {scores.overall_score}")
    print(f"Issues: {scores.issues}")

    # DSPy metric for optimization
    optimizer = MIPROv2(metric=skill_quality_metric, ...)
"""

from __future__ import annotations

from .skill_quality import (
    SkillQualityScores,
    assess_skill_quality,
    compute_overall_score,
    evaluate_code_examples,
    evaluate_frontmatter,
    evaluate_patterns,
    evaluate_structure,
    parse_skill_content,
    skill_quality_metric,
    skill_quality_metric_detailed,
)

__all__ = [
    "SkillQualityScores",
    "assess_skill_quality",
    "compute_overall_score",
    "evaluate_code_examples",
    "evaluate_frontmatter",
    "evaluate_patterns",
    "evaluate_structure",
    "parse_skill_content",
    "skill_quality_metric",
    "skill_quality_metric_detailed",
]
