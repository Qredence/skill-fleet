"""
FastAPI service layer.

This module contains service classes that bridge FastAPI routes to workflow orchestrators.
Each service handles a specific domain of operations.

Services:
    SkillService: Manages skill creation and retrieval
    ConversationalService: Handles chat/conversation operations
    TaxonomyService: Manages taxonomy operations
    QualityService: Handles quality assurance operations
    HITLService: Manages human-in-the-loop interactions

The service layer provides:
    - Clean separation between API routes and business logic
    - Reusable business logic for both API and CLI
    - Consistent interface to workflow orchestrators
"""

from __future__ import annotations

from .skill_service import SkillService

__all__ = ["SkillService"]
