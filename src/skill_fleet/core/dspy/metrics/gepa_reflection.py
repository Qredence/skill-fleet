"""GEPA-optimized metrics with reflection feedback.

GEPA (Generalized Efficient Prompt Algorithm) is a reflection-based optimizer that:
1. Runs your program
2. Analyzes failures using the reflection_lm
3. Uses LM feedback to improve instructions iteratively

This module provides metrics designed specifically for GEPA's reflection loop.
Key difference from standard metrics: GEPA metrics return detailed feedback
that the reflection_lm can use to improve instructions.

GEPA Metric Signature:
    metric(gold, pred, trace=None, pred_name=None, pred_trace=None) -> dict
    
    Returns:
        {
            "score": float (0.0-1.0),
            "feedback": str (explanation for reflection_lm)
        }
"""

from __future__ import annotations

import re
from typing import Any

import dspy


def gepa_skill_quality_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: dspy.Trace | None = None,
    pred_name: str | None = None,
    pred_trace: dspy.Trace | None = None,
) -> dict[str, Any]:
    """GEPA-compatible skill quality metric with reflection feedback.
    
    Evaluates skill quality across multiple dimensions and provides
    detailed feedback that GEPA's reflection_lm can use to improve prompts.
    
    Args:
        gold: Expected example from training set
        pred: Model's prediction
        trace: Execution trace (optional)
        pred_name: Name of the predictor (GEPA-specific)
        pred_trace: Predictor's trace (GEPA-specific)
    
    Returns:
        {
            "score": 0.0-1.0,
            "feedback": Detailed feedback for reflection LM
        }
    """
    score = 0.0
    feedback_parts = []
    
    # ========== Field Presence Checks ==========
    field_checks = {
        "domain": ("Domain field present", 0.15),
        "category": ("Skill category identified", 0.15),
        "target_level": ("Target level determined", 0.15),
        "skill_style": ("Skill style detected", 0.10),
    }
    
    for field, (description, weight) in field_checks.items():
        if hasattr(pred, field) and getattr(pred, field):
            score += weight
        else:
            feedback_parts.append(f"❌ Missing or empty {field}")
    
    # ========== Content Quality Checks ==========
    
    # Check topics/keywords (should be list with 3+ items)
    if hasattr(pred, "topics") and isinstance(pred.topics, list) and len(pred.topics) >= 3:
        score += 0.10
    elif hasattr(pred, "topics"):
        feedback_parts.append(f"⚠️  Topics count: {len(getattr(pred, 'topics', []))} (need 3+)")
    else:
        feedback_parts.append("❌ Missing topics/keywords")
    
    # Check description quality
    if hasattr(pred, "description") and pred.description:
        desc_len = len(pred.description.split())
        if desc_len >= 10:  # Reasonable description length
            score += 0.10
        else:
            feedback_parts.append(f"⚠️  Description too short: {desc_len} words (need 10+)")
    else:
        feedback_parts.append("❌ Missing skill description")
    
    # ========== Accuracy Checks ==========
    
    # Check taxonomy path accuracy (if available)
    if hasattr(gold, "expected_taxonomy_path") and hasattr(pred, "category"):
        expected_category = gold.expected_taxonomy_path.split("/")[0]
        predicted_category = pred.category.lower() if hasattr(pred, "category") else ""
        
        if predicted_category and expected_category.lower() in predicted_category:
            score += 0.10
        else:
            feedback_parts.append(
                f"⚠️  Category mismatch: predicted '{predicted_category}' "
                f"vs expected '{expected_category}'"
            )
    
    # ========== Structure Checks ==========
    
    # Check if this looks like a complete skill
    required_outline_items = ["overview", "when to use", "quick start", "key insight"]
    if hasattr(pred, "outline") and pred.outline:
        found_items = sum(
            1 for item in required_outline_items 
            if item.lower() in str(pred.outline).lower()
        )
        structure_score = min(found_items / len(required_outline_items), 1.0) * 0.15
        score += structure_score
        
        if found_items < len(required_outline_items):
            missing = [item for item in required_outline_items 
                      if item.lower() not in str(pred.outline).lower()]
            feedback_parts.append(f"⚠️  Missing outline sections: {', '.join(missing)}")
    else:
        feedback_parts.append("❌ No outline/structure provided")
    
    # ========== Positive Feedback ==========
    
    # If score is high, provide encouraging feedback
    if score >= 0.8:
        feedback_parts.insert(0, "✅ Strong foundation")
    elif score >= 0.6:
        feedback_parts.insert(0, "🟡 Decent structure, room for improvement")
    else:
        feedback_parts.insert(0, "🔴 Need significant improvements")
    
    # ========== Reflection Guidance ==========
    
    # Provide specific guidance based on what's missing
    if score < 0.7:
        if "Missing topics" in "\n".join(feedback_parts):
            feedback_parts.append("📌 Try: Ask for at least 5-7 key topics the skill covers")
        
        if "Missing outline" in "\n".join(feedback_parts):
            feedback_parts.append("📌 Try: Request clear section headings (Overview, When to Use, etc.)")
        
        if "Category mismatch" in "\n".join(feedback_parts):
            feedback_parts.append("📌 Try: Ask the model to confirm the skill's domain/category first")
    
    final_feedback = "\n".join(feedback_parts)
    
    return {
        "score": min(score, 1.0),
        "feedback": final_feedback,
    }


def gepa_semantic_match_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: dspy.Trace | None = None,
    pred_name: str | None = None,
    pred_trace: dspy.Trace | None = None,
) -> dict[str, Any]:
    """GEPA metric: Semantic match between expected and predicted.
    
    Simpler, faster metric focused on whether the output is semantically
    aligned with expectations.
    
    Returns:
        {
            "score": 0.0-1.0,
            "feedback": str
        }
    """
    score = 0.0
    feedback_parts = []
    
    # Check if we got a meaningful skill
    has_name = bool(hasattr(pred, "name") and pred.name)
    has_desc = bool(hasattr(pred, "description") and pred.description and len(pred.description) > 20)
    has_structure = bool(hasattr(pred, "outline") or hasattr(pred, "topics"))
    
    checks = [
        (has_name, "❌ No skill name/title"),
        (has_desc, "❌ Description missing or too short"),
        (has_structure, "❌ No outline or topic structure"),
    ]
    
    for check, fail_msg in checks:
        if check:
            score += 0.25
        else:
            feedback_parts.append(fail_msg)
    
    # Final weight
    score = min(score, 1.0)
    
    if score >= 0.75:
        feedback_parts.insert(0, "✅ Output looks like a valid skill")
    else:
        feedback_parts.insert(0, "⚠️  Output doesn't look like a complete skill")
    
    return {
        "score": score,
        "feedback": "\n".join(feedback_parts),
    }


def gepa_composite_metric(
    gold: dspy.Example,
    pred: dspy.Prediction,
    trace: dspy.Trace | None = None,
    pred_name: str | None = None,
    pred_trace: dspy.Trace | None = None,
) -> dict[str, Any]:
    """GEPA metric: Weighted combination of quality checks.
    
    Uses multiple quality signals to provide comprehensive feedback
    that guides GEPA's instruction refinement.
    
    Returns:
        {
            "score": 0.0-1.0,
            "feedback": str (for reflection_lm)
        }
    """
    # Get individual metric results
    quality_result = gepa_skill_quality_metric(gold, pred, trace, pred_name, pred_trace)
    semantic_result = gepa_semantic_match_metric(gold, pred, trace, pred_name, pred_trace)
    
    # Composite score (70% quality, 30% semantic)
    composite_score = (quality_result["score"] * 0.7) + (semantic_result["score"] * 0.3)
    
    # Combine feedback
    feedback = f"""COMPOSITE EVALUATION:

Quality Assessment (70% weight): {quality_result['score']:.2%}
{quality_result['feedback']}

Semantic Validation (30% weight): {semantic_result['score']:.2%}
{semantic_result['feedback']}

Overall Score: {composite_score:.2%}
"""
    
    return {
        "score": min(composite_score, 1.0),
        "feedback": feedback.strip(),
    }
