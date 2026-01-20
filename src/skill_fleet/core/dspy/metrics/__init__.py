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

from .enhanced_metrics import (
    create_metric_for_phase,
    metadata_quality_metric,
    skill_style_alignment_metric,
    taxonomy_accuracy_metric,
    comprehensive_metric,
)
from .gepa_reflection import (
    gepa_composite_metric,
    gepa_semantic_match_metric,
    gepa_skill_quality_metric,
)
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
    # Skill quality metrics
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
    # Enhanced metrics
    "taxonomy_accuracy_metric",
    "metadata_quality_metric",
    "skill_style_alignment_metric",
    "create_metric_for_phase",
    "comprehensive_metric",
    # GEPA-specific reflection metrics
    "gepa_skill_quality_metric",
    "gepa_semantic_match_metric",
    "gepa_composite_metric",
]
