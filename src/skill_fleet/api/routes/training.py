"""Training data analytics endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...config.training.manager import TrainingDataManager

router = APIRouter()


@router.get("/analytics", response_model=dict[str, Any])
async def get_training_analytics() -> dict[str, Any]:
    """
    Get analytics for training data quality and usage.

    Returns:
        Dictionary containing:
        - total_examples: Total count
        - quality_distribution: Histogram of quality scores
        - top_performers: Examples with high success rates
        - category_breakdown: Count by category
        - recommendations: Actionable improvements

    """
    manager = TrainingDataManager()
    # Force reload metadata
    manager._load_metadata()

    total = len(manager._metadata)
    if total == 0:
        return {
            "total_examples": 0,
            "quality_distribution": {},
            "top_performers": [],
            "category_breakdown": {},
            "recommendations": ["No training metadata found. Run optimization to generate stats."],
        }

    # Analyze
    quality_scores = [m.quality_score for m in manager._metadata.values()]
    quality_dist = {
        "high (>=0.8)": len([s for s in quality_scores if s >= 0.8]),
        "medium (0.5-0.8)": len([s for s in quality_scores if 0.5 <= s < 0.8]),
        "low (<0.5)": len([s for s in quality_scores if s < 0.5]),
    }

    # Categories
    categories = {}
    for m in manager._metadata.values():
        categories[m.category] = categories.get(m.category, 0) + 1

    # Top performers
    sorted_by_success = sorted(
        manager._metadata.values(), key=lambda m: m.success_rate, reverse=True
    )
    top_performers = [
        {
            "id": m.example_id,
            "task": m.task_description[:50] + "...",
            "score": m.quality_score,
            "success_rate": m.success_rate,
        }
        for m in sorted_by_success[:5]
    ]

    # Recommendations
    recommendations = []
    if quality_dist["low (<0.5)"] > total * 0.3:
        recommendations.append("High number of low-quality examples. Consider pruning.")
    if len(categories) < 3:
        recommendations.append("Low category diversity. Add examples for more skill types.")

    return {
        "total_examples": total,
        "quality_distribution": quality_dist,
        "top_performers": top_performers,
        "category_breakdown": categories,
        "recommendations": recommendations,
    }
