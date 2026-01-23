"""Pydantic schemas for signature optimization API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeFailuresRequest(BaseModel):
    """Request body for analyzing signature failures."""

    signature_name: str = Field(..., description="Name of the signature to analyze")
    failure_examples: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Example failures with inputs and expected outputs",
    )


class AnalyzeFailuresResponse(BaseModel):
    """Response model for failure analysis."""

    signature_name: str
    analysis: dict[str, Any]
    root_causes: list[str]
    suggested_improvements: list[str]


class ImproveRequest(BaseModel):
    """Request body for proposing signature improvements."""

    signature_name: str = Field(..., description="Name of the signature to improve")
    current_version: str | None = Field(default=None, description="Current signature version")
    improvement_targets: list[str] = Field(
        default_factory=list,
        description="Specific areas to improve",
    )


class ImproveResponse(BaseModel):
    """Response model for improvement proposals."""

    signature_name: str
    proposed_changes: dict[str, Any]
    expected_impact: str
    confidence: float
    test_cases: list[dict[str, Any]]


class CompareRequest(BaseModel):
    """Request body for A/B testing signatures."""

    signature_a_name: str = Field(..., description="Name of signature A")
    signature_a_version: str | None = Field(default=None, description="Version of signature A")
    signature_b_name: str = Field(..., description="Name of signature B")
    signature_b_version: str | None = Field(default=None, description="Version of signature B")
    test_inputs: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Test inputs for comparison",
    )


class CompareResponse(BaseModel):
    """Response model for signature comparison."""

    signature_a: dict[str, Any]
    signature_b: dict[str, Any]
    winner: str | None
    metrics: dict[str, float]
    recommendation: str
