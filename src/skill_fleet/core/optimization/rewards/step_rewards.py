"""Reward functions for DSPy Refine and BestOfN modules.

These functions score LLM outputs for quality assurance, enabling:
- dspy.Refine: Automatic feedback loop to improve outputs
- dspy.BestOfN: Select best output from multiple attempts

All reward functions follow the signature:
    def reward_fn(args, pred: dspy.Prediction) -> float:
        # Returns score between 0.0 and 1.0
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dspy

logger = logging.getLogger(__name__)


# =============================================================================
# Step 1: Understand - Taxonomy Path Validation
# =============================================================================


def taxonomy_path_reward(args, pred: dspy.Prediction) -> float:
    """Score taxonomy path validity and confidence.

    Checks:
    - Valid path format (lowercase, underscores, slashes)
    - Reasonable depth (2-6 levels)
    - Confidence score above threshold

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        path = getattr(pred, "taxonomy_path", "")
        if isinstance(path, str):
            path = path.strip()

        # Valid path format (no spaces, proper separators)
        if re.match(r"^[a-z0-9_]+(/[a-z0-9_]+)*$", path):
            score += 0.4

        # Reasonable depth (2-6 levels)
        depth = len(path.split("/"))
        if 2 <= depth <= 6:
            score += 0.3
        elif depth == 1:
            score += 0.1  # Partial credit for single level

        # Starts with valid category
        valid_roots = [
            "_core",
            "technical_skills",
            "domain_knowledge",
            "tool_proficiency",
            "mcp_capabilities",
            "specializations",
            "task_focus_areas",
            "memory_blocks",
            "general",
        ]
        if path.split("/")[0] in valid_roots:
            score += 0.1

        # Confidence check
        confidence = getattr(pred, "confidence_score", 0.0)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = 0.0

        if confidence > 0.7:
            score += 0.2
        elif confidence > 0.5:
            score += 0.1

    except Exception as e:
        logger.warning(f"Error in taxonomy_path_reward: {e}")
        return 0.0

    return min(score, 1.0)


# =============================================================================
# Step 2: Plan - Metadata Completeness
# =============================================================================


def metadata_completeness_reward(args, pred: dspy.Prediction) -> float:
    """Score metadata completeness and agentskills.io compliance.

    Checks:
    - skill_id with valid path format
    - name in kebab-case (agentskills.io)
    - description of reasonable length
    - capabilities list
    - type and weight fields

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        # Handle both Pydantic model and dict/JSON string
        meta = getattr(pred, "skill_metadata", None)
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except json.JSONDecodeError:
                return 0.0

        if meta is None:
            return 0.0

        # For Pydantic models, convert to dict-like access
        def get_field(obj, field, default=None):
            """Get field value from object or dict with fallback.

            Args:
                obj: Object or dict to get field from
                field: Field name to retrieve
                default: Default value if field not found

            Returns:
                Field value or default if not found
            """
            if hasattr(obj, field):
                return getattr(obj, field)
            if isinstance(obj, dict):
                return obj.get(field, default)
            return default

        # skill_id with path format
        skill_id = get_field(meta, "skill_id", "")
        if skill_id and "/" in skill_id:
            score += 0.2

        # name in kebab-case
        name = get_field(meta, "name", "")
        if name and re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
            score += 0.2
        elif name:
            score += 0.1  # Partial credit for having a name

        # description length (50-1024 chars)
        description = get_field(meta, "description", "")
        if 50 <= len(description) <= 1024:
            score += 0.2
        elif len(description) > 20:
            score += 0.1

        # capabilities (2-10 items)
        capabilities = get_field(meta, "capabilities", [])
        if isinstance(capabilities, list) and 2 <= len(capabilities) <= 10:
            score += 0.2
        elif isinstance(capabilities, list) and len(capabilities) >= 1:
            score += 0.1

        # type and weight fields present
        skill_type = get_field(meta, "type", "")
        weight = get_field(meta, "weight", "")
        if skill_type and weight:
            score += 0.2
        elif skill_type or weight:
            score += 0.1

    except Exception as e:
        logger.warning(f"Error in metadata_completeness_reward: {e}")
        return 0.0

    return min(score, 1.0)


def capabilities_reward(args, pred: dspy.Prediction) -> float:
    """Score capabilities list quality.

    Checks:
    - Reasonable number of capabilities (2-10)
    - Each capability has name and description
    - Names are in snake_case format

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        capabilities = getattr(pred, "capabilities", None)
        if isinstance(capabilities, str):
            try:
                capabilities = json.loads(capabilities)
            except json.JSONDecodeError:
                return 0.0

        if not isinstance(capabilities, list):
            return 0.0

        # Number of capabilities (2-10 is ideal)
        count = len(capabilities)
        if 3 <= count <= 7:
            score += 0.4
        elif 2 <= count <= 10:
            score += 0.3
        elif count >= 1:
            score += 0.1

        # Check each capability
        valid_caps = 0
        for cap in capabilities:
            if isinstance(cap, dict):
                name = cap.get("name", "")
                desc = cap.get("description", "")
            elif hasattr(cap, "name"):
                name = cap.name
                desc = getattr(cap, "description", "")
            else:
                continue

            # Name in snake_case
            if re.match(r"^[a-z][a-z0-9_]*$", name):
                valid_caps += 0.5
            # Has description
            if len(desc) > 10:
                valid_caps += 0.5

        if count > 0:
            score += (valid_caps / count) * 0.6

    except Exception as e:
        logger.warning(f"Error in capabilities_reward: {e}")
        return 0.0

    return min(score, 1.0)


# =============================================================================
# Step 4: Edit - Content Quality
# =============================================================================


def skill_content_reward(args, pred: dspy.Prediction) -> float:
    """Score skill content quality (SKILL.md generation).

    Checks:
    - Required sections present (Overview, Capabilities, etc.)
    - Has code examples (``` blocks)
    - Reasonable length (500-5000 words)
    - Proper formatting

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        content = getattr(pred, "skill_content", "")
        if not isinstance(content, str) or not content:
            return 0.0

        # Required sections present
        required_sections = [
            "# ",  # Title
            "## Overview",
            "## Capabilities",
            "## Dependencies",
            "## Usage Examples",
        ]
        section_score = sum(1 for section in required_sections if section in content)
        score += (section_score / len(required_sections)) * 0.4

        # Has code examples
        code_blocks = content.count("```")
        if code_blocks >= 4:  # At least 2 complete code blocks
            score += 0.2
        elif code_blocks >= 2:
            score += 0.15
        elif code_blocks >= 1:
            score += 0.1

        # Reasonable length (500-5000 words)
        word_count = len(content.split())
        if 800 <= word_count <= 3000:
            score += 0.2
        elif 500 <= word_count <= 5000:
            score += 0.15
        elif 300 <= word_count:
            score += 0.1

        # Has proper markdown formatting
        formatting_elements = [
            r"\*\*.*?\*\*",  # Bold
            r"- ",  # Lists
            r"\d+\. ",  # Numbered lists
            r"###",  # Subsections
        ]
        format_count = sum(1 for pattern in formatting_elements if re.search(pattern, content))
        score += (format_count / len(formatting_elements)) * 0.2

    except Exception as e:
        logger.warning(f"Error in skill_content_reward: {e}")
        return 0.0

    return min(score, 1.0)


def usage_examples_reward(args, pred: dspy.Prediction) -> float:
    """Score usage examples quality.

    Checks:
    - Has multiple examples (2-5)
    - Each example has code
    - Examples have descriptions

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        examples = getattr(pred, "usage_examples", None)
        if isinstance(examples, str):
            try:
                examples = json.loads(examples)
            except json.JSONDecodeError:
                return 0.0

        if not isinstance(examples, list):
            return 0.0

        # Number of examples
        count = len(examples)
        if 2 <= count <= 5:
            score += 0.4
        elif count >= 1:
            score += 0.2

        # Check each example
        valid_examples = 0
        for ex in examples:
            if isinstance(ex, dict):
                code = ex.get("code", "")
                desc = ex.get("description", "")
            elif hasattr(ex, "code"):
                code = ex.code
                desc = getattr(ex, "description", "")
            else:
                continue

            if len(code) > 20:
                valid_examples += 0.5
            if len(desc) > 10:
                valid_examples += 0.5

        if count > 0:
            score += (valid_examples / count) * 0.6

    except Exception as e:
        logger.warning(f"Error in usage_examples_reward: {e}")
        return 0.0

    return min(score, 1.0)


# =============================================================================
# Step 5: Package - Validation Quality
# =============================================================================


def validation_report_reward(args, pred: dspy.Prediction) -> float:
    """Score validation report quality.

    Checks:
    - Has clear pass/fail status
    - Lists any errors/warnings found
    - Quality score is reasonable

    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0

    try:
        report = getattr(pred, "validation_report", None)
        if isinstance(report, str):
            try:
                report = json.loads(report)
            except json.JSONDecodeError:
                return 0.0

        if report is None:
            return 0.0

        # Get fields
        def get_field(obj, field, default=None):
            """Get field value from object or dict with fallback.

            Args:
                obj: Object or dict to get field from
                field: Field name to retrieve
                default: Default value if field not found

            Returns:
                Field value or default if not found
            """
            if hasattr(obj, field):
                return getattr(obj, field)
            if isinstance(obj, dict):
                return obj.get(field, default)
            return default

        # Has status field
        status = get_field(report, "status", "")
        if status in ["passed", "failed", "warnings"]:
            score += 0.3

        # Has passed boolean
        passed = get_field(report, "passed", None)
        if isinstance(passed, bool):
            score += 0.2

        # Has errors list (even if empty)
        errors = get_field(report, "errors", None)
        if isinstance(errors, list):
            score += 0.25

        # Has warnings list
        warnings = get_field(report, "warnings", None)
        if isinstance(warnings, list):
            score += 0.25

    except Exception as e:
        logger.warning(f"Error in validation_report_reward: {e}")
        return 0.0

    return min(score, 1.0)


def quality_score_reward(args, pred: dspy.Prediction) -> float:
    """Score the quality_score field validity.

    Returns:
        float: Score between 0.0 and 1.0
    """
    try:
        quality = getattr(pred, "quality_score", None)
        if isinstance(quality, str):
            try:
                quality = float(quality)
            except ValueError:
                return 0.0

        if quality is None:
            return 0.0

        # Valid range (0.0-1.0)
        if 0.0 <= quality <= 1.0:
            return 1.0
        else:
            return 0.0

    except Exception as e:
        logger.warning(f"Error in quality_score_reward: {e}")
        return 0.0


# =============================================================================
# Composite Rewards
# =============================================================================


def combined_plan_reward(args, pred: dspy.Prediction) -> float:
    """Combined reward for Plan step (metadata + capabilities).

    Returns:
        float: Weighted average score between 0.0 and 1.0
    """
    metadata_score = metadata_completeness_reward(args, pred)
    capabilities_score = capabilities_reward(args, pred)

    # Weight metadata higher as it's more critical
    return metadata_score * 0.6 + capabilities_score * 0.4


def combined_edit_reward(args, pred: dspy.Prediction) -> float:
    """Combined reward for Edit step (content + examples).

    Returns:
        float: Weighted average score between 0.0 and 1.0
    """
    content_score = skill_content_reward(args, pred)
    examples_score = usage_examples_reward(args, pred)

    # Weight content higher as it's the main deliverable
    return content_score * 0.7 + examples_score * 0.3


def combined_package_reward(args, pred: dspy.Prediction) -> float:
    """Combined reward for Package step (validation + quality).

    Returns:
        float: Weighted average score between 0.0 and 1.0
    """
    report_score = validation_report_reward(args, pred)
    quality_valid = quality_score_reward(args, pred)

    return report_score * 0.7 + quality_valid * 0.3
