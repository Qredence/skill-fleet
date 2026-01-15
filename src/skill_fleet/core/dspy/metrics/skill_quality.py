"""Skill quality metrics for DSPy evaluation and optimization.

This module provides multi-dimensional quality assessment functions for evaluating
generated skills. These metrics are used by:
1. DSPy Evaluate for measuring skill quality
2. DSPy optimizers (MIPROv2, BootstrapFewShot) for optimization feedback
3. Validation pipeline for quality gates

Quality dimensions based on analysis of excellent skills (FastAPI, Anthropics, Obra):
- Structure completeness (frontmatter, sections)
- Pattern quality (anti-patterns, production patterns, key insights)
- Practical value (real-world impact, common mistakes, red flags)
- Code quality (executable examples, copy-paste ready)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import dspy
import yaml


@dataclass
class SkillQualityScores:
    """Detailed quality scores for a skill."""

    # Structure scores (0.0 - 1.0)
    frontmatter_completeness: float = 0.0
    has_overview: bool = False
    has_when_to_use: bool = False
    has_quick_reference: bool = False

    # Pattern scores
    pattern_count: int = 0
    has_anti_patterns: bool = False
    has_production_patterns: bool = False
    has_key_insights: bool = False

    # Practical value scores
    has_common_mistakes: bool = False
    has_red_flags: bool = False
    has_real_world_impact: bool = False

    # Code quality scores
    code_examples_count: int = 0
    code_examples_quality: float = 0.0

    # Obra/superpowers quality indicators (stricter criteria)
    has_core_principle: bool = False  # "Core principle:" statement
    has_strong_guidance: bool = False  # Iron Law / imperative rules
    has_good_bad_contrast: bool = False  # Paired Good/Bad or ❌/✅ examples
    description_quality: float = 0.0  # Quality of "Use when..." description

    # Overall
    overall_score: float = 0.0
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "frontmatter_completeness": self.frontmatter_completeness,
            "has_overview": self.has_overview,
            "has_when_to_use": self.has_when_to_use,
            "has_quick_reference": self.has_quick_reference,
            "pattern_count": self.pattern_count,
            "has_anti_patterns": self.has_anti_patterns,
            "has_production_patterns": self.has_production_patterns,
            "has_key_insights": self.has_key_insights,
            "has_common_mistakes": self.has_common_mistakes,
            "has_red_flags": self.has_red_flags,
            "has_real_world_impact": self.has_real_world_impact,
            "code_examples_count": self.code_examples_count,
            "code_examples_quality": self.code_examples_quality,
            # Obra/superpowers quality indicators
            "has_core_principle": self.has_core_principle,
            "has_strong_guidance": self.has_strong_guidance,
            "has_good_bad_contrast": self.has_good_bad_contrast,
            "description_quality": self.description_quality,
            # Overall
            "overall_score": self.overall_score,
            "issues": self.issues,
            "strengths": self.strengths,
        }


def parse_skill_content(skill_content: str) -> tuple[dict[str, Any], str]:
    """Parse SKILL.md content into frontmatter and body.

    Args:
        skill_content: Raw SKILL.md content

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    frontmatter: dict[str, Any] = {}
    body = skill_content

    # Check for YAML frontmatter
    if skill_content.startswith("---"):
        parts = skill_content.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                frontmatter = {}
            body = parts[2].strip()

    return frontmatter, body


def evaluate_frontmatter(frontmatter: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    """Evaluate frontmatter completeness.

    Required fields: name, description
    Recommended fields: metadata (skill_id, version, type, weight)
    Optional fields: license, compatibility, see_also, keywords

    Returns:
        Tuple of (score, issues, strengths)
    """
    issues: list[str] = []
    strengths: list[str] = []
    score = 0.0

    # Required fields (40% of score)
    if frontmatter.get("name"):
        score += 0.2
        strengths.append("Has skill name")
    else:
        issues.append("Missing required 'name' field")

    if frontmatter.get("description"):
        desc = str(frontmatter["description"])
        score += 0.2
        if desc.lower().startswith("use when"):
            score += 0.1
            strengths.append("Description follows 'Use when...' pattern")
        else:
            issues.append("Description should start with 'Use when...'")
    else:
        issues.append("Missing required 'description' field")

    # Metadata fields (30% of score)
    metadata = frontmatter.get("metadata", {})
    if isinstance(metadata, dict):
        if metadata.get("skill_id"):
            score += 0.1
        if metadata.get("version"):
            score += 0.1
        if metadata.get("type"):
            score += 0.05
        if metadata.get("weight"):
            score += 0.05
        if all(metadata.get(k) for k in ["skill_id", "version", "type"]):
            strengths.append("Complete metadata section")
    else:
        issues.append("Missing or invalid 'metadata' section")

    # Optional fields (20% of score)
    if frontmatter.get("keywords"):
        score += 0.05
    if frontmatter.get("license"):
        score += 0.05
    if frontmatter.get("compatibility"):
        score += 0.05
    if frontmatter.get("see_also"):
        score += 0.05

    return min(score, 1.0), issues, strengths


def evaluate_structure(body: str) -> tuple[dict[str, bool], list[str], list[str]]:
    """Evaluate skill body structure for required sections.

    Returns:
        Tuple of (section_flags, issues, strengths)
    """
    issues: list[str] = []
    strengths: list[str] = []

    # Section detection patterns
    sections = {
        "has_overview": r"##\s*(Overview|Introduction)",
        "has_when_to_use": r"##\s*When\s+(to\s+)?Use",
        "has_quick_reference": r"##\s*Quick\s+Reference",
        "has_core_patterns": r"##\s*(Core\s+)?Patterns?",
        "has_common_mistakes": r"##\s*Common\s+Mistakes?",
        "has_red_flags": r"##\s*Red\s+Flags?",
        "has_real_world_impact": r"##\s*(Real[- ]World\s+Impact|Impact|Benefits)",
    }

    flags: dict[str, bool] = {}
    for key, pattern in sections.items():
        flags[key] = bool(re.search(pattern, body, re.IGNORECASE))

    # Evaluate and report
    required_sections = ["has_overview", "has_when_to_use", "has_core_patterns"]
    recommended_sections = ["has_quick_reference", "has_common_mistakes", "has_red_flags"]

    for section in required_sections:
        if flags.get(section):
            strengths.append(f"Has {section.replace('has_', '').replace('_', ' ')} section")
        else:
            issues.append(f"Missing {section.replace('has_', '').replace('_', ' ')} section")

    for section in recommended_sections:
        if flags.get(section):
            strengths.append(f"Has {section.replace('has_', '').replace('_', ' ')} section")

    if flags.get("has_real_world_impact"):
        strengths.append("Includes real-world impact/benefits")

    return flags, issues, strengths


def evaluate_patterns(body: str) -> tuple[dict[str, Any], list[str], list[str]]:
    """Evaluate pattern quality in skill content.

    Looks for:
    - Pattern count (target: 5+)
    - Anti-pattern examples (❌)
    - Production pattern examples (✅)
    - Key insights after patterns

    Returns:
        Tuple of (pattern_metrics, issues, strengths)
    """
    issues: list[str] = []
    strengths: list[str] = []

    # Count patterns (### Pattern or ### 1. or ### Name:)
    pattern_headers = re.findall(r"###\s+(?:Pattern\s+)?\d*\.?\s*\w+", body)
    pattern_count = len(pattern_headers)

    # Check for anti-patterns and production patterns
    has_anti_patterns = bool(
        re.search(r"❌|Common\s+mistake|Anti[- ]?pattern|Don'?t", body, re.IGNORECASE)
    )
    has_production_patterns = bool(
        re.search(r"✅|Production\s+pattern|Correct|Do\s+this", body, re.IGNORECASE)
    )

    # Check for key insights
    has_key_insights = bool(
        re.search(
            r"\*\*Key\s+insight[s]?:?\*\*|\*\*Insight:?\*\*|Key\s+takeaway", body, re.IGNORECASE
        )
    )

    # Evaluate
    metrics = {
        "pattern_count": pattern_count,
        "has_anti_patterns": has_anti_patterns,
        "has_production_patterns": has_production_patterns,
        "has_key_insights": has_key_insights,
    }

    if pattern_count >= 5:
        strengths.append(f"Excellent pattern coverage ({pattern_count} patterns)")
    elif pattern_count >= 3:
        strengths.append(f"Good pattern coverage ({pattern_count} patterns)")
    elif pattern_count >= 1:
        issues.append(f"Limited patterns ({pattern_count}), target is 5+")
    else:
        issues.append("No patterns found")

    if has_anti_patterns and has_production_patterns:
        strengths.append("Shows both anti-patterns (❌) and production patterns (✅)")
    elif not has_anti_patterns:
        issues.append("Missing anti-pattern examples (❌)")
    elif not has_production_patterns:
        issues.append("Missing production pattern examples (✅)")

    if has_key_insights:
        strengths.append("Includes key insights after patterns")
    else:
        issues.append("Missing key insights after patterns")

    return metrics, issues, strengths


def evaluate_code_examples(body: str) -> tuple[dict[str, Any], list[str], list[str]]:
    """Evaluate code example quality.

    Checks for:
    - Code block count
    - Language specification
    - Reasonable code length
    - No placeholder code

    Returns:
        Tuple of (code_metrics, issues, strengths)
    """
    issues: list[str] = []
    strengths: list[str] = []

    # Find all code blocks
    code_blocks = re.findall(r"```(\w*)\n(.*?)```", body, re.DOTALL)
    code_count = len(code_blocks)

    # Evaluate code quality
    quality_score = 0.0
    if code_count > 0:
        # Base score for having code
        quality_score = 0.3

        # Check language specification
        specified_langs = sum(1 for lang, _ in code_blocks if lang)
        if specified_langs == code_count:
            quality_score += 0.2
            strengths.append("All code blocks have language specification")
        elif specified_langs > 0:
            quality_score += 0.1

        # Check for placeholder code
        placeholder_patterns = [
            r"\.\.\..*\.\.\.",
            r"#\s*TODO",
            r"pass\s*$",
            r"raise\s+NotImplementedError",
        ]
        has_placeholders = any(
            re.search(pattern, code, re.MULTILINE)
            for _, code in code_blocks
            for pattern in placeholder_patterns
        )
        if not has_placeholders:
            quality_score += 0.3
            strengths.append("Code examples are complete (no placeholders)")
        else:
            issues.append("Some code examples contain placeholders")

        # Check for reasonable code length (not too short)
        substantial_blocks = sum(1 for _, code in code_blocks if len(code.strip().split("\n")) >= 3)
        if substantial_blocks >= code_count * 0.7:
            quality_score += 0.2
            strengths.append("Code examples are substantial")

    metrics = {
        "code_examples_count": code_count,
        "code_examples_quality": min(quality_score, 1.0),
    }

    if code_count >= 5:
        strengths.append(f"Rich code examples ({code_count} blocks)")
    elif code_count >= 2:
        strengths.append(f"Has code examples ({code_count} blocks)")
    elif code_count == 0:
        issues.append("No code examples found")

    return metrics, issues, strengths


def evaluate_quality_indicators(
    body: str, frontmatter: dict[str, Any]
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Evaluate Obra/superpowers-style quality indicators.

    These are stricter criteria based on golden skills from:
    - https://github.com/obra/superpowers/tree/main/skills

    Checks for:
    - Core principle statement (strong, imperative)
    - Strong guidance / Iron Law (imperative rules)
    - Good/Bad contrast patterns (paired examples)
    - Description quality (specific triggering conditions)

    Returns:
        Tuple of (quality_metrics, issues, strengths)
    """
    issues: list[str] = []
    strengths: list[str] = []

    # Check for core principle statement
    # Patterns: "Core principle:", "**Core principle:**", "Core principle."
    has_core_principle = bool(
        re.search(
            r"\*\*Core\s+principle:?\*\*|Core\s+principle:|Core\s+principle\.",
            body,
            re.IGNORECASE,
        )
    )

    # Check for strong guidance / Iron Law
    # Patterns: "NO X WITHOUT Y", "ALWAYS", "NEVER", "MUST", "Iron Law"
    strong_guidance_patterns = [
        r"NO\s+\w+\s+WITHOUT",  # "NO FIXES WITHOUT ROOT CAUSE"
        r"Iron\s+Law",
        r"\*\*ALWAYS:?\*\*",
        r"\*\*NEVER:?\*\*",
        r"You\s+MUST",
        r"MANDATORY",
    ]
    has_strong_guidance = any(
        re.search(pattern, body, re.IGNORECASE) for pattern in strong_guidance_patterns
    )

    # Check for Good/Bad contrast patterns
    # Obra uses <Good> and <Bad> tags, FastAPI uses ❌/✅
    good_bad_patterns = [
        (r"<Good>", r"<Bad>"),  # Obra style
        (r"❌.*?✅|✅.*?❌", None),  # Emoji pairs (either order)
        (r"Common\s+mistake.*?Production\s+pattern", None),  # FastAPI style
    ]
    has_good_bad_contrast = False
    for good_pattern, bad_pattern in good_bad_patterns:
        if bad_pattern:
            if re.search(good_pattern, body, re.IGNORECASE | re.DOTALL) and re.search(
                bad_pattern, body, re.IGNORECASE | re.DOTALL
            ):
                has_good_bad_contrast = True
                break
        else:
            if re.search(good_pattern, body, re.IGNORECASE | re.DOTALL):
                has_good_bad_contrast = True
                break

    # Also check for paired ❌ and ✅ separately
    if not has_good_bad_contrast:
        has_bad = bool(re.search(r"❌", body))
        has_good = bool(re.search(r"✅", body))
        has_good_bad_contrast = has_bad and has_good

    # Evaluate description quality
    description_quality = 0.0
    desc = str(frontmatter.get("description", ""))
    if desc:
        # Base score for having description
        description_quality = 0.2

        # "Use when" pattern (+0.3)
        if desc.lower().startswith("use when"):
            description_quality += 0.3

        # Specific triggering conditions (+0.2)
        # Good: "Use when implementing any feature or bugfix, before writing implementation code"
        # Bad: "A skill for creating things"
        trigger_words = ["before", "after", "during", "when encountering", "if", "while"]
        if any(word in desc.lower() for word in trigger_words):
            description_quality += 0.2

        # Action-oriented (+0.15)
        action_words = ["implementing", "building", "creating", "debugging", "fixing", "writing"]
        if any(word in desc.lower() for word in action_words):
            description_quality += 0.15

        # Not too short, not too long (+0.15)
        word_count = len(desc.split())
        if 8 <= word_count <= 30:
            description_quality += 0.15

    # Report findings
    if has_core_principle:
        strengths.append("Has clear core principle statement")
    else:
        issues.append("Missing core principle statement (add '**Core principle:**')")

    if has_strong_guidance:
        strengths.append("Has strong imperative guidance (Iron Law style)")
    else:
        issues.append("Missing strong guidance (add imperative rules like 'NO X WITHOUT Y')")

    if has_good_bad_contrast:
        strengths.append("Has Good/Bad contrast examples")
    else:
        issues.append("Missing paired Good/Bad contrast examples")

    if description_quality >= 0.7:
        strengths.append("High-quality description with specific triggers")
    elif description_quality >= 0.5:
        strengths.append("Adequate description quality")
    else:
        issues.append("Description lacks specific triggering conditions")

    metrics = {
        "has_core_principle": has_core_principle,
        "has_strong_guidance": has_strong_guidance,
        "has_good_bad_contrast": has_good_bad_contrast,
        "description_quality": min(description_quality, 1.0),
    }

    return metrics, issues, strengths


def compute_overall_score(
    scores: SkillQualityScores, weights: dict[str, float] | None = None
) -> float:
    """Compute weighted overall quality score with stricter calibration.

    Applies Obra/superpowers-style quality standards:
    - Includes new quality indicators (core principle, strong guidance, etc.)
    - Applies penalty multiplier for missing critical elements
    - Calibrated against golden skills from https://github.com/obra/superpowers

    Args:
        scores: Individual quality scores
        weights: Optional custom weights (default uses config weights)

    Returns:
        Overall score between 0.0 and 1.0
    """
    if weights is None:
        # Updated weights with stricter calibration
        weights = {
            # Original metrics (reduced weights)
            "pattern_count": 0.10,  # Reduced from 0.15
            "has_anti_patterns": 0.08,  # Reduced from 0.10
            "has_key_insights": 0.08,  # Reduced from 0.10
            "has_real_world_impact": 0.08,  # Reduced from 0.10
            "has_quick_reference": 0.06,  # Reduced from 0.10
            "has_common_mistakes": 0.06,  # Reduced from 0.10
            "has_red_flags": 0.04,  # Reduced from 0.05
            "frontmatter_completeness": 0.10,  # Reduced from 0.15
            "code_examples_quality": 0.10,  # Reduced from 0.15
            # New Obra/superpowers quality indicators (30% total)
            "has_core_principle": 0.10,
            "has_strong_guidance": 0.08,
            "has_good_bad_contrast": 0.07,
            "description_quality": 0.05,
        }

    weighted_sum = 0.0
    total_weight = 0.0

    # Pattern count (normalized to 0-1, target is 5)
    pattern_score = min(scores.pattern_count / 5.0, 1.0)
    weighted_sum += pattern_score * weights.get("pattern_count", 0.10)
    total_weight += weights.get("pattern_count", 0.10)

    # Boolean scores (original)
    bool_metrics = [
        ("has_anti_patterns", scores.has_anti_patterns),
        ("has_key_insights", scores.has_key_insights),
        ("has_real_world_impact", scores.has_real_world_impact),
        ("has_quick_reference", scores.has_quick_reference),
        ("has_common_mistakes", scores.has_common_mistakes),
        ("has_red_flags", scores.has_red_flags),
    ]
    for metric_name, value in bool_metrics:
        weight = weights.get(metric_name, 0.08)
        weighted_sum += (1.0 if value else 0.0) * weight
        total_weight += weight

    # New Obra/superpowers boolean scores
    obra_bool_metrics = [
        ("has_core_principle", scores.has_core_principle),
        ("has_strong_guidance", scores.has_strong_guidance),
        ("has_good_bad_contrast", scores.has_good_bad_contrast),
    ]
    for metric_name, value in obra_bool_metrics:
        weight = weights.get(metric_name, 0.08)
        weighted_sum += (1.0 if value else 0.0) * weight
        total_weight += weight

    # Float scores
    weighted_sum += scores.frontmatter_completeness * weights.get("frontmatter_completeness", 0.10)
    total_weight += weights.get("frontmatter_completeness", 0.10)

    weighted_sum += scores.code_examples_quality * weights.get("code_examples_quality", 0.10)
    total_weight += weights.get("code_examples_quality", 0.10)

    weighted_sum += scores.description_quality * weights.get("description_quality", 0.05)
    total_weight += weights.get("description_quality", 0.05)

    # Calculate base score
    base_score = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Apply penalty multiplier for missing critical elements
    # Critical elements: core principle, strong guidance, good/bad contrast
    critical_count = sum(
        [
            scores.has_core_principle,
            scores.has_strong_guidance,
            scores.has_good_bad_contrast,
        ]
    )

    # Penalty: 0 critical = 0.7x, 1 critical = 0.85x, 2 critical = 0.95x, 3 critical = 1.0x
    penalty_multipliers = {0: 0.70, 1: 0.85, 2: 0.95, 3: 1.0}
    penalty_multiplier = penalty_multipliers.get(critical_count, 1.0)

    return base_score * penalty_multiplier


def assess_skill_quality(
    skill_content: str,
    weights: dict[str, float] | None = None,
) -> SkillQualityScores:
    """Comprehensive skill quality assessment.

    This is the main entry point for evaluating skill quality.

    Args:
        skill_content: Raw SKILL.md content
        weights: Optional custom metric weights

    Returns:
        SkillQualityScores with detailed assessment
    """
    scores = SkillQualityScores()

    # Parse content
    frontmatter, body = parse_skill_content(skill_content)

    # Evaluate frontmatter
    fm_score, fm_issues, fm_strengths = evaluate_frontmatter(frontmatter)
    scores.frontmatter_completeness = fm_score
    scores.issues.extend(fm_issues)
    scores.strengths.extend(fm_strengths)

    # Evaluate structure
    structure_flags, struct_issues, struct_strengths = evaluate_structure(body)
    scores.has_overview = structure_flags.get("has_overview", False)
    scores.has_when_to_use = structure_flags.get("has_when_to_use", False)
    scores.has_quick_reference = structure_flags.get("has_quick_reference", False)
    scores.has_common_mistakes = structure_flags.get("has_common_mistakes", False)
    scores.has_red_flags = structure_flags.get("has_red_flags", False)
    scores.has_real_world_impact = structure_flags.get("has_real_world_impact", False)
    scores.issues.extend(struct_issues)
    scores.strengths.extend(struct_strengths)

    # Evaluate patterns
    pattern_metrics, pattern_issues, pattern_strengths = evaluate_patterns(body)
    scores.pattern_count = pattern_metrics["pattern_count"]
    scores.has_anti_patterns = pattern_metrics["has_anti_patterns"]
    scores.has_production_patterns = pattern_metrics["has_production_patterns"]
    scores.has_key_insights = pattern_metrics["has_key_insights"]
    scores.issues.extend(pattern_issues)
    scores.strengths.extend(pattern_strengths)

    # Evaluate code examples
    code_metrics, code_issues, code_strengths = evaluate_code_examples(body)
    scores.code_examples_count = code_metrics["code_examples_count"]
    scores.code_examples_quality = code_metrics["code_examples_quality"]
    scores.issues.extend(code_issues)
    scores.strengths.extend(code_strengths)

    # Evaluate Obra/superpowers quality indicators (stricter criteria)
    quality_metrics, quality_issues, quality_strengths = evaluate_quality_indicators(
        body, frontmatter
    )
    scores.has_core_principle = quality_metrics["has_core_principle"]
    scores.has_strong_guidance = quality_metrics["has_strong_guidance"]
    scores.has_good_bad_contrast = quality_metrics["has_good_bad_contrast"]
    scores.description_quality = quality_metrics["description_quality"]
    scores.issues.extend(quality_issues)
    scores.strengths.extend(quality_strengths)

    # Compute overall score (includes penalty multiplier for missing critical elements)
    scores.overall_score = compute_overall_score(scores, weights)

    return scores


def skill_quality_metric(
    example: dspy.Example,
    prediction: dspy.Prediction,
    trace: Any = None,
) -> float:
    """DSPy-compatible metric function for skill quality.

    This function is designed to be used with dspy.Evaluate and DSPy optimizers.

    Args:
        example: DSPy example with expected outputs
        prediction: DSPy prediction with generated skill content
        trace: Optional trace for debugging

    Returns:
        Quality score between 0.0 and 1.0
    """
    # Extract skill content from prediction
    skill_content = ""
    if hasattr(prediction, "skill_content"):
        skill_content = prediction.skill_content
    elif hasattr(prediction, "content"):
        skill_content = prediction.content
    elif hasattr(prediction, "output"):
        skill_content = prediction.output
    elif isinstance(prediction, str):
        skill_content = prediction

    if not skill_content:
        return 0.0

    # Assess quality
    scores = assess_skill_quality(skill_content)
    return scores.overall_score


def skill_quality_metric_detailed(
    example: dspy.Example,
    prediction: dspy.Prediction,
    trace: Any = None,
) -> tuple[float, SkillQualityScores]:
    """DSPy-compatible metric with detailed scores.

    Returns both the overall score and detailed breakdown.

    Args:
        example: DSPy example with expected outputs
        prediction: DSPy prediction with generated skill content
        trace: Optional trace for debugging

    Returns:
        Tuple of (overall_score, detailed_scores)
    """
    skill_content = ""
    if hasattr(prediction, "skill_content"):
        skill_content = prediction.skill_content
    elif hasattr(prediction, "content"):
        skill_content = prediction.content
    elif hasattr(prediction, "output"):
        skill_content = prediction.output
    elif isinstance(prediction, str):
        skill_content = prediction

    if not skill_content:
        return 0.0, SkillQualityScores()

    scores = assess_skill_quality(skill_content)
    return scores.overall_score, scores


__all__ = [
    "SkillQualityScores",
    "assess_skill_quality",
    "compute_overall_score",
    "evaluate_code_examples",
    "evaluate_frontmatter",
    "evaluate_patterns",
    "evaluate_structure",
    "parse_skill_content",
    "skill_quality_metric",
    "skill_quality_metric_detailed",
]
