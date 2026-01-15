"""Draft lifecycle routes.

Skill creation is draft-first:
- Jobs write drafts under `skills/_drafts/<job_id>/...`
- Promotion into the real taxonomy is explicit
"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...taxonomy.manager import TaxonomyManager
from ..jobs import delete_job_session, get_job, save_job_session

router = APIRouter()


class PromoteDraftRequest(BaseModel):
    """Request model for promoting a draft."""

    overwrite: bool = True
    delete_draft: bool = False
    force: bool = False


def _safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


@router.post("/{job_id}/promote")
async def promote_draft(job_id: str, request: PromoteDraftRequest):
    """Validate and promote a job draft into the real taxonomy."""
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

    skills_root = Path("skills")
    try:
        # Derive skills root from the draft path (…/skills/_drafts/...)
        draft_path = Path(job.draft_path)
        for parent in draft_path.parents:
            if parent.name == "skills":
                skills_root = parent
                break
    except Exception:
        pass

    target_dir = skills_root / job.intended_taxonomy_path

    if target_dir.exists() and not request.overwrite:
        raise HTTPException(status_code=409, detail="Target skill already exists (overwrite=false)")

    try:
        if target_dir.exists() and request.overwrite:
            _safe_rmtree(target_dir)

        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(Path(job.draft_path), target_dir, dirs_exist_ok=request.overwrite)

        # Update taxonomy meta/cache by loading metadata (best-effort).
        try:
            TaxonomyManager(skills_root)._ensure_all_skills_loaded()
        except Exception:
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

        return {
            "job_id": job_id,
            "status": "promoted",
            "final_path": job.final_path,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Promotion failed: {e}") from e
