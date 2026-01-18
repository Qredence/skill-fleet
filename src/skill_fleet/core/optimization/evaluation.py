"""Evaluation metrics and data loading for DSPy optimization.

This module provides:
- Metrics for evaluating skill creation quality
- Functions to load training/validation datasets
- Utilities for running evaluations

Metrics are compatible with DSPy optimizers (MIPROv2, GEPA, etc.)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


# =============================================================================
# Data Loading
# =============================================================================


def load_trainset(
    path: str | Path = "config/training/trainset.json",
) -> list[dspy.Example]:
    """Load training examples from JSON file.

    Args:
        path: Path to the trainset JSON file

    Returns:
        List of dspy.Example objects with inputs marked
    """
    import dspy

    from ...common.paths import resolve_repo_relative_path

    path = resolve_repo_relative_path(path)
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Training set not found at {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    examples = []
    for item in data:
        example = dspy.Example(**item).with_inputs("task_description")
        examples.append(example)

    logger.info(f"Loaded {len(examples)} training examples from {path}")
    return examples


def split_dataset(
    examples: list[dspy.Example],
    train_ratio: float = 0.8,
) -> tuple[list[dspy.Example], list[dspy.Example]]:
    """Split examples into train and validation sets.

    Args:
        examples: List of examples to split
        train_ratio: Fraction for training (default 0.8)

    Returns:
        Tuple of (train_set, val_set)
    """
    split_idx = int(len(examples) * train_ratio)
    return examples[:split_idx], examples[split_idx:]


# =============================================================================
# Evaluation Metrics
# =============================================================================


def taxonomy_path_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Any = None,
) -> float:
    """Evaluate taxonomy path accuracy.

    Scoring:
    - Exact match: 1.0
    - Same root category: 0.5
    - Same first two levels: 0.7
    - No match: 0.0

    Args:
        gold: Example with expected_taxonomy_path
        pred: Prediction with understanding.taxonomy_path
        trace: Optional trace information

    Returns:
        Score between 0.0 and 1.0
    """
    expected_path = getattr(gold, "expected_taxonomy_path", "")

    # Extract predicted path
    if isinstance(pred, dict):
        understanding = pred.get("understanding")
    else:
        understanding = getattr(pred, "understanding", None)

    if understanding is None:
        return 0.0

    if isinstance(understanding, dict):
        pred_path = understanding.get("taxonomy_path", "")
    else:
        pred_path = getattr(understanding, "taxonomy_path", "")

    if not expected_path or not pred_path:
        return 0.0

    # Normalize paths
    expected_path = expected_path.strip().lower()
    pred_path = pred_path.strip().lower()

    # Exact match
    if pred_path == expected_path:
        return 1.0

    # Split into parts
    expected_parts = expected_path.split("/")
    pred_parts = pred_path.split("/")

    # Same root category
    if expected_parts[0] == pred_parts[0]:
        # Check depth of match
        matching_parts = 0
        for e, p in zip(expected_parts, pred_parts, strict=False):
            if e == p:
                matching_parts += 1
            else:
                break

        # Score based on matching depth
        if matching_parts >= 3:
            return 0.8
        elif matching_parts >= 2:
            return 0.6
        else:
            return 0.4

    return 0.0


def metadata_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Any = None,
) -> float:
    """Evaluate metadata completeness and accuracy.

    Scoring:
    - Name matches: 0.3
    - Type matches: 0.2
    - Weight matches: 0.1
    - Capabilities overlap: 0.4

    Args:
        gold: Example with expected metadata fields
        pred: Prediction with plan.skill_metadata
        trace: Optional trace information

    Returns:
        Score between 0.0 and 1.0
    """
    if isinstance(pred, dict):
        plan = pred.get("plan")
    else:
        plan = getattr(pred, "plan", None)

    if plan is None:
        return 0.0

    if isinstance(plan, dict):
        metadata = plan.get("skill_metadata", {})
    else:
        metadata = getattr(plan, "skill_metadata", {})

    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            return 0.0

    if not metadata:
        return 0.0

    score = 0.0

    # Helper to get field from metadata (dict or object)
    def get_meta_field(field: str) -> Any:
        """Extract a field value from metadata that may be either a dict or object.

        Args:
            field: The field name to extract

        Returns:
            The field value if found, None otherwise
        """
        if isinstance(metadata, dict):
            return metadata.get(field)
        return getattr(metadata, field, None)

    # Name match
    expected_name = getattr(gold, "expected_name", "")
    pred_name = get_meta_field("name") or ""
    if pred_name.lower() == expected_name.lower():
        score += 0.3
    elif expected_name.lower() in pred_name.lower() or pred_name.lower() in expected_name.lower():
        score += 0.15

    # Type match
    expected_type = getattr(gold, "expected_type", "")
    pred_type = get_meta_field("type") or ""
    if pred_type.lower() == expected_type.lower():
        score += 0.2

    # Weight match
    expected_weight = getattr(gold, "expected_weight", "")
    pred_weight = get_meta_field("weight") or ""
    if pred_weight.lower() == expected_weight.lower():
        score += 0.1

    # Capabilities overlap
    expected_caps = set(getattr(gold, "expected_capabilities", []))
    pred_caps_raw = get_meta_field("capabilities") or []

    # Handle capabilities that might be list of objects or strings
    pred_caps = set()
    for cap in pred_caps_raw:
        if isinstance(cap, str):
            pred_caps.add(cap.lower())
        elif isinstance(cap, dict):
            pred_caps.add(cap.get("name", "").lower())
        elif hasattr(cap, "name"):
            pred_caps.add(cap.name.lower())

    expected_caps_lower = {c.lower() for c in expected_caps}

    if expected_caps_lower and pred_caps:
        overlap = len(expected_caps_lower & pred_caps)
        union = len(expected_caps_lower | pred_caps)
        jaccard = overlap / union if union > 0 else 0
        score += jaccard * 0.4

    return min(score, 1.0)


def content_quality_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Any = None,
) -> float:
    """Evaluate content generation quality.

    Scoring:
    - Has Overview section: 0.2
    - Has Capabilities section: 0.2
    - Has code examples: 0.3
    - Reasonable length: 0.3

    Args:
        gold: Example (not used for content, just structure)
        pred: Prediction with content.skill_content
        trace: Optional trace information

    Returns:
        Score between 0.0 and 1.0
    """
    if isinstance(pred, dict):
        content_data = pred.get("content")
    else:
        content_data = getattr(pred, "content", None)

    if content_data is None:
        return 0.0

    if isinstance(content_data, dict):
        content = content_data.get("skill_content", "")
    else:
        content = getattr(content_data, "skill_content", "")

    if not content:
        return 0.0

    score = 0.0

    # Has Overview section
    if "## Overview" in content or "## overview" in content.lower():
        score += 0.2

    # Has Capabilities section
    if "## Capabilities" in content or "## capabilities" in content.lower():
        score += 0.2

    # Has code examples
    code_blocks = content.count("```")
    if code_blocks >= 4:  # At least 2 complete blocks
        score += 0.3
    elif code_blocks >= 2:
        score += 0.2
    elif code_blocks >= 1:
        score += 0.1

    # Reasonable length (500-3000 words is ideal)
    word_count = len(content.split())
    if 500 <= word_count <= 3000:
        score += 0.3
    elif 300 <= word_count <= 5000:
        score += 0.2
    elif word_count >= 200:
        score += 0.1

    return min(score, 1.0)


def skill_creation_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: Any = None,
) -> float:
    """Composite metric for full skill creation workflow.

    Combines:
    - Taxonomy path accuracy: 30%
    - Metadata quality: 35%
    - Content quality: 35%

    Args:
        gold: Example with expected values
        pred: Prediction with workflow outputs
        trace: Optional trace information

    Returns:
        Score between 0.0 and 1.0
    """
    path_score = taxonomy_path_metric(gold, pred, trace)
    metadata_score = metadata_metric(gold, pred, trace)
    content_score = content_quality_metric(gold, pred, trace)

    # Weighted combination
    total = (path_score * 0.30) + (metadata_score * 0.35) + (content_score * 0.35)

    logger.debug(
        f"Skill creation metric: path={path_score:.2f}, "
        f"metadata={metadata_score:.2f}, content={content_score:.2f}, "
        f"total={total:.2f}"
    )

    return total


# =============================================================================
# Evaluation Utilities
# =============================================================================


def evaluate_program(
    program: dspy.Module,
    examples: list[dspy.Example],
    metric: callable = skill_creation_metric,
    **program_kwargs: Any,
) -> dict[str, Any]:
    """Run evaluation on a set of examples.

    Args:
        program: DSPy program to evaluate
        examples: List of examples to evaluate on
        metric: Metric function to use
        **program_kwargs: Additional kwargs for program execution

    Returns:
        Dict with scores, mean, std, and individual results
    """
    import numpy as np

    scores = []
    results = []

    for example in examples:
        try:
            pred = program(
                task_description=example.task_description,
                **program_kwargs,
            )
            score = metric(example, pred)
            scores.append(score)
            results.append(
                {
                    "example": example.task_description[:50],
                    "score": score,
                    "success": True,
                }
            )
        except Exception as e:
            logger.warning(f"Evaluation error: {e}")
            scores.append(0.0)
            results.append(
                {
                    "example": example.task_description[:50],
                    "score": 0.0,
                    "success": False,
                    "error": str(e),
                }
            )

    return {
        "scores": scores,
        "mean": float(np.mean(scores)),
        "std": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
        "n_examples": len(examples),
        "results": results,
    }


def print_evaluation_report(eval_results: dict[str, Any]) -> None:
    """Print a formatted evaluation report.

    Args:
        eval_results: Results from evaluate_program
    """
    print("\n" + "=" * 60)
    print("EVALUATION REPORT")
    print("=" * 60)
    print(f"Examples evaluated: {eval_results['n_examples']}")
    print(f"Mean score: {eval_results['mean']:.3f}")
    print(f"Std deviation: {eval_results['std']:.3f}")
    print(f"Min score: {eval_results['min']:.3f}")
    print(f"Max score: {eval_results['max']:.3f}")
    print("-" * 60)
    print("\nIndividual Results:")
    for i, result in enumerate(eval_results["results"], 1):
        status = "OK" if result["success"] else "FAIL"
        print(f"  {i}. [{status}] {result['example']}... -> {result['score']:.2f}")
        if not result["success"]:
            print(f"      Error: {result.get('error', 'Unknown')}")
    print("=" * 60 + "\n")
