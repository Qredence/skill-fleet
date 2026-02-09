"""Pydantic schemas for analytics-related API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyticsResponse(BaseModel):
    """Response model for usage analytics."""

    total_events: int = Field(description="Total number of usage events")
    unique_skills_used: int = Field(description="Number of unique skills used")
    success_rate: float = Field(description="Success rate (0.0-1.0)")
    most_used_skills: list[tuple[str, int]] = Field(
        description="List of (skill_id, count) tuples for most used skills"
    )
    common_combinations: list[dict[str, Any]] = Field(
        description="Common skill combinations used together"
    )
    cold_skills: list[str] = Field(description="Skills that have been used infrequently")


class RecommendationItem(BaseModel):
    """A single skill recommendation."""

    skill_id: str = Field(description="Recommended skill identifier")
    reason: str = Field(description="Explanation for the recommendation")
    priority: str = Field(description="Recommendation priority (high, medium, low)")


class RecommendationsResponse(BaseModel):
    """Response model for skill recommendations."""

    user_id: str = Field(description="User ID for which recommendations are generated")
    recommendations: list[RecommendationItem] = Field(
        description="List of recommended skills with reasons"
    )
    total_recommendations: int = Field(description="Total number of recommendations")
