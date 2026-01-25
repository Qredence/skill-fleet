"""
Taxonomy management routes for v1 API.

This module provides endpoints for taxonomy operations.
These routes use taxonomy service for managing skills taxonomy.

Endpoints:
    GET  /api/v1/taxonomy - Get global taxonomy
    POST /api/v1/taxonomy - Update taxonomy
    GET  /api/v1/taxonomy/user/{user_id} - Get user-specific taxonomy
    POST /api/v1/taxonomy/user/{user_id}/adapt - Adapt taxonomy to user
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Path

from .....api.exceptions import NotFoundException
from .....api.schemas.taxonomy import (
    AdaptTaxonomyRequest,
    AdaptTaxonomyResponse,
    TaxonomyResponse,
    UpdateTaxonomyRequest,
    UserTaxonomyResponse,
)
from .....app.dependencies import TaxonomyManagerDep
from .....app.services.cached_taxonomy import get_cached_taxonomy_service

logger = logging.getLogger(__name__)

router = APIRouter()

if TYPE_CHECKING:
    from .....taxonomy.manager import TaxonomyManager


@router.get("/", response_model=TaxonomyResponse)
async def get_taxonomy(taxonomy_manager: TaxonomyManagerDep) -> TaxonomyResponse:
    """
    Get the global skills taxonomy.

    Args:
        taxonomy_manager: Injected TaxonomyManager for taxonomy access

    Returns:
        TaxonomyResponse: Taxonomy structure, total skills, and last updated timestamp

    """
    try:
        # Use cached taxonomy service for performance
        cached_service = get_cached_taxonomy_service(taxonomy_manager)
        result = cached_service.get_global_taxonomy()

        return TaxonomyResponse(
            taxonomy={
                "structure": result["structure"],
                "domains": result["domains"],
                "categories": result["categories"],
            },
            total_skills=result["total_skills"],
            last_updated=result["last_updated"],
        )

    except Exception as e:
        logger.exception(f"Error getting taxonomy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve taxonomy: {e}"
        ) from e


@router.post("/", response_model=dict[str, str])
async def update_taxonomy(
    request: UpdateTaxonomyRequest,
    taxonomy_manager: TaxonomyManagerDep,
) -> dict[str, str]:
    """
    Update the global taxonomy.

    Args:
        request: Taxonomy update request
        taxonomy_manager: Injected TaxonomyManager for taxonomy access

    Returns:
        Dictionary with status message

    Note:
        Currently returns success without actual updates.
        Full implementation would apply updates to taxonomy_meta.json
        and rebuild the taxonomy index.
        Cache is invalidated to force refresh on next read.

    """
    try:
        # Verify taxonomy manager is accessible
        _ = taxonomy_manager.meta

        # TODO: Implement actual update logic:
        # - Merge updates into taxonomy structure
        # - Validate new categories/paths
        # - Update taxonomy_meta.json
        # - Rebuild index

        logger.info(f"Taxonomy update requested by user {request.user_id}: {list(request.updates.keys())}")

        # Invalidate cache to force refresh
        cached_service = get_cached_taxonomy_service(taxonomy_manager)
        invalidated = cached_service.invalidate_taxonomy()
        logger.info(f"Invalidated {invalidated} taxonomy cache entries")

        return {
            "status": "updated",
            "message": "Taxonomy update processed",
        }

    except Exception as e:
        logger.exception(f"Error updating taxonomy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update taxonomy: {e}"
        ) from e


@router.get("/user/{user_id}", response_model=UserTaxonomyResponse)
async def get_user_taxonomy(
    user_id: str = Path(..., description="User ID"),
    taxonomy_manager: TaxonomyManagerDep = None,
) -> UserTaxonomyResponse:
    """
    Get user-specific taxonomy adaptation.

    Args:
        user_id: Unique user identifier
        taxonomy_manager: Injected TaxonomyManager for taxonomy access

    Returns:
        UserTaxonomyResponse: User-specific taxonomy with adaptations and stats

    """
    try:
        # Use cached taxonomy service for performance
        cached_service = get_cached_taxonomy_service(taxonomy_manager)
        result = cached_service.get_user_taxonomy(user_id)

        # Build usage stats
        usage_stats = {
            "total_mounted": len(result["mounted_skills"]),
            "categories_mounted": len(result["adapted_categories"]),
            "last_updated": datetime.now().isoformat(),
        }

        return UserTaxonomyResponse(
            user_id=user_id,
            taxonomy={
                "global_structure": result["global_structure"],
                "mounted_skills": result["mounted_skills"],
                "user_id": user_id,
            },
            adapted_categories=result["adapted_categories"],
            usage_stats=usage_stats,
        )

    except Exception as e:
        logger.exception(f"Error getting user taxonomy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user taxonomy: {e}"
        ) from e


@router.post("/user/{user_id}/adapt", response_model=AdaptTaxonomyResponse)
async def adapt_taxonomy(
    user_id: str = Path(..., description="User ID"),
    request: AdaptTaxonomyRequest = None,
    taxonomy_manager: TaxonomyManagerDep = None,
) -> AdaptTaxonomyResponse:
    """
    Adapt taxonomy to user based on their usage patterns.

    Args:
        user_id: Unique user identifier
        request: Adaptation request with query history and interaction data
        taxonomy_manager: Injected TaxonomyManager for taxonomy access

    Returns:
        AdaptTaxonomyResponse: Adapted taxonomy with suggestions and confidence

    """
    try:
        # Use cached taxonomy service for performance
        cached_service = get_cached_taxonomy_service(taxonomy_manager)

        # Get relevant branches based on query history
        if request and request.query_history:
            # Use recent queries to find relevant taxonomy branches
            query_text = " ".join(request.query_history[-5:])  # Last 5 queries
            relevant_branches = cached_service.get_relevant_branches(query_text)
        else:
            # Fallback to full taxonomy from cache
            result = cached_service.get_global_taxonomy()
            relevant_branches = result["structure"]

        # Get mounted skills from cached user taxonomy
        user_taxonomy_result = cached_service.get_user_taxonomy(user_id)
        mounted_skills = user_taxonomy_result["mounted_skills"]

        # Build adapted taxonomy
        adapted_taxonomy = {
            "relevant_branches": relevant_branches,
            "mounted_skills": mounted_skills,
            "query_context": query_text if request and request.query_history else "",
        }

        # Generate suggestions based on interaction data
        suggestions = []
        confidence_scores = {}

        if request and request.interaction_data:
            # Extract patterns from interaction data
            frequent_domains = request.interaction_data.get("frequent_domains", [])
            for domain in frequent_domains:
                suggestions.append(f"Explore more skills in {domain}")
                confidence_scores[f"domain_{domain}"] = 0.8

        # Add default suggestions if none generated
        if not suggestions:
            suggestions = [
                "Explore skills based on your recent queries",
                "Consider mounting frequently used skills",
            ]

        # Add default confidence scores
        if not confidence_scores:
            confidence_scores = {
                "overall_confidence": 0.7,
                "taxonomy_match": 0.6,
            }

        return AdaptTaxonomyResponse(
            user_id=user_id,
            adapted_taxonomy=adapted_taxonomy,
            suggestions=suggestions,
            confidence_scores=confidence_scores,
        )

    except Exception as e:
        logger.exception(f"Error adapting taxonomy: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to adapt taxonomy: {e}"
        ) from e
