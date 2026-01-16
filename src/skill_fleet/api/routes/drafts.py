"""Draft lifecycle routes.

Skill creation is draft-first:
- Jobs write drafts under `skills/_drafts/<job_id>/...`
- Promotion into the real taxonomy is explicit
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...common.security import resolve_path_within_root
from ...taxonomy.manager import TaxonomyManager
from ..dependencies import SkillsRoot, TaxonomyManagerDep
from ..jobs import delete_job_session, get_job, save_job_session

router = APIRouter()


class PromoteDraftRequest(BaseModel):
    """Request model for promoting a draft."""

    overwrite: bool = Field(default=True, description="Overwrite existing skill if present")
    delete_draft: bool = Field(default=False, description="Delete draft after promotion")
    force: bool = Field(default=False, description="Force promotion even if validation failed")


class PromoteDraftResponse(BaseModel):
    """Response model for draft promotion."""

    job_id: str = Field(..., description="The job ID that was promoted")
    status: str = Field(default="promoted", description="Promotion status")
    final_path: str = Field(..., description="Final path where the skill was saved")


def _safe_rmtree(path: Path) -> None:
    """Safely remove a directory tree if it exists."""
    if path.exists():
        shutil.rmtree(path)


@router.post("/{job_id}/promote", response_model=PromoteDraftResponse)
async def promote_draft(
    job_id: str,
    request: PromoteDraftRequest,
    skills_root: SkillsRoot,
    taxonomy_manager: TaxonomyManagerDep,
) -> PromoteDraftResponse:
    """Validate and promote a job draft into the real taxonomy.

    This endpoint moves a draft skill from the staging area into the
    production taxonomy. The draft must have been created by a completed
    skill creation job.

    Args:
        job_id: The job ID whose draft should be promoted
        request: Promotion options (overwrite, delete_draft, force)
        skills_root: Root directory for skills (injected)

    Returns:
        PromoteDraftResponse with the final path

    Raises:
        HTTPException: 404 if job not found, 400 if job not completed or no draft,
                      409 if target exists and overwrite=false, 500 on promotion failure
    """
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed (status={job.status})")

    if job.draft_path is None or job.intended_taxonomy_path is None:
        raise HTTPException(status_code=400, detail="Job does not have a draft to promote")

    if job.validation_passed is False and not request.force:
        raise HTTPException(
            status_code=400,
            detail="Draft failed validation. Pass force=true to promote anyway.",
        )

    try:
        target_dir = resolve_path_within_root(skills_root, job.intended_taxonomy_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target path: {e}")

    if target_dir.exists() and not request.overwrite:
        raise HTTPException(status_code=409, detail="Target skill already exists (overwrite=false)")

    try:
        if target_dir.exists() and request.overwrite:
            _safe_rmtree(target_dir)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(Path(job.draft_path), target_dir, dirs_exist_ok=request.overwrite)

        # Update taxonomy meta/cache by loading metadata (best-effort).
        try:
            taxonomy_manager._ensure_all_skills_loaded()
        except Exception:
            # Taxonomy update is optional, continue even if it fails
            pass

        job.promoted = True
        job.final_path = str(target_dir)
        job.saved_path = job.final_path

        if request.delete_draft:
            # Remove the whole job draft root directory (…/skills/_drafts/<job_id>).
            job_root = skills_root / "_drafts" / job_id
            _safe_rmtree(job_root)
            delete_job_session(job_id)

        save_job_session(job_id)

        return PromoteDraftResponse(
            job_id=job_id,
            status="promoted",
            final_path=job.final_path,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion failed: {e}") from e
