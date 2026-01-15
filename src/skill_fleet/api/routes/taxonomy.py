"""Taxonomy operation routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..dependencies import TaxonomyManagerDep

router = APIRouter()


class SkillSummary(BaseModel):
    """Summary of a skill for listing."""

    skill_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    type: str = "technical"


class ListSkillsResponse(BaseModel):
    """Response model for listing skills."""

    skills: list[SkillSummary] = Field(default_factory=list)
    total: int = 0


@router.get("/", response_model=ListSkillsResponse)
async def list_skills(manager: TaxonomyManagerDep) -> ListSkillsResponse:
    """List all available skills in the taxonomy."""
    manager._ensure_all_skills_loaded()
    skills = [
        SkillSummary(
            skill_id=meta.skill_id,
            name=meta.name,
            description=meta.description,
            version=meta.version,
            type=meta.type,
        )
        for meta in manager.metadata_cache.values()
    ]
    return ListSkillsResponse(skills=skills, total=len(skills))


class TaxonomyTreeNode(BaseModel):
    """A node in the taxonomy tree."""

    name: str
    path: str
    children: list[TaxonomyTreeNode] = Field(default_factory=list)
    skill_count: int = 0


class TaxonomyTreeResponse(BaseModel):
    """Response model for taxonomy tree."""

    tree: list[TaxonomyTreeNode] = Field(default_factory=list)


@router.get("/tree", response_model=TaxonomyTreeResponse)
async def get_taxonomy_tree(manager: TaxonomyManagerDep) -> TaxonomyTreeResponse:
    """Get the taxonomy tree structure."""
    # Build tree from skills root directory structure
    tree: list[TaxonomyTreeNode] = []
    skills_root = manager.skills_root

    for item in sorted(skills_root.iterdir()):
        if item.is_dir() and not item.name.startswith((".", "_")):
            node = _build_tree_node(item, skills_root)
            tree.append(node)

    return TaxonomyTreeResponse(tree=tree)


def _build_tree_node(path: Any, root: Any) -> TaxonomyTreeNode:
    """Recursively build a tree node from a directory."""
    rel_path = str(path.relative_to(root))
    children: list[TaxonomyTreeNode] = []
    skill_count = 0

    for item in sorted(path.iterdir()):
        if item.is_dir() and not item.name.startswith((".", "_")):
            if (item / "metadata.json").exists():
                skill_count += 1
            else:
                child = _build_tree_node(item, root)
                children.append(child)
                skill_count += child.skill_count

    return TaxonomyTreeNode(
        name=path.name,
        path=rel_path,
        children=children,
        skill_count=skill_count,
    )
