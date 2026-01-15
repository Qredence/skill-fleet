"""Evaluation routes for skill quality assessment.

API-first approach for skill evaluation using DSPy metrics calibrated
against golden skills from https://github.com/obra/superpowers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...common.security import sanitize_taxonomy_path
from ...core.dspy.metrics import SkillQualityScores, assess_skill_quality
from ..dependencies import SkillsRoot

router = APIRouter()


class EvaluateSkillRequest(BaseModel):
    """Request body for evaluating a skill."""

    path: str = Field(..., description="Taxonomy-relative path to the skill")
    weights: dict[str, float] | None = Field(
        default=None,
        description="Optional custom metric weights for scoring",
    )


class EvaluateContentRequest(BaseModel):
    """Request body for evaluating raw skill content."""

    content: str = Field(..., description="Raw SKILL.md content to evaluate")
    weights: dict[str, float] | None = Field(
        default=None,
        description="Optional custom metric weights for scoring",
    )


class QualityIndicators(BaseModel):
    """Obra/superpowers quality indicators."""

    has_core_principle: bool = Field(description="Has 'Core principle:' statement")
    has_strong_guidance: bool = Field(description="Has Iron Law / imperative rules")
    has_good_bad_contrast: bool = Field(description="Has paired Good/Bad examples")
    description_quality: float = Field(description="Quality score for description (0-1)")


class EvaluationResponse(BaseModel):
    """Response model for skill evaluation."""

    overall_score: float = Field(description="Overall quality score (0-1)")

    # Structure scores
    frontmatter_completeness: float
    has_overview: bool
    has_when_to_use: bool
    has_quick_reference: bool

    # Pattern scores
    pattern_count: int
    has_anti_patterns: bool
    has_production_patterns: bool
    has_key_insights: bool

    # Practical value scores
    has_common_mistakes: bool
    has_red_flags: bool
    has_real_world_impact: bool

    # Code quality scores
    code_examples_count: int
    code_examples_quality: float

    # Obra/superpowers quality indicators
    quality_indicators: QualityIndicators

    # Feedback
    issues: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)


class BatchEvaluateRequest(BaseModel):
    """Request body for batch evaluation."""

    paths: list[str] = Field(..., description="List of taxonomy-relative paths to evaluate")
    weights: dict[str, float] | None = Field(default=None)


class BatchEvaluationResult(BaseModel):
    """Result for a single skill in batch evaluation."""

    path: str
    overall_score: float
    issues_count: int
    strengths_count: int
    error: str | None = None


class BatchEvaluateResponse(BaseModel):
    """Response model for batch evaluation."""

    results: list[BatchEvaluationResult]
    average_score: float
    total_evaluated: int
    total_errors: int


def _scores_to_response(scores: SkillQualityScores) -> EvaluationResponse:
    """Convert SkillQualityScores to API response model."""
    return EvaluationResponse(
        overall_score=scores.overall_score,
        frontmatter_completeness=scores.frontmatter_completeness,
        has_overview=scores.has_overview,
        has_when_to_use=scores.has_when_to_use,
        has_quick_reference=scores.has_quick_reference,
        pattern_count=scores.pattern_count,
        has_anti_patterns=scores.has_anti_patterns,
        has_production_patterns=scores.has_production_patterns,
        has_key_insights=scores.has_key_insights,
        has_common_mistakes=scores.has_common_mistakes,
        has_red_flags=scores.has_red_flags,
        has_real_world_impact=scores.has_real_world_impact,
        code_examples_count=scores.code_examples_count,
        code_examples_quality=scores.code_examples_quality,
        quality_indicators=QualityIndicators(
            has_core_principle=scores.has_core_principle,
            has_strong_guidance=scores.has_strong_guidance,
            has_good_bad_contrast=scores.has_good_bad_contrast,
            description_quality=scores.description_quality,
        ),
        issues=scores.issues,
        strengths=scores.strengths,
    )


def _resolve_skill_md_path(*, skills_root: Path, taxonomy_path: str) -> Path:
    """Resolve an untrusted taxonomy-relative path to a SKILL.md path safely.

    Raises:
        ValueError: If the taxonomy path is invalid or escapes skills_root.
        FileNotFoundError: If the SKILL.md file does not exist.
    """
    safe_taxonomy_path = sanitize_taxonomy_path(taxonomy_path)
    if safe_taxonomy_path is None:
        raise ValueError("Invalid path")

    skills_root_resolved = skills_root.resolve()

    # Disallow symlinks for the skill directory itself (defense-in-depth).
    skill_dir = skills_root_resolved / safe_taxonomy_path
    if skill_dir.exists() and skill_dir.is_symlink():
        raise ValueError("Invalid path")

    candidate_md = skill_dir / "SKILL.md"
    if not candidate_md.exists():
        raise FileNotFoundError(candidate_md.as_posix())

    # Disallow symlink SKILL.md files to prevent escaping via filesystem links.
    if candidate_md.is_symlink():
        raise ValueError("Invalid path")

    resolved_md = candidate_md.resolve(strict=True)
    try:
        resolved_md.relative_to(skills_root_resolved)
    except ValueError as e:
        raise ValueError("Invalid path") from e

    return resolved_md


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_skill(
    request: EvaluateSkillRequest,
    skills_root: SkillsRoot,
) -> EvaluationResponse:
    """Evaluate a skill's quality at the specified path.

    Uses DSPy metrics calibrated against golden skills from Obra/superpowers.
    Applies stricter criteria including:
    - Core principle statement check
    - Strong guidance / Iron Law check
    - Good/Bad contrast pattern check
    - Description quality assessment

    Penalty multiplier applied for missing critical elements.
    """
    path = request.path
    if not path:
        raise HTTPException(status_code=400, detail="path is required")

    try:
        skill_md = _resolve_skill_md_path(skills_root=skills_root, taxonomy_path=path)
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid path") from err
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail=f"SKILL.md not found at {sanitize_taxonomy_path(path) or path}",
        ) from err

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read SKILL.md: {e}",
        ) from e

    scores = assess_skill_quality(content, weights=request.weights)
    return _scores_to_response(scores)


@router.post("/evaluate-content", response_model=EvaluationResponse)
async def evaluate_content(
    request: EvaluateContentRequest,
) -> EvaluationResponse:
    """Evaluate raw SKILL.md content directly.

    Useful for evaluating content before saving to disk or for
    testing generated content quality.
    """
    if not request.content:
        raise HTTPException(status_code=400, detail="content is required")

    scores = assess_skill_quality(request.content, weights=request.weights)
    return _scores_to_response(scores)


@router.post("/evaluate-batch", response_model=BatchEvaluateResponse)
async def evaluate_batch(
    request: BatchEvaluateRequest,
    skills_root: SkillsRoot,
) -> BatchEvaluateResponse:
    """Evaluate multiple skills in batch.

    Returns individual scores and aggregate statistics.
    """
    if not request.paths:
        raise HTTPException(status_code=400, detail="paths list is required")

    results: list[BatchEvaluationResult] = []
    total_score = 0.0
    total_errors = 0

    for path in request.paths:
        try:
            skill_md = _resolve_skill_md_path(skills_root=skills_root, taxonomy_path=path)
        except ValueError:
            results.append(
                BatchEvaluationResult(
                    path=path,
                    overall_score=0.0,
                    issues_count=0,
                    strengths_count=0,
                    error="Invalid path",
                )
            )
            total_errors += 1
            continue
        except FileNotFoundError:
            results.append(
                BatchEvaluationResult(
                    path=path,
                    overall_score=0.0,
                    issues_count=0,
                    strengths_count=0,
                    error="SKILL.md not found",
                )
            )
            total_errors += 1
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
            scores = assess_skill_quality(content, weights=request.weights)
            results.append(
                BatchEvaluationResult(
                    path=path,
                    overall_score=scores.overall_score,
                    issues_count=len(scores.issues),
                    strengths_count=len(scores.strengths),
                )
            )
            total_score += scores.overall_score
        except Exception as e:
            results.append(
                BatchEvaluationResult(
                    path=path,
                    overall_score=0.0,
                    issues_count=0,
                    strengths_count=0,
                    error=str(e),
                )
            )
            total_errors += 1

    evaluated_count = len(results) - total_errors
    average_score = total_score / evaluated_count if evaluated_count > 0 else 0.0

    return BatchEvaluateResponse(
        results=results,
        average_score=average_score,
        total_evaluated=evaluated_count,
        total_errors=total_errors,
    )


@router.get("/metrics-info")
async def get_metrics_info() -> dict[str, Any]:
    """Get information about the evaluation metrics and weights.

    Returns the default weights and descriptions for each metric.
    """
    return {
        "description": "Skill quality metrics calibrated against Obra/superpowers golden skills",
        "reference": "https://github.com/obra/superpowers/tree/main/skills",
        "default_weights": {
            # Original metrics
            "pattern_count": {"weight": 0.10, "description": "Number of patterns (target: 5+)"},
            "has_anti_patterns": {"weight": 0.08, "description": "Has ❌ anti-pattern examples"},
            "has_key_insights": {"weight": 0.08, "description": "Has 'Key insight:' summaries"},
            "has_real_world_impact": {"weight": 0.08, "description": "Has quantified benefits"},
            "has_quick_reference": {"weight": 0.06, "description": "Has quick reference table"},
            "has_common_mistakes": {"weight": 0.06, "description": "Has common mistakes section"},
            "has_red_flags": {"weight": 0.04, "description": "Has red flags section"},
            "frontmatter_completeness": {"weight": 0.10, "description": "YAML frontmatter quality"},
            "code_examples_quality": {"weight": 0.10, "description": "Code example quality"},
            # Obra/superpowers quality indicators
            "has_core_principle": {
                "weight": 0.10,
                "description": "Has 'Core principle:' statement",
            },
            "has_strong_guidance": {
                "weight": 0.08,
                "description": "Has Iron Law / imperative rules",
            },
            "has_good_bad_contrast": {
                "weight": 0.07,
                "description": "Has paired Good/Bad examples",
            },
            "description_quality": {
                "weight": 0.05,
                "description": "Description follows 'Use when...' pattern",
            },
        },
        "penalty_multipliers": {
            "description": "Penalty applied based on missing critical elements",
            "0_critical": 0.70,
            "1_critical": 0.85,
            "2_critical": 0.95,
            "3_critical": 1.00,
        },
        "critical_elements": [
            "has_core_principle",
            "has_strong_guidance",
            "has_good_bad_contrast",
        ],
    }
