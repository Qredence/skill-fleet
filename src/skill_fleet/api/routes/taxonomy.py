"""Taxonomy operation routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from ...taxonomy.manager import TaxonomyManager

router = APIRouter()


@router.get("/")
async def list_skills():
    """List all available skills in the taxonomy."""
    # Using default path for now
    manager = TaxonomyManager(Path("skills"))
    skills = manager.list_skills()
    return {"skills": [s.dict() for s in skills]}
