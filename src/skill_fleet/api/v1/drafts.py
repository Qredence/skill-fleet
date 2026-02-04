"""
Draft lifecycle routes for v1 API.

This module provides endpoints for draft promotion.
Skill creation is draft-first: jobs write drafts under `skills/_drafts/<job_id>/...`
Promotion into the real taxonomy is explicit.

Endpoints:
    POST /api/v1/drafts/{job_id}/promote - Promote a draft to the taxonomy
"""

from __future__ import annotations

import contextlib
import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from skill_fleet.common.security import resolve_path_within_root, sanitize_taxonomy_path

from ..dependencies import SkillsRoot, TaxonomyManagerDep
from ..services.jobs import delete_job_session, get_job, save_job_session

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


def _resolve_skills_root(skills_root: SkillsRoot) -> Path:
    """
    Resolve and validate the injected skills root.

    Args:
        skills_root: Root directory for skills (injected)

    Returns:
        Resolved absolute path

    """
    try:
        if not skills_root.is_absolute():
            raise ValueError("skills_root must be an absolute path")
        skills_root_resolved = skills_root.resolve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid skills root: {e}") from e
    return skills_root_resolved


def _validate_job_for_promotion(job, request: PromoteDraftRequest) -> None:
    """
    Validate job state for draft promotion.

    Args:
        job: JobState from storage
        request: Promotion request

    """
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job is not completed (status={job.status})")

    if job.draft_path is None or job.intended_taxonomy_path is None:
        raise HTTPException(status_code=400, detail="Job does not have a draft to promote")

    if job.validation_passed is False and not request.force:
        raise HTTPException(
            status_code=400,
            detail="Draft failed validation. Pass force=true to promote anyway.",
        )


def _resolve_target_dir(
    skills_root_resolved: Path,
    intended_taxonomy_path: str,
    overwrite: bool,
) -> Path:
    """
    Resolve and validate the target taxonomy directory.

    Args:
        skills_root_resolved: Absolute skills root
        intended_taxonomy_path: Job's intended taxonomy path
        overwrite: Whether overwrite is allowed

    Returns:
        Resolved target directory

    """
    try:
        safe_path = sanitize_taxonomy_path(intended_taxonomy_path)
        if not safe_path:
            raise ValueError("Invalid taxonomy path")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid target path: {e}") from e

    try:
        target_dir = resolve_path_within_root(skills_root_resolved, safe_path)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid target path: {e}") from e

    if target_dir.exists() and not overwrite:
        raise HTTPException(status_code=409, detail="Target skill already exists (overwrite=false)")

    return target_dir


def _resolve_draft_path(skills_root_resolved: Path, draft_path: str) -> Path:
    """
    Resolve and validate the draft path to prevent traversal.

    Args:
        skills_root_resolved: Absolute skills root
        draft_path: Draft path from job state

    Returns:
        Resolved draft path

    """
    drafts_dir = skills_root_resolved / "_drafts"
    try:
        draft_path_obj = Path(draft_path)
        if not draft_path_obj.is_absolute():
            raise ValueError("Draft path must be absolute")

        draft_path_resolved = draft_path_obj.resolve(strict=False)
        drafts_dir_resolved = drafts_dir.resolve()

        drafts_str = os.fspath(drafts_dir_resolved)
        draft_str = os.fspath(draft_path_resolved)
        if os.path.commonpath([drafts_str, draft_str]) != drafts_str:
            raise ValueError("Draft path escapes drafts directory")

        draft_path_resolved.relative_to(drafts_dir_resolved)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid draft path: {e}") from e

    return draft_path_resolved


@router.post("/{job_id}/promote")
async def promote_draft(
    job_id: str,
    request: PromoteDraftRequest,
    skills_root: SkillsRoot,
    taxonomy_manager: TaxonomyManagerDep,
) -> PromoteDraftResponse:
    """
    Validate and promote a job draft into the real taxonomy.

    This endpoint moves a draft skill from the staging area into the
    production taxonomy. The draft must have been created by a completed
    skill creation job.

    Args:
        job_id: The job ID whose draft should be promoted
        request: Promotion options (overwrite, delete_draft, force)
        skills_root: Root directory for skills (injected)
        taxonomy_manager: Taxonomy manager for path resolution and validation

    Returns:
        PromoteDraftResponse with the final path

    Raises:
        HTTPException: 404 if job not found, 400 if job not completed or no draft,
                      409 if target exists and overwrite=false, 500 on promotion failure

    """
    skills_root_resolved = _resolve_skills_root(skills_root)

    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    _validate_job_for_promotion(job, request)
    assert job.intended_taxonomy_path is not None
    assert job.draft_path is not None

    target_dir = _resolve_target_dir(
        skills_root_resolved,
        job.intended_taxonomy_path,
        request.overwrite,
    )

    draft_path_resolved = _resolve_draft_path(skills_root_resolved, job.draft_path)

    try:
        # Transaction-safe promotion: use temporary directory for atomicity
        with tempfile.TemporaryDirectory(prefix="skill_promote_") as temp_dir:
            temp_dir_path = Path(temp_dir)

            backup_path = temp_dir_path / "backup"
            needs_restore = False

            if target_dir.exists() and request.overwrite:
                shutil.move(str(target_dir), str(backup_path))
                needs_restore = True
            elif target_dir.exists():
                raise HTTPException(
                    status_code=409, detail="Target skill already exists (overwrite=false)"
                )

            try:
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(draft_path_resolved, target_dir, dirs_exist_ok=request.overwrite)

                if backup_path.exists():
                    shutil.rmtree(backup_path)

            except Exception:
                if needs_restore and backup_path.exists():
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    shutil.move(str(backup_path), str(target_dir))
                raise

        # Update taxonomy meta/cache by loading metadata (best-effort)
        # Refresh cache by reloading always-loaded skills
        with contextlib.suppress(Exception):
            taxonomy_manager._load_always_loaded_skills()

        job.promoted = True
        job.final_path = str(target_dir)
        job.saved_path = job.final_path

        if request.delete_draft:
            job_root = skills_root_resolved / "_drafts" / job_id
            _safe_rmtree(job_root)
            delete_job_session(job_id)
        else:
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
