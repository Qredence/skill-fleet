"""
V1 API router.

This module aggregates all v1 API routes into a single router.
The v1 API follows the structure outlined in the main restructure plan.

Routes are organized by domain:
- /api/v1/chat - Conversational interface
- /api/v1/skills - Skill creation and management
- /api/v1/taxonomy - Taxonomy management
- /api/v1/quality - Quality assurance
- /api/v1/optimization - Signature optimization
- /api/v1/hitl - Human-in-the-loop interactions
- /api/v1/jobs - Job status and management
- /api/v1/drafts - Draft promotion
"""

from __future__ import annotations

from fastapi import APIRouter

from .conversational import router as conversational_router
from .drafts import router as drafts_router
from .hitl import router as hitl_router
from .jobs import router as jobs_router
from .optimization import router as optimization_router
from .quality import router as quality_router
from .skills import router as skills_router
from .taxonomy import router as taxonomy_router

router = APIRouter()

# Include sub-routers with prefixes
router.include_router(conversational_router, prefix="/chat", tags=["conversational"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy_router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(quality_router, prefix="/quality", tags=["quality"])
router.include_router(optimization_router, prefix="/optimization", tags=["optimization"])
router.include_router(hitl_router, prefix="/hitl", tags=["hitl"])
router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
router.include_router(drafts_router, prefix="/drafts", tags=["drafts"])
