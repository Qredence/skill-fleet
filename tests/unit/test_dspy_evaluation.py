"""Unit tests for DSPy evaluation utilities."""

from __future__ import annotations

from skill_fleet.core.dspy.evaluation import SkillEvaluator


def test_evaluate_skill_derives_skill_name_from_frontmatter() -> None:
    evaluator = SkillEvaluator(configure_lm=False)
    content = """---
name: derived-skill-name
description: Use when testing evaluation name fallback.
---

# Title

## Overview

Text.
"""

    result = evaluator.evaluate_skill(skill_content=content)
    assert result.skill_name == "derived-skill-name"


def test_evaluate_skill_keeps_explicit_skill_name() -> None:
    evaluator = SkillEvaluator(configure_lm=False)
    content = """---
name: frontmatter-name
description: Use when testing explicit name behavior.
---

# Title
"""

    result = evaluator.evaluate_skill(skill_content=content, skill_name="caller-provided-name")
    assert result.skill_name == "caller-provided-name"
