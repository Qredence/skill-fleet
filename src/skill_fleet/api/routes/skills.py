"""Skill creation routes."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ...core.models import SkillCreationResult
from ...core.dspy import SkillCreationProgram
from ...taxonomy.manager import TaxonomyManager
from ..jobs import JOBS, create_job, wait_for_hitl_response

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateSkillRequest(BaseModel):
    """Request body for creating a new skill."""

    task_description: str
    user_id: str = "default"


# Skills root directory (configurable via env var)
SKILLS_ROOT = Path(os.environ.get("SKILL_FLEET_SKILLS_ROOT", "skills"))


def _save_skill_to_taxonomy(result: SkillCreationResult) -> str | None:
    """Save a completed skill to the taxonomy.

    Args:
        result: SkillCreationResult from the workflow

    Returns:
        Path where skill was saved, or None if save failed
    """
    if not result.skill_content or not result.metadata:
        logger.warning("Cannot save skill: missing content or metadata")
        return None

    try:
        manager = TaxonomyManager(SKILLS_ROOT)

        # Extract metadata for registration
        metadata = result.metadata
        taxonomy_path = (
            metadata.taxonomy_path if hasattr(metadata, "taxonomy_path") else metadata.skill_id
        )

        # Sanitize the provided taxonomy path to avoid path traversal or
        # accidental writes outside of the configured SKILLS_ROOT. We only
        # allow a simple relative path composed of alphanumeric, hyphen,
        # underscore and forward-slash segments (no .. segments, no absolute
        # paths). If the provided path is unsafe, reject the save.
        def _sanitize_taxonomy_path(path: str) -> str | None:
            if not path:
                return None
            # Reject absolute paths and parent-directory traversal
            if path.startswith("/") or ".." in path:
                return None
            # Normalize and ensure it remains within SKILLS_ROOT when joined
            normalized = Path(path).as_posix().strip("/")
            # Simple character whitelist for each path segment
            for segment in normalized.split("/"):
                if not segment:
                    return None
                # allow letters, numbers, hyphen, underscore
                if not all(c.isalnum() or c in "-_" for c in segment):
                    return None
            return normalized

        safe_taxonomy_path = _sanitize_taxonomy_path(taxonomy_path)
        if not safe_taxonomy_path:
            logger.error("Unsafe taxonomy path provided by workflow: %s", taxonomy_path)
            return None

        # Never overwrite an existing skill via the API auto-save path.
        if manager.skill_exists(safe_taxonomy_path):
            full_path = SKILLS_ROOT / safe_taxonomy_path
            logger.info(f"Skill already exists; skipping save: {full_path}")
            return str(full_path)

        # Build metadata dict for register_skill
        meta_dict = {
            "skill_id": metadata.skill_id,
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "type": metadata.type,
            "tags": metadata.tags if hasattr(metadata, "tags") else [],
            "dependencies": metadata.dependencies if hasattr(metadata, "dependencies") else [],
        }

        # Evolution tracking
        evolution = {
            "created_by": "skill-fleet-api",
            "workflow": "SkillCreationProgram",
            "validation_score": result.validation_report.score
            if result.validation_report
            else None,
        }

        # Register the skill (saves SKILL.md and metadata.json)
        success = manager.register_skill(
            path=safe_taxonomy_path,
            metadata=meta_dict,
            content=result.skill_content,
            evolution=evolution,
        )

        if success:
            full_path = SKILLS_ROOT / safe_taxonomy_path
            logger.info(f"Skill saved successfully to: {full_path}")
            return str(full_path)
        else:
            logger.error(f"Failed to register skill at path: {taxonomy_path}")
            return None

    except Exception as e:
        logger.error(f"Error saving skill to taxonomy: {e}", exc_info=True)
        return None


async def run_skill_creation(job_id: str, task_description: str, user_id: str):
    """Execute the end-to-end skill creation workflow as a background job.

    This coroutine is intended to be scheduled via FastAPI's ``BackgroundTasks``
    mechanism (see the ``/create`` route in this module). When invoked, it
    retrieves the corresponding job record from the global ``JOBS`` registry
    using ``job_id`` and drives the full lifecycle of a single skill creation
    request.
    """

    job = JOBS[job_id]
    job.status = "running"

    async def hitl_callback(interaction_type: str, data: dict):
        """Handle Human-in-the-Loop interactions during skill creation.

        The callback updates the job state to indicate a pending HITL
        interaction, then awaits the response posted to the HITL endpoint for
        this job. If a timeout occurs, the job is marked failed and the
        TimeoutError is propagated.
        """

        job.status = "pending_hitl"
        job.hitl_type = interaction_type
        job.hitl_data = data

        # Wait for response via /hitl/{job_id}/response
        try:
            response = await wait_for_hitl_response(job_id)
            job.status = "running"
            return response
        except TimeoutError:
            job.status = "failed"
            job.error = "HITL interaction timed out (user took too long to respond)"
            raise

    try:
        program = SkillCreationProgram()
        result = await program.aforward(
            task_description=task_description,
            user_context={"user_id": user_id},
            taxonomy_structure="{}",  # JSON string for taxonomy structure
            existing_skills="[]",  # JSON string for existing skills list
            hitl_callback=hitl_callback,
        )

        if result.status == "failed":
            job.status = "failed"
            job.error = result.error
        else:
            job.status = result.status
            job.result = result

            # Auto-save completed skills to taxonomy
            if result.status == "completed" and result.skill_content:
                saved_path = _save_skill_to_taxonomy(result)
                if saved_path:
                    job.saved_path = saved_path
                    logger.info(f"Job {job_id} completed and skill saved to: {saved_path}")
                else:
                    logger.warning(f"Job {job_id} completed but skill could not be saved")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job.status = "failed"
        job.error = str(e)


@router.post("/create")
async def create(request: CreateSkillRequest, background_tasks: BackgroundTasks):
    """Initiate a new skill creation job."""
    if not request.task_description:
        raise HTTPException(status_code=400, detail="task_description is required")

    job_id = create_job()
    background_tasks.add_task(run_skill_creation, job_id, request.task_description, request.user_id)

    return {"job_id": job_id, "status": "accepted"}
