"""Skill creation routes."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from ...common.security import sanitize_taxonomy_path
from ...core.dspy import SkillCreationProgram
from ...core.models import SkillCreationResult
from ...taxonomy.manager import TaxonomyManager
from ..dependencies import TaxonomyManagerDep, get_drafts_root, get_skills_root
from ..jobs import JOBS, create_job, save_job_session, wait_for_hitl_response

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateSkillRequest(BaseModel):
    """Request body for creating a new skill."""

    task_description: str = Field(..., description="Description of the skill to create")
    user_id: str = Field(default="default", description="User ID for context")


class CreateSkillResponse(BaseModel):
    """Response model for skill creation."""

    job_id: str = Field(..., description="Unique identifier for the background job")
    status: str = Field(default="accepted", description="Initial job status")


class SkillDetailResponse(BaseModel):
    """Detailed information about a skill."""

    skill_id: str
    name: str
    description: str
    version: str
    type: str
    metadata: dict[str, Any]
    content: str | None = None


@router.get("/{path:path}", response_model=SkillDetailResponse)
async def get_skill(path: str, manager: TaxonomyManagerDep) -> SkillDetailResponse:
    """Get details for a skill by its path or ID (supports aliases)."""
    # 1. Resolve Location (Handles Aliases + Legacy Paths via Manager)
    try:
        canonical_path = manager.resolve_skill_location(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Skill '{path}' not found") from e

    # 2. Load Metadata
    meta = manager.get_skill_metadata(canonical_path) or manager._try_load_skill_by_id(
        canonical_path
    )
    if not meta:
        raise HTTPException(status_code=404, detail="Skill metadata not found")

    # 3. Load Content
    content = None
    if meta.path.name == "metadata.json":
        md_path = meta.path.parent / "SKILL.md"
        if md_path.exists():
            content = md_path.read_text(encoding="utf-8")

    # Convert dataclass to dict for response
    # We need to construct metadata dict safely
    meta_dict = {
        "weight": meta.weight,
        "load_priority": meta.load_priority,
        "dependencies": meta.dependencies,
        "capabilities": meta.capabilities,
        "always_loaded": meta.always_loaded,
    }

    return SkillDetailResponse(
        skill_id=meta.skill_id,
        name=meta.name,
        description=meta.description,
        version=meta.version,
        type=meta.type,
        metadata=meta_dict,
        content=content,
    )


_FENCE_START_RE = re.compile(r"^\s*```(?P<lang>[a-zA-Z0-9_+-]*)\s*$")
_HEADING_BACKTICK_RE = re.compile(r"^\s{0,3}#{2,6}\s+`(?P<name>[^`]+)`\s*$")


def _safe_single_filename(candidate: str) -> str | None:
    """Return a safe single-path filename or None.

    LLM output is untrusted; keep this strict to prevent path traversal.
    """

    name = candidate.strip()
    if not name:
        return None
    if "/" in name or "\\" in name:
        return None
    if name.startswith("."):
        return None
    if not all(c.isalnum() or c in "._-" for c in name):
        return None
    return name


def _extract_named_file_code_blocks(skill_md: str) -> dict[str, str]:
    """Extract code blocks that are explicitly labeled with a backticked filename heading.

    Example:
        ### `pytest.ini`
        ```ini
        ...
        ```
    """

    assets: dict[str, str] = {}
    lines = skill_md.splitlines()
    i = 0
    while i < len(lines):
        m = _HEADING_BACKTICK_RE.match(lines[i])
        if not m:
            i += 1
            continue

        raw_name = m.group("name")
        filename = _safe_single_filename(raw_name)
        if not filename:
            i += 1
            continue

        # Scan forward until we find the next fenced block (allow brief prose between).
        j = i + 1
        fence_line = None
        while j < len(lines):
            if lines[j].lstrip().startswith("#"):
                break
            if _FENCE_START_RE.match(lines[j]):
                fence_line = j
                break
            j += 1
        if fence_line is None:
            i += 1
            continue

        j = fence_line + 1
        body: list[str] = []
        while j < len(lines) and not lines[j].strip().startswith("```"):
            body.append(lines[j])
            j += 1

        if j < len(lines) and lines[j].strip().startswith("```"):
            assets[filename] = "\n".join(body).rstrip() + "\n"
            i = j + 1
            continue

        i += 1

    return assets


def _extract_usage_example_code_blocks(skill_md: str) -> dict[str, str]:
    """Extract fenced code blocks under the '## Usage Examples' section.

    Writes as simple `example_N.<ext>` files (best-effort).
    """

    lines = skill_md.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == "## Usage Examples":
            start = idx + 1
            break
    if start is None:
        return {}

    end = len(lines)
    for idx in range(start, len(lines)):
        # Stop at the next section at the same/higher level.
        if lines[idx].startswith("#") and lines[idx].lstrip().startswith("## "):
            end = idx
            break

    section = lines[start:end]

    ext_for_lang = {
        "python": "py",
        "py": "py",
        "bash": "sh",
        "sh": "sh",
        "zsh": "sh",
        "shell": "sh",
        "ini": "ini",
        "toml": "toml",
        "yaml": "yml",
        "yml": "yml",
        "json": "json",
    }

    examples: dict[str, str] = {}
    i = 0
    example_idx = 0
    while i < len(section):
        fence = _FENCE_START_RE.match(section[i])
        if not fence:
            i += 1
            continue

        lang = (fence.group("lang") or "").lower()
        i += 1
        body: list[str] = []
        while i < len(section) and not section[i].strip().startswith("```"):
            body.append(section[i])
            i += 1

        if i < len(section) and section[i].strip().startswith("```"):
            example_idx += 1
            ext = ext_for_lang.get(lang, "txt")
            filename = f"example_{example_idx}.{ext}"
            examples[filename] = "\n".join(body).rstrip() + "\n"
            i += 1
            continue

        i += 1

    return examples


def _ensure_draft_root(drafts_root: Path, job_id: str) -> Path:
    """Ensure the per-job draft root exists (with its own taxonomy_meta.json).

    Args:
        drafts_root: Base directory for drafts
        job_id: Unique job identifier

    Returns:
        Path to the job-specific draft root
    """
    job_root = drafts_root / job_id
    job_root.mkdir(parents=True, exist_ok=True)
    meta_path = job_root / "taxonomy_meta.json"
    if not meta_path.exists():
        meta_path.write_text(
            json.dumps(
                {
                    "total_skills": 0,
                    "generation_count": 0,
                    "statistics": {"by_type": {}, "by_weight": {}, "by_priority": {}},
                    "last_updated": "",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return job_root


def _save_skill_to_draft(
    *, drafts_root: Path, job_id: str, result: SkillCreationResult
) -> str | None:
    """Save a completed skill to the draft area.

    Args:
        drafts_root: Base directory for drafts
        job_id: Unique job identifier
        result: SkillCreationResult from the workflow

    Returns:
        Path where the draft skill was saved, or None if save failed
    """
    if not result.skill_content or not result.metadata:
        logger.warning("Cannot save skill: missing content or metadata")
        return None

    try:
        draft_root = _ensure_draft_root(drafts_root, job_id)
        manager = TaxonomyManager(draft_root)

        # Extract metadata for registration
        metadata = result.metadata
        taxonomy_path = (
            metadata.taxonomy_path if hasattr(metadata, "taxonomy_path") else metadata.skill_id
        )

        # Use centralized path sanitization to prevent traversal attacks
        safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
        if not safe_taxonomy_path:
            logger.error("Unsafe taxonomy path provided by workflow: %s", taxonomy_path)
            return None

        # Build metadata dict for register_skill.
        #
        # Important: preserve workflow-produced metadata (capabilities, load_priority, etc.)
        # so deterministic validators and downstream tooling see the same intent the DSPy
        # planner produced.
        meta_dict = {
            "skill_id": metadata.skill_id,
            "name": metadata.name,
            "description": metadata.description,
            "version": metadata.version,
            "type": metadata.type,
            "weight": getattr(metadata, "weight", "medium"),
            "load_priority": getattr(metadata, "load_priority", "on_demand"),
            "dependencies": getattr(metadata, "dependencies", []) or [],
            "capabilities": getattr(metadata, "capabilities", []) or [],
            "category": getattr(metadata, "category", ""),
            "keywords": getattr(metadata, "keywords", []) or [],
            "scope": getattr(metadata, "scope", ""),
            "see_also": getattr(metadata, "see_also", []) or [],
            "tags": getattr(metadata, "tags", []) or [],
        }

        # Evolution tracking
        evolution = {
            "created_by": "skill-fleet-api",
            "workflow": "SkillCreationProgram",
            "validation_score": result.validation_report.score
            if result.validation_report
            else None,
        }

        # Register the skill (writes SKILL.md + metadata.json + standard subdirs)
        success = manager.register_skill(
            path=safe_taxonomy_path,
            metadata=meta_dict,
            content=result.skill_content,
            evolution=evolution,
            extra_files=result.extra_files,
            overwrite=True,
        )

        if success:
            full_path = draft_root / safe_taxonomy_path
            try:
                skill_md_path = full_path / "SKILL.md"
                if skill_md_path.exists():
                    skill_md = skill_md_path.read_text(encoding="utf-8")
                    assets = _extract_named_file_code_blocks(skill_md)
                    examples = _extract_usage_example_code_blocks(skill_md)

                    if assets:
                        assets_dir = full_path / "assets"
                        assets_dir.mkdir(parents=True, exist_ok=True)
                        for filename, content in assets.items():
                            (assets_dir / filename).write_text(content, encoding="utf-8")

                    if examples:
                        examples_dir = full_path / "examples"
                        examples_dir.mkdir(parents=True, exist_ok=True)
                        for filename, content in examples.items():
                            (examples_dir / filename).write_text(content, encoding="utf-8")
            except Exception:
                logger.warning(
                    "Failed to extract skill artifacts (assets/examples) for %s", full_path
                )

            logger.info("Draft saved successfully to: %s", full_path)
            return str(full_path)
        else:
            logger.error("Failed to register draft skill at path: %s", taxonomy_path)
            return None

    except Exception as e:
        logger.error(f"Error saving skill to draft: {e}", exc_info=True)
        return None


async def run_skill_creation(
    job_id: str,
    task_description: str,
    user_id: str,
    skills_root: Path,
    drafts_root: Path,
):
    """Execute the end-to-end skill creation workflow as a background job.

    This coroutine is intended to be scheduled via FastAPI's ``BackgroundTasks``
    mechanism (see the ``/create`` route in this module). When invoked, it
    retrieves the corresponding job record from the global ``JOBS`` registry
    using ``job_id`` and drives the full lifecycle of a single skill creation
    request.

    Args:
        job_id: Unique identifier for this job
        task_description: User's description of the skill to create
        user_id: User identifier for context
        skills_root: Root directory for skills taxonomy
        drafts_root: Root directory for draft skills
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

        # Persist state so we don't lose the HITL request on restart
        save_job_session(job_id)

        # Wait for response via /hitl/{job_id}/response
        try:
            response = await wait_for_hitl_response(job_id)
            job.status = "running"
            return response
        except TimeoutError:
            job.status = "failed"
            job.error = "HITL interaction timed out (user took too long to respond)"
            raise

    def progress_callback(phase: str, message: str) -> None:
        """Update job state with progress information for CLI display."""
        job.current_phase = phase
        job.progress_message = message
        # Persist progress updates periodically (optional, but good for long jobs)
        # We don't save on every detailed message to avoid I/O thrashing,
        # but saving on phase change is a good balance.
        save_job_session(job_id)

    try:
        # Provide real taxonomy context to Phase 1 (better path selection + overlap analysis).
        # The DSPy program contract expects JSON strings for these fields.
        taxonomy_manager = TaxonomyManager(skills_root)
        taxonomy_structure = taxonomy_manager.get_relevant_branches(task_description)
        mounted_skills = taxonomy_manager.get_mounted_skills(user_id)

        program = SkillCreationProgram()
        result = await program.aforward(
            task_description=task_description,
            user_context={"user_id": user_id},
            taxonomy_structure=json.dumps(taxonomy_structure),
            existing_skills=json.dumps(mounted_skills),
            hitl_callback=hitl_callback,
            progress_callback=progress_callback,
        )

        if result.status == "failed":
            job.status = "failed"
            job.error = result.error
        else:
            job.status = result.status
            job.result = result
            if result.metadata is not None:
                job.intended_taxonomy_path = (
                    result.metadata.taxonomy_path or result.metadata.skill_id
                )
            if result.validation_report is not None:
                job.validation_passed = bool(result.validation_report.passed)
                job.validation_status = str(result.validation_report.status)
                job.validation_score = float(result.validation_report.score)

            # Draft-first: save to skills/_drafts/<job_id>/... and require explicit promotion.
            if result.status == "completed" and result.skill_content:
                draft_path = _save_skill_to_draft(
                    drafts_root=drafts_root, job_id=job_id, result=result
                )
                if draft_path:
                    job.draft_path = draft_path
                    logger.info("Job %s completed; draft saved to: %s", job_id, draft_path)
                else:
                    logger.warning("Job %s completed but draft could not be saved", job_id)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job.status = "failed"
        job.error = str(e)
    finally:
        save_job_session(job_id)


@router.post("/create", response_model=CreateSkillResponse)
async def create(
    request: CreateSkillRequest,
    background_tasks: BackgroundTasks,
) -> CreateSkillResponse:
    """Initiate a new skill creation job.

    Creates a background job that executes the 3-phase skill creation workflow:
    1. Understanding & Planning (with HITL clarification)
    2. Content Generation (with HITL preview)
    3. Validation & Refinement (with HITL review)

    The job runs asynchronously. Use the returned job_id to poll for status
    via GET /api/v2/hitl/{job_id}/prompt.
    """
    if not request.task_description:
        raise HTTPException(status_code=400, detail="task_description is required")

    # Get paths from dependencies (called directly since we're in a background task context)
    skills_root = get_skills_root()
    drafts_root = get_drafts_root(skills_root)

    job_id = create_job()
    background_tasks.add_task(
        run_skill_creation,
        job_id,
        request.task_description,
        request.user_id,
        skills_root,
        drafts_root,
    )

    return CreateSkillResponse(job_id=job_id, status="accepted")
