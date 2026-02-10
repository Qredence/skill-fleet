"""
Pydantic schemas for API v1 endpoints.

This module contains request/response models for all v1 API endpoints.
These schemas provide type safety and automatic validation for API operations.

Schema modules:
    skills: Skill creation, validation, and refinement schemas
    conversational: Chat interface schemas
    taxonomy: Taxonomy management schemas
    quality: Quality assurance schemas
    optimization: Signature optimization schemas
    hitl: Human-in-the-loop interaction schemas
    models: Core job state models
"""

from __future__ import annotations

from .agent import AgentMessageRequest, AgentMessageResponse
from .conversational import (
    SendMessageRequest,
    SendMessageResponse,
    SessionHistoryResponse,
)
from .hitl import (
    QuestionOption,
    StructuredQuestion,
    StructureFixRequest,
    StructureFixSuggestion,
    normalize_questions,
)
from .models import (
    DeepUnderstandingState,
    JobState,
    TDDWorkflowState,
)
from .optimization import (
    AnalyzeFailuresRequest,
    AnalyzeFailuresResponse,
    CompareRequest,
    CompareResponse,
    ImproveRequest,
    ImproveResponse,
)
from .quality import (
    AssessQualityRequest,
    AssessQualityResponse,
    AutoFixRequest,
    AutoFixResponse,
    ValidateRequest,
    ValidateResponse,
)
from .skills import (
    CreateSkillRequest,
    CreateSkillResponse,
    RefineSkillRequest,
    RefineSkillResponse,
    SkillDetailResponse,
    ValidateSkillResponse,
)
from .taxonomy import (
    AdaptTaxonomyRequest,
    AdaptTaxonomyResponse,
    TaxonomyResponse,
    UpdateTaxonomyRequest,
    UserTaxonomyResponse,
)

__all__ = [
    # Job state models
    "TDDWorkflowState",
    "DeepUnderstandingState",
    "JobState",
    # HITL models
    "QuestionOption",
    "StructuredQuestion",
    "StructureFixSuggestion",
    "StructureFixRequest",
    "normalize_questions",
    # Skills schemas
    "CreateSkillRequest",
    "CreateSkillResponse",
    "SkillDetailResponse",
    "ValidateSkillResponse",
    "RefineSkillRequest",
    "RefineSkillResponse",
    # Conversational schemas
    "AgentMessageRequest",
    "AgentMessageResponse",
    "SendMessageRequest",
    "SendMessageResponse",
    "SessionHistoryResponse",
    # Taxonomy schemas
    "TaxonomyResponse",
    "UpdateTaxonomyRequest",
    "UserTaxonomyResponse",
    "AdaptTaxonomyRequest",
    "AdaptTaxonomyResponse",
    # Quality schemas
    "ValidateRequest",
    "ValidateResponse",
    "AssessQualityRequest",
    "AssessQualityResponse",
    "AutoFixRequest",
    "AutoFixResponse",
    # Optimization schemas
    "AnalyzeFailuresRequest",
    "AnalyzeFailuresResponse",
    "ImproveRequest",
    "ImproveResponse",
    "CompareRequest",
    "CompareResponse",
]
