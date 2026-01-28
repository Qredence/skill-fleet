"""Pydantic schemas for taxonomy management API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaxonomyResponse(BaseModel):
    """Response model for retrieving taxonomy."""

    taxonomy: dict[str, Any]
    total_skills: int
    last_updated: str


class UpdateTaxonomyRequest(BaseModel):
    """Request body for updating taxonomy."""

    updates: dict[str, Any] = Field(..., description="Taxonomy updates")
    user_id: str = Field(default="default", description="User ID for context")


class UserTaxonomyResponse(BaseModel):
    """Response model for retrieving user-specific taxonomy."""

    user_id: str
    taxonomy: dict[str, Any]
    adapted_categories: list[str]
    usage_stats: dict[str, Any]


class AdaptTaxonomyRequest(BaseModel):
    """Request body for adapting taxonomy to user."""

    user_id: str = Field(..., description="User ID")
    query_history: list[str] = Field(default=[], description="Recent user queries")
    interaction_data: dict[str, Any] = Field(
        default_factory=dict, description="User interaction patterns"
    )


class AdaptTaxonomyResponse(BaseModel):
    """Response model for adapting taxonomy."""

    user_id: str
    adapted_taxonomy: dict[str, Any]
    suggestions: list[str]
    confidence_scores: dict[str, float]
