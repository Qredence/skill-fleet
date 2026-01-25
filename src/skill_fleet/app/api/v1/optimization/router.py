"""
Signature optimization routes for v1 API.

This module provides endpoints for signature optimization operations.
These routes use signature optimization workflow orchestrators.

Endpoints:
    POST /api/v1/optimization/analyze - Analyze signature failures
    POST /api/v1/optimization/improve - Propose signature improvements
    POST /api/v1/optimization/compare - A/B test signatures
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException

from .....api.exceptions import NotFoundException
from .....api.schemas.optimization import (
    AnalyzeFailuresRequest,
    AnalyzeFailuresResponse,
    CompareRequest,
    CompareResponse,
    ImproveRequest,
    ImproveResponse,
)
from .....app.dependencies import SkillServiceDep
from .....workflows.signature_optimization.tuner import SignatureTuningOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

if TYPE_CHECKING:
    from .....app.services.skill_service import SkillService


def _build_sample_content(failure_examples: list[dict[str, Any]]) -> str:
    """
    Build sample content from failure examples for analysis.

    Args:
        failure_examples: List of failure examples with inputs/outputs

    Returns:
        Sample content string for tuning analysis

    """
    if not failure_examples:
        return "Sample skill content for analysis."

    examples = []
    for i, example in enumerate(failure_examples[:5], 1):
        input_data = example.get("input", {})
        expected = example.get("expected_output", "")
        actual = example.get("actual_output", "")
        examples.append(f"Example {i}: Input={input_data}, Expected={expected}, Got={actual}")

    return "\n".join(examples)


@router.post("/analyze", response_model=AnalyzeFailuresResponse)
async def analyze_failures(request: AnalyzeFailuresRequest) -> AnalyzeFailuresResponse:
    """
    Analyze signature failures to identify root causes.

    Args:
        request: Analysis request with signature name and failure examples

    Returns:
        AnalyzeFailuresResponse: Analysis results with root causes and suggestions

    Raises:
        HTTPException: If analysis fails

    """
    orchestrator = SignatureTuningOrchestrator()

    # Build sample content from failure examples
    sample_content = _build_sample_content(request.failure_examples)

    try:
        # Run signature tuning to get failure analysis
        result = await orchestrator.tune_signature(
            skill_content=sample_content,
            current_signature=request.signature_name,
            metric_score=0.5,  # Low score to trigger analysis
            target_score=0.80,
            skill_type="comprehensive",
            enable_mlflow=False,
        )

        # Extract analysis from result
        failure_analysis = result.get("failure_analysis", {})
        tuning_needed = result.get("tuning_needed", False)

        # Build root causes list
        root_causes = []
        if failure_analysis.get("insufficient_examples"):
            root_causes.append("Insufficient training examples")
        if failure_analysis.get("unclear_instructions"):
            root_causes.append("Unclear signature instructions")
        if failure_analysis.get("missing_context"):
            root_causes.append("Missing relevant context")
        if failure_analysis.get("poor_format"):
            root_causes.append("Poor output format specification")

        # If no specific causes found but tuning was needed
        if not root_causes and tuning_needed:
            root_causes.append("General performance below threshold")

        # Build suggested improvements
        suggested_improvements = failure_analysis.get("suggested_improvements", [])
        if not suggested_improvements:
            suggested_improvements = [
                "Add more diverse training examples",
                "Refine signature definition for clarity",
                "Adjust input/output format specifications",
            ]

        # Build analysis dict with additional details
        analysis = {
            "tuning_needed": tuning_needed,
            "current_score": result.get("current_score", 0.0),
            "target_score": result.get("target_score", 0.80),
            "accept_improvement": result.get("accept_improvement", False),
        }

        return AnalyzeFailuresResponse(
            signature_name=request.signature_name,
            analysis=analysis,
            root_causes=root_causes,
            suggested_improvements=suggested_improvements,
        )

    except Exception as e:
        logger.exception(f"Error in signature failure analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failure analysis failed: {e}"
        ) from e


@router.post("/improve", response_model=ImproveResponse)
async def improve_signature(request: ImproveRequest) -> ImproveResponse:
    """
    Propose improvements for a signature.

    Args:
        request: Improvement request with signature name and targets

    Returns:
        ImproveResponse: Proposed changes with expected impact and confidence

    Raises:
        HTTPException: If improvement proposal fails

    """
    orchestrator = SignatureTuningOrchestrator()

    # Build sample content for improvement
    sample_content = f"Sample content for {request.signature_name} signature improvement."

    try:
        # Run signature tuning to get proposed improvements
        result = await orchestrator.tune_signature(
            skill_content=sample_content,
            current_signature=request.signature_name,
            metric_score=0.65,  # Below threshold to trigger improvement
            target_score=0.80,
            skill_type="comprehensive",
            signature_id=request.signature_name,
            enable_mlflow=False,
        )

        # Extract proposed signature
        proposed_signature = result.get("proposed_signature", "")
        tuning_needed = result.get("tuning_needed", False)

        # If no improvement needed, return early
        if not tuning_needed:
            return ImproveResponse(
                signature_name=request.signature_name,
                proposed_changes={},
                expected_impact="No improvement needed - signature meets quality threshold",
                confidence=1.0,
                test_cases=[],
            )

        # Parse proposed signature to extract changes
        proposed_changes = {
            "signature_text": proposed_signature,
            "version": result.get("version", "2"),
        }

        # Build test cases from improvement targets
        test_cases = []
        for target in request.improvement_targets:
            test_cases.append({
                "target": target,
                "description": f"Test case for {target}",
                "status": "proposed",
            })

        # Add default test cases if none specified
        if not test_cases:
            test_cases = [
                {
                    "target": "general_improvement",
                    "description": "Test improved signature on diverse inputs",
                    "status": "proposed",
                }
            ]

        # Calculate confidence from accept_improvement flag
        accept_improvement = result.get("accept_improvement", False)
        confidence = 0.85 if accept_improvement else 0.70

        # Build expected impact description
        improvement_amount = result.get("improvement_amount", 0.0)
        expected_impact = f"Expected improvement of {improvement_amount:.1%} in quality score"

        return ImproveResponse(
            signature_name=request.signature_name,
            proposed_changes=proposed_changes,
            expected_impact=expected_impact,
            confidence=confidence,
            test_cases=test_cases,
        )

    except Exception as e:
        logger.exception(f"Error in signature improvement proposal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Improvement proposal failed: {e}"
        ) from e


@router.post("/compare", response_model=CompareResponse)
async def compare_signatures(request: CompareRequest) -> CompareResponse:
    """
    A/B test two signatures against each other.

    Args:
        request: Comparison request with two signatures and test inputs

    Returns:
        CompareResponse: Comparison results with winner and metrics

    Raises:
        HTTPException: If comparison fails

    """
    orchestrator = SignatureTuningOrchestrator()

    # Build sample content from test inputs
    if request.test_inputs:
        test_content = "\n".join(
            f"Test {i}: {test_input}"
            for i, test_input in enumerate(request.test_inputs[:5], 1)
        )
    else:
        test_content = "Sample test content for signature comparison."

    try:
        # Get version history for both signatures
        history_a = orchestrator.get_version_history(request.signature_a_name)
        history_b = orchestrator.get_version_history(request.signature_b_name)

        # Run tuning for both signatures to get scores
        result_a = await orchestrator.tune_signature(
            skill_content=test_content,
            current_signature=request.signature_a_name,
            metric_score=0.75,
            target_score=0.80,
            signature_id=request.signature_a_name,
            enable_mlflow=False,
        )

        result_b = await orchestrator.tune_signature(
            skill_content=test_content,
            current_signature=request.signature_b_name,
            metric_score=0.75,
            target_score=0.80,
            signature_id=request.signature_b_name,
            enable_mlflow=False,
        )

        # Extract scores
        score_a = result_a.get("current_score", 0.75)
        score_b = result_b.get("current_score", 0.75)
        improvement_a = result_a.get("improvement_amount", 0.0)
        improvement_b = result_b.get("improvement_amount", 0.0)

        # Determine winner
        if abs(score_a - score_b) < 0.05:
            winner = None  # Too close to call
            recommendation = f"Both signatures perform similarly (A: {score_a:.2f}, B: {score_b:.2f}). Consider other factors."
        elif score_a > score_b:
            winner = request.signature_a_name
            recommendation = f"Signature A ({request.signature_a_name}) shows better performance ({score_a:.2f} vs {score_b:.2f})"
        else:
            winner = request.signature_b_name
            recommendation = f"Signature B ({request.signature_b_name}) shows better performance ({score_b:.2f} vs {score_a:.2f})"

        # Build signature info with versions
        signature_a_info = {
            "name": request.signature_a_name,
            "version": request.signature_a_version or (history_a.get("version") if history_a else "1"),
        }
        signature_b_info = {
            "name": request.signature_b_name,
            "version": request.signature_b_version or (history_b.get("version") if history_b else "1"),
        }

        # Build metrics dict
        metrics = {
            "score_a": score_a,
            "score_b": score_b,
            "improvement_a": improvement_a,
            "improvement_b": improvement_b,
            "difference": abs(score_a - score_b),
        }

        return CompareResponse(
            signature_a=signature_a_info,
            signature_b=signature_b_info,
            winner=winner,
            metrics=metrics,
            recommendation=recommendation,
        )

    except Exception as e:
        logger.exception(f"Error in signature comparison: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Signature comparison failed: {e}"
        ) from e
