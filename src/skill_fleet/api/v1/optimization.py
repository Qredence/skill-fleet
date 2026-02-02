"""
Signature optimization routes for v1 API.

This module provides endpoints for signature optimization operations.
These routes use signature optimization workflow orchestrators.

Endpoints:
    POST /api/v1/optimization/analyze - Analyze signature failures
    POST /api/v1/optimization/improve - Propose signature improvements
    POST /api/v1/optimization/compare - A/B test signatures

Status: STUB ENDPOINTS - Returns 503 Service Unavailable.
TODO(2026-03): Either implement these endpoints using the new workflow
architecture or remove this module entirely.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from ..exceptions import ServiceUnavailableException
from ..schemas.optimization import (
    AnalyzeFailuresRequest,
    AnalyzeFailuresResponse,
    CompareRequest,
    CompareResponse,
    ImproveRequest,
    ImproveResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_UNAVAILABLE_MSG = (
    "Signature optimization is temporarily unavailable. "
    "Migration to new workflow architecture in progress."
)


@router.post("/analyze", response_model=AnalyzeFailuresResponse)
async def analyze_failures(request: AnalyzeFailuresRequest) -> AnalyzeFailuresResponse:
    """
    Analyze signature failures to identify root causes.

    Status: STUB - Returns 503 Service Unavailable.
    """
    raise ServiceUnavailableException(_UNAVAILABLE_MSG)


@router.post("/improve", response_model=ImproveResponse)
async def improve_signature(request: ImproveRequest) -> ImproveResponse:
    """
    Propose improvements for a signature.

    Status: STUB - Returns 503 Service Unavailable.
    """
    raise ServiceUnavailableException(_UNAVAILABLE_MSG)


@router.post("/compare", response_model=CompareResponse)
async def compare_signatures(request: CompareRequest) -> CompareResponse:
    """
    A/B test two signatures against each other.

    Status: STUB - Returns 503 Service Unavailable.
    """
    raise ServiceUnavailableException(_UNAVAILABLE_MSG)
