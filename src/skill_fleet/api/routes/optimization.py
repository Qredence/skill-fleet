"""Optimization routes for DSPy program optimization.

API-first approach for optimizing skill creation programs using
MIPROv2 and BootstrapFewShot optimizers.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator

from ...common.paths import find_repo_root
from ...common.security import (
    resolve_path_within_root,
    sanitize_relative_file_path,
    sanitize_taxonomy_path,
)
from ...core.dspy.optimization import SkillOptimizer
from ..dependencies import SkillsRoot

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory storage for optimization jobs (in production, use Redis/DB)
_optimization_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = asyncio.Lock()


def _default_optimized_root() -> Path:
    repo_root = find_repo_root(Path.cwd()) or find_repo_root(Path(__file__).resolve())
    if repo_root:
        return repo_root / "config" / "optimized"

    logger.warning("Repo root not found; saving optimized programs relative to CWD")
    return Path.cwd() / "config" / "optimized"


class OptimizeRequest(BaseModel):
    """Request body for starting an optimization job."""

    optimizer: str = Field(
        default="miprov2",
        description="Optimizer to use: 'miprov2' or 'bootstrap_fewshot'",
    )
    training_paths: list[str] = Field(
        default_factory=list,
        description="Paths to gold-standard skills for training",
    )
    auto: str = Field(
        default="medium",
        description="MIPROv2 auto setting: 'light', 'medium', or 'heavy'",
    )
    max_bootstrapped_demos: int = Field(
        default=4,
        description="Maximum number of bootstrapped demonstrations",
    )
    max_labeled_demos: int = Field(
        default=4,
        description="Maximum number of labeled demonstrations",
    )
    save_path: str | None = Field(
        default=None,
        description="Path to save optimized program (relative to config/optimized)",
    )

    @field_validator("training_paths")
    @classmethod
    def _validate_training_paths(cls, value: list[str]) -> list[str]:
        sanitized_paths: list[str] = []
        for path in value:
            sanitized = sanitize_taxonomy_path(path)
            if not sanitized:
                raise ValueError(
                    "training_paths must contain taxonomy-relative skill paths and may only contain "
                    "alphanumeric characters, hyphens, underscores, and slashes"
                )
            sanitized_paths.append(sanitized)
        return sanitized_paths

    @field_validator("save_path")
    @classmethod
    def _validate_save_path(cls, value: str | None) -> str | None:
        if value is None:
            return None

        sanitized = sanitize_relative_file_path(value)
        if not sanitized:
            raise ValueError(
                "save_path must be a relative path under config/optimized and may only contain "
                "alphanumeric characters, dots, hyphens, underscores, and slashes"
            )
        return sanitized


class OptimizeResponse(BaseModel):
    """Response model for optimization job creation."""

    job_id: str
    status: str
    message: str


class OptimizationStatus(BaseModel):
    """Status of an optimization job."""

    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: float = 0.0  # 0.0 to 1.0
    message: str = ""
    result: dict[str, Any] | None = None
    error: str | None = None


class OptimizerInfo(BaseModel):
    """Information about an optimizer."""

    name: str
    description: str
    parameters: dict[str, Any]


@router.post("/start", response_model=OptimizeResponse)
async def start_optimization(
    request: OptimizeRequest,
    background_tasks: BackgroundTasks,
    skills_root: SkillsRoot,
) -> OptimizeResponse:
    """Start an optimization job.

    Optimization runs in the background. Use the returned job_id
    to check status via GET /optimization/status/{job_id}.
    """
    import uuid

    job_id = str(uuid.uuid4())

    # Validate optimizer
    if request.optimizer not in ["miprov2", "bootstrap_fewshot"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid optimizer: {request.optimizer}. Use 'miprov2' or 'bootstrap_fewshot'",
        )

    # Initialize job status
    async with _jobs_lock:
        _optimization_jobs[job_id] = {
            "status": "pending",
            "progress": 0.0,
            "message": "Job queued",
            "result": None,
            "error": None,
        }

    # Start background task
    background_tasks.add_task(
        _run_optimization,
        job_id=job_id,
        request=request,
        skills_root=skills_root,
    )

    return OptimizeResponse(
        job_id=job_id,
        status="pending",
        message="Optimization job started. Check status with GET /optimization/status/{job_id}",
    )


async def _run_optimization(
    job_id: str,
    request: OptimizeRequest,
    skills_root: Path,
) -> None:
    """Run optimization in background."""
    try:
        async with _jobs_lock:
            _optimization_jobs[job_id]["status"] = "running"
            _optimization_jobs[job_id]["message"] = "Loading training data..."
            _optimization_jobs[job_id]["progress"] = 0.1

        # Load training examples from paths
        training_examples = []
        for path in request.training_paths:
            try:
                skill_dir = resolve_path_within_root(skills_root, path)
            except ValueError:
                logger.warning("Rejected unsafe training path: %s", path)
                continue

            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                training_examples.append(
                    {
                        "path": path,
                        "content": content,
                    }
                )

        if not training_examples:
            async with _jobs_lock:
                _optimization_jobs[job_id]["status"] = "failed"
                _optimization_jobs[job_id]["error"] = "No valid training examples found"
            return

        async with _jobs_lock:
            _optimization_jobs[job_id]["message"] = (
                f"Loaded {len(training_examples)} training examples"
            )
            _optimization_jobs[job_id]["progress"] = 0.2

        # Initialize optimizer with configure_lm=False since the optimize_with_* methods
        # handle LM configuration internally using dspy.context() for async safety
        optimizer = SkillOptimizer(configure_lm=False)

        async with _jobs_lock:
            _optimization_jobs[job_id]["message"] = f"Running {request.optimizer} optimization..."
            _optimization_jobs[job_id]["progress"] = 0.3

        # Run optimization (this is CPU/GPU intensive)
        # Note: In production, this should be run in a separate process/worker
        if request.optimizer == "miprov2":
            result = await asyncio.to_thread(
                optimizer.optimize_with_miprov2,
                training_examples=training_examples,
                auto=request.auto,
                max_bootstrapped_demos=request.max_bootstrapped_demos,
                max_labeled_demos=request.max_labeled_demos,
            )
        else:
            result = await asyncio.to_thread(
                optimizer.optimize_with_bootstrap,
                training_examples=training_examples,
                max_bootstrapped_demos=request.max_bootstrapped_demos,
                max_labeled_demos=request.max_labeled_demos,
            )

        async with _jobs_lock:
            _optimization_jobs[job_id]["progress"] = 0.9

        # Save if requested
        if request.save_path:
            save_dir = _default_optimized_root()
            save_file = resolve_path_within_root(save_dir, request.save_path)
            save_file.parent.mkdir(parents=True, exist_ok=True)

            if hasattr(result, "save"):
                result.save(str(save_file))
                message = f"Optimization complete. Saved to {save_file}"
            else:
                message = "Optimization complete (save not supported)"

            async with _jobs_lock:
                _optimization_jobs[job_id]["message"] = message

        async with _jobs_lock:
            _optimization_jobs[job_id]["status"] = "completed"
            _optimization_jobs[job_id]["progress"] = 1.0
            _optimization_jobs[job_id]["result"] = {
                "optimizer": request.optimizer,
                "training_examples_count": len(training_examples),
                "save_path": request.save_path,
            }

    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {e}", exc_info=True)
        async with _jobs_lock:
            _optimization_jobs[job_id]["status"] = "failed"
            _optimization_jobs[job_id]["error"] = str(e)


@router.get("/status/{job_id}", response_model=OptimizationStatus)
async def get_optimization_status(job_id: str) -> OptimizationStatus:
    """Get the status of an optimization job."""
    async with _jobs_lock:
        if job_id not in _optimization_jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Optimization job {job_id} not found",
            )

        job = _optimization_jobs[job_id].copy()  # Copy to avoid holding lock during response

    return OptimizationStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        result=job["result"],
        error=job["error"],
    )


@router.get("/optimizers", response_model=list[OptimizerInfo])
async def list_optimizers() -> list[OptimizerInfo]:
    """List available optimizers and their configurations."""
    return [
        OptimizerInfo(
            name="miprov2",
            description="MIPROv2 optimizer - Multi-stage Instruction Proposal and Optimization",
            parameters={
                "auto": {
                    "type": "string",
                    "options": ["light", "medium", "heavy"],
                    "default": "medium",
                    "description": "Optimization depth vs cost tradeoff",
                },
                "max_bootstrapped_demos": {
                    "type": "integer",
                    "default": 4,
                    "description": "Maximum auto-generated demonstrations",
                },
                "max_labeled_demos": {
                    "type": "integer",
                    "default": 4,
                    "description": "Maximum human-curated demonstrations",
                },
            },
        ),
        OptimizerInfo(
            name="bootstrap_fewshot",
            description="BootstrapFewShot optimizer - Simple few-shot learning with bootstrapping",
            parameters={
                "max_bootstrapped_demos": {
                    "type": "integer",
                    "default": 4,
                    "description": "Maximum auto-generated demonstrations",
                },
                "max_labeled_demos": {
                    "type": "integer",
                    "default": 4,
                    "description": "Maximum human-curated demonstrations",
                },
                "max_rounds": {
                    "type": "integer",
                    "default": 1,
                    "description": "Number of bootstrapping rounds",
                },
            },
        ),
    ]


@router.delete("/jobs/{job_id}")
async def cancel_optimization(job_id: str) -> dict[str, str]:
    """Cancel or remove an optimization job.

    Note: Running jobs cannot be cancelled, only removed from tracking.
    """
    async with _jobs_lock:
        if job_id not in _optimization_jobs:
            raise HTTPException(
                status_code=404,
                detail=f"Optimization job {job_id} not found",
            )

        job = _optimization_jobs.pop(job_id)

    return {
        "job_id": job_id,
        "previous_status": job["status"],
        "message": "Job removed from tracking",
    }


@router.get("/config")
async def get_optimization_config() -> dict[str, Any]:
    """Get the current optimization configuration from config.yaml."""
    import yaml

    from ...common.paths import default_config_path

    config_path = default_config_path()
    if not config_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Configuration file not found",
        )

    try:
        with open(config_path) as f:
            config: object = yaml.safe_load(f)

        return {
            "optimization": config.get("optimization", {}),
            "evaluation": config.get("evaluation", {}),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load configuration: {e}",
        ) from e
