"""V1 API router.

This module aggregates all v1 API routes into a single router.
The v1 API follows the structure outlined in the main restructure plan.

Routes are organized by domain:
- /api/v1/chat - Conversational interface
- /api/v1/skills - Skill creation and management
- /api/v1/taxonomy - Taxonomy management
- /api/v1/quality - Quality assurance
- /api/v1/optimization - Signature optimization
"""

from __future__ import annotations

from fastapi import APIRouter

from .conversational.router import router as conversational_router
from .optimization.router import router as optimization_router
from .quality.router import router as quality_router
from .skills.router import router as skills_router
from .taxonomy.router import router as taxonomy_router

router = APIRouter()

# Include sub-routers with prefixes
router.include_router(conversational_router, prefix="/chat", tags=["conversational"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])
router.include_router(taxonomy_router, prefix="/taxonomy", tags=["taxonomy"])
router.include_router(quality_router, prefix="/quality", tags=["quality"])
router.include_router(optimization_router, prefix="/optimization", tags=["optimization"])
