"""Draft lifecycle routes.

Skill creation is draft-first:
- Jobs write drafts under `skills/_drafts/<job_id>/...`
- Promotion into the real taxonomy is explicit
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...common.security import resolve_path_within_root
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
    # Normalize and validate the injected skills root to ensure it is an absolute,
    # filesystem-rooted path before using it in any filesystem operations.
    try:
        skills_root_resolved = skills_root.resolve()
        if not skills_root_resolved.is_absolute():
            raise ValueError("skills_root must be an absolute path")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid skills root: {e}") from e

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
        # Ensure the target directory is resolved within the normalized skills root.
        target_dir = resolve_path_within_root(skills_root_resolved, job.intended_taxonomy_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target path: {e}") from e

    if target_dir.exists() and not request.overwrite:
        raise HTTPException(status_code=409, detail="Target skill already exists (overwrite=false)")

    # Validate draft_path to prevent path traversal attacks
    # The draft_path should be within the drafts directory
    drafts_dir = skills_root_resolved / "_drafts"
    try:
        # Validate that draft_path is a safe absolute path and resolve it
        draft_path_obj = Path(job.draft_path)
        if not draft_path_obj.is_absolute():
            raise ValueError("Draft path must be absolute")

        # Resolve both paths and check containment
        draft_path_resolved = draft_path_obj.resolve(strict=False)
        drafts_dir_resolved = drafts_dir.resolve()

        # Verify the draft path is within the drafts directory using commonpath
        drafts_str = os.fspath(drafts_dir_resolved)
        draft_str = os.fspath(draft_path_resolved)
        if os.path.commonpath([drafts_str, draft_str]) != drafts_str:
            raise ValueError("Draft path escapes drafts directory")

        # Also verify using relative_to for semantic clarity
        draft_path_resolved.relative_to(drafts_dir_resolved)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid draft path: {e}") from e

    try:
        if target_dir.exists() and request.overwrite:
            _safe_rmtree(target_dir)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(draft_path_resolved, target_dir, dirs_exist_ok=request.overwrite)

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
            job_root = skills_root_resolved / "_drafts" / job_id
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
