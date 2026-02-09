"""
Analytics and recommendations routes for v1 API.

This module provides endpoints for usage analytics and skill recommendations.

Endpoints:
    GET /api/v1/analytics - Get usage analytics
    GET /api/v1/analytics/recommendations - Get skill recommendations
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from ...analytics.engine import AnalyticsEngine, RecommendationEngine
from ..dependencies import TaxonomyManagerDep
from ..schemas.analytics import AnalyticsResponse, RecommendationItem, RecommendationsResponse

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    taxonomy_manager: TaxonomyManagerDep,
    user_id: str | None = Query(None, description="Filter analytics by user ID (optional)"),
) -> AnalyticsResponse:
    """
    Get usage analytics and statistics.

    Analyzes skill usage patterns from the usage log, including:
    - Total events and success rate
    - Most frequently used skills
    - Common skill combinations
    - Cold/underutilized skills

    Args:
        taxonomy_manager: Injected TaxonomyManager for analytics access
        user_id: Optional user ID to filter analytics (omit for all users)

    Returns:
        AnalyticsResponse with comprehensive usage statistics

    """
    try:
        # Initialize analytics engine
        analytics_file = taxonomy_manager.skills_root / "_analytics" / "usage_log.jsonl"

        if not analytics_file.exists():
            # Return empty analytics if no usage data
            return AnalyticsResponse(
                total_events=0,
                unique_skills_used=0,
                success_rate=0.0,
                most_used_skills=[],
                common_combinations=[],
                cold_skills=[],
            )

        engine = AnalyticsEngine(analytics_file)
        stats = engine.analyze_usage(user_id=user_id)

        return AnalyticsResponse(
            total_events=stats["total_events"],
            unique_skills_used=stats["unique_skills_used"],
            success_rate=stats["success_rate"],
            most_used_skills=stats["most_used_skills"],
            common_combinations=stats["common_combinations"],
            cold_skills=stats["cold_skills"],
        )

    except Exception as e:
        logger.exception(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}",
        ) from e


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    taxonomy_manager: TaxonomyManagerDep,
    user_id: str = Query(..., description="User ID for personalized recommendations"),
) -> RecommendationsResponse:
    """
    Get skill recommendations for a user.

    Generates personalized skill recommendations based on:
    - User's usage patterns
    - Dependencies of frequently used skills
    - Taxonomy structure and skill relationships

    Args:
        taxonomy_manager: Injected TaxonomyManager for recommendations
        user_id: User ID for personalized recommendations (required)

    Returns:
        RecommendationsResponse with list of recommended skills and reasons

    """
    try:
        # Initialize analytics engine and recommendation engine
        analytics_file = taxonomy_manager.skills_root / "_analytics" / "usage_log.jsonl"

        if not analytics_file.exists():
            # Return empty recommendations if no usage data
            return RecommendationsResponse(
                user_id=user_id,
                recommendations=[],
                total_recommendations=0,
            )

        analytics_engine = AnalyticsEngine(analytics_file)
        recommender = RecommendationEngine(analytics_engine, taxonomy_manager)

        # Get recommendations
        raw_recommendations = recommender.recommend_skills(user_id)

        # Convert to schema format
        recommendations = [
            RecommendationItem(
                skill_id=rec["skill_id"],
                reason=rec["reason"],
                priority=rec["priority"],
            )
            for rec in raw_recommendations
        ]

        return RecommendationsResponse(
            user_id=user_id,
            recommendations=recommendations,
            total_recommendations=len(recommendations),
        )

    except Exception as e:
        logger.exception(f"Error getting recommendations for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}",
        ) from e
