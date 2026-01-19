"""Enhanced evaluation metrics for DSPy optimization.

Additional metrics beyond basic skill_quality_metric for comprehensive evaluation.
"""

from __future__ import annotations

import re
from typing import Any, Callable

import dspy


def taxonomy_accuracy_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Evaluate taxonomy path accuracy.
    
    Checks if predicted taxonomy path matches expected path or category.
    
    Args:
        example: Example with expected_taxonomy_path
        prediction: Prediction with taxonomy_path or recommended_path
        trace: Optional trace (unused)
    
    Returns:
        Score 0.0-1.0
    """
    if not hasattr(example, "expected_taxonomy_path"):
        return 0.5  # Neutral if no expected path
    
    expected_path = example.expected_taxonomy_path
    
    # Try different prediction field names
    predicted_path = None
    for field in ["taxonomy_path", "recommended_path", "path"]:
        if hasattr(prediction, field):
            predicted_path = getattr(prediction, field)
            break
    
    if not predicted_path:
        return 0.0  # No path predicted
    
    # Exact match
    if predicted_path == expected_path:
        return 1.0
    
    # Category match (first segment)
    expected_category = expected_path.split("/")[0] if "/" in expected_path else expected_path
    predicted_category = predicted_path.split("/")[0] if "/" in predicted_path else predicted_path
    
    if expected_category.lower() == predicted_category.lower():
        return 0.7  # Partial credit for correct category
    
    return 0.0


def metadata_quality_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Evaluate metadata quality (name, description, tags).
    
    Checks:
    - Name is kebab-case
    - Description starts with "Use when..."
    - Tags are relevant and diverse
    - Version follows semver
    
    Args:
        example: Example with expected metadata
        prediction: Prediction with skill_metadata
        trace: Optional trace (unused)
    
    Returns:
        Score 0.0-1.0
    """
    score = 0.0
    
    # Check if metadata exists
    if not hasattr(prediction, "skill_metadata"):
        return 0.0
    
    metadata = prediction.skill_metadata
    
    # Check name is kebab-case
    if hasattr(metadata, "name"):
        name = metadata.name
        if re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            score += 0.25
    
    # Check description starts with "Use when..."
    if hasattr(metadata, "description"):
        desc = metadata.description.strip()
        if desc.startswith("Use when") or desc.startswith("use when"):
            score += 0.25
        
        # Check description length (should be 10-30 words)
        word_count = len(desc.split())
        if 10 <= word_count <= 40:
            score += 0.15
    
    # Check tags exist and are diverse
    if hasattr(metadata, "tags"):
        tags = metadata.tags
        if isinstance(tags, list) and 3 <= len(tags) <= 7:
            score += 0.2
            # Check tags are lowercase and reasonable
            if all(isinstance(t, str) and t.islower() for t in tags):
                score += 0.15
    
    return min(score, 1.0)


def skill_style_alignment_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Evaluate if predicted skill style matches expected style.
    
    Args:
        example: Example with expected_skill_style
        prediction: Prediction with skill_style
        trace: Optional trace (unused)
    
    Returns:
        Score 0.0-1.0
    """
    if not hasattr(example, "expected_skill_style"):
        return 0.5  # Neutral if no expectation
    
    expected_style = example.expected_skill_style
    
    # Try different field names
    predicted_style = None
    for field in ["skill_style", "style", "estimated_length"]:
        if hasattr(prediction, field):
            predicted_style = getattr(prediction, field)
            break
    
    if not predicted_style:
        return 0.0
    
    # Direct match
    if predicted_style == expected_style:
        return 1.0
    
    # Fuzzy match for length vs. style
    style_length_map = {
        "navigation_hub": "short",
        "comprehensive": "medium",
        "minimal": "short",
    }
    
    if predicted_style in style_length_map and style_length_map[predicted_style] == expected_style:
        return 0.7
    
    return 0.0


def comprehensive_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """Comprehensive metric combining multiple quality dimensions.
    
    Weights:
    - 40%: Taxonomy accuracy
    - 30%: Metadata quality
    - 30%: Style alignment
    
    Args:
        example: Training example
        prediction: Model prediction
        trace: Optional trace (unused)
    
    Returns:
        Weighted score 0.0-1.0
    """
    taxonomy_score = taxonomy_accuracy_metric(example, prediction, trace)
    metadata_score = metadata_quality_metric(example, prediction, trace)
    style_score = skill_style_alignment_metric(example, prediction, trace)
    
    weighted_score = (
        0.4 * taxonomy_score +
        0.3 * metadata_score +
        0.3 * style_score
    )
    
    return weighted_score


def create_metric_for_phase(phase: str) -> Callable:
    """Create appropriate metric for a specific workflow phase.
    
    Args:
        phase: Workflow phase name ('understanding', 'generation', 'validation')
    
    Returns:
        Metric function suitable for that phase
    """
    if phase == "understanding":
        # Focus on taxonomy and intent accuracy
        return lambda ex, pred, trace=None: (
            0.6 * taxonomy_accuracy_metric(ex, pred, trace) +
            0.4 * metadata_quality_metric(ex, pred, trace)
        )
    
    elif phase == "generation":
        # Focus on comprehensive quality
        return comprehensive_metric
    
    elif phase == "validation":
        # Focus on metadata and style compliance
        return lambda ex, pred, trace=None: (
            0.5 * metadata_quality_metric(ex, pred, trace) +
            0.5 * skill_style_alignment_metric(ex, pred, trace)
        )
    
    else:
        # Default: comprehensive
        return comprehensive_metric
