"""Unit tests for DSPy skill quality metrics."""

from __future__ import annotations

from skill_fleet.core.dspy.metrics import (
    SkillQualityScores,
    assess_skill_quality,
    compute_overall_score,
    evaluate_code_examples,
    evaluate_frontmatter,
    evaluate_patterns,
    evaluate_structure,
    parse_skill_content,
)

# Sample skill content for testing
EXCELLENT_SKILL_CONTENT = """---
name: test-skill
description: Use when building test applications with complex requirements
license: MIT
compatibility: Python 3.8+
metadata:
  skill_id: test/skill
  version: 1.0.0
  type: technical
  weight: medium
keywords:
  - testing
  - quality
---

# Test Skill

## Overview

This is a test skill for unit testing. **Core principle:** Always test your code.

## When to Use

**Use when:**
- Building applications that need testing
- Writing unit tests

**When NOT to use:**
- Simple scripts that don't need tests

## Quick Reference

| Problem | Solution | Keywords |
|---------|----------|----------|
| No tests | Write tests | testing, unit |
| Flaky tests | Fix isolation | flaky, isolation |

## Core Patterns

### 1. Basic Testing Pattern

**The problem:** Code without tests breaks silently.

**❌ Common mistake:**
```python
def add(a, b):
    return a + b
# No tests!
```

**✅ Production pattern:**
```python
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
```

**Key insight:** Always write tests alongside your code.

### 2. Async Testing Pattern

**The problem:** Async code is harder to test.

**❌ Common mistake:**
```python
async def fetch_data():
    return await api.get()
# Sync test won't work
```

**✅ Production pattern:**
```python
import pytest

@pytest.mark.asyncio
async def test_fetch_data():
    result = await fetch_data()
    assert result is not None
```

**Key insight:** Use pytest-asyncio for async tests.

### 3. Mock Pattern

**The problem:** External dependencies make tests slow and flaky.

**❌ Common mistake:**
```python
def test_api():
    result = real_api.call()  # Slow and unreliable
```

**✅ Production pattern:**
```python
from unittest.mock import Mock

def test_api():
    mock_api = Mock(return_value={"data": "test"})
    result = process(mock_api)
    assert result["data"] == "test"
```

**Key insight:** Mock external dependencies for fast, reliable tests.

### 4. Fixture Pattern

**The problem:** Test setup code is duplicated.

**❌ Common mistake:**
```python
def test_one():
    db = setup_database()
    # test code

def test_two():
    db = setup_database()  # Duplicated!
    # test code
```

**✅ Production pattern:**
```python
@pytest.fixture
def db():
    return setup_database()

def test_one(db):
    # test code

def test_two(db):
    # test code
```

**Key insight:** Use fixtures to share setup code.

### 5. Parameterized Testing

**The problem:** Testing multiple inputs requires duplicate tests.

**❌ Common mistake:**
```python
def test_add_1():
    assert add(1, 2) == 3

def test_add_2():
    assert add(0, 0) == 0
```

**✅ Production pattern:**
```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

**Key insight:** Parameterized tests reduce duplication.

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
|---------|----------------|-----|
| No tests | Bugs go undetected | Write tests |
| Slow tests | CI takes too long | Mock dependencies |
| Flaky tests | False failures | Fix isolation |

## Red Flags

- Tests that pass locally but fail in CI
- Tests that depend on execution order
- Tests that modify global state

**All of these mean: Fix your test isolation.**

## Real-World Impact

- 80% reduction in production bugs with good test coverage
- 50% faster debugging with clear test failures
- 90% confidence in refactoring with comprehensive tests
"""

MINIMAL_SKILL_CONTENT = """---
name: minimal-skill
description: A minimal skill
---

# Minimal Skill

## Overview

This is minimal.
"""

INCOMPLETE_SKILL_CONTENT = """# No Frontmatter Skill

Just some content without proper structure.
"""


class TestParseSkillContent:
    """Tests for parse_skill_content function."""

    def test_parse_with_frontmatter(self):
        """Test parsing skill with YAML frontmatter."""
        frontmatter, body = parse_skill_content(EXCELLENT_SKILL_CONTENT)

        assert frontmatter["name"] == "test-skill"
        assert "Use when" in frontmatter["description"]
        assert frontmatter["metadata"]["version"] == "1.0.0"
        assert "## Overview" in body

    def test_parse_without_frontmatter(self):
        """Test parsing skill without frontmatter."""
        frontmatter, body = parse_skill_content(INCOMPLETE_SKILL_CONTENT)

        assert frontmatter == {}
        assert "# No Frontmatter Skill" in body

    def test_parse_minimal_frontmatter(self):
        """Test parsing skill with minimal frontmatter."""
        frontmatter, body = parse_skill_content(MINIMAL_SKILL_CONTENT)

        assert frontmatter["name"] == "minimal-skill"
        assert "## Overview" in body


class TestEvaluateFrontmatter:
    """Tests for evaluate_frontmatter function."""

    def test_excellent_frontmatter(self):
        """Test evaluation of excellent frontmatter."""
        frontmatter, _ = parse_skill_content(EXCELLENT_SKILL_CONTENT)
        score, issues, strengths = evaluate_frontmatter(frontmatter)

        assert score >= 0.8
        assert "Has skill name" in strengths
        assert "Description follows 'Use when...' pattern" in strengths
        assert len(issues) < len(strengths)

    def test_minimal_frontmatter(self):
        """Test evaluation of minimal frontmatter."""
        frontmatter, _ = parse_skill_content(MINIMAL_SKILL_CONTENT)
        score, issues, strengths = evaluate_frontmatter(frontmatter)

        assert score >= 0.3  # Has name and description
        assert score < 0.8  # Missing metadata
        # Check that there are issues (description doesn't start with "Use when")
        assert len(issues) > 0

    def test_missing_frontmatter(self):
        """Test evaluation of missing frontmatter."""
        score, issues, strengths = evaluate_frontmatter({})

        assert score == 0.0
        assert "Missing required 'name' field" in issues
        assert "Missing required 'description' field" in issues


class TestEvaluateStructure:
    """Tests for evaluate_structure function."""

    def test_excellent_structure(self):
        """Test evaluation of excellent structure."""
        _, body = parse_skill_content(EXCELLENT_SKILL_CONTENT)
        flags, issues, strengths = evaluate_structure(body)

        assert flags["has_overview"] is True
        assert flags["has_when_to_use"] is True
        assert flags["has_quick_reference"] is True
        assert flags["has_common_mistakes"] is True
        assert flags["has_red_flags"] is True
        assert len(strengths) > len(issues)

    def test_minimal_structure(self):
        """Test evaluation of minimal structure."""
        _, body = parse_skill_content(MINIMAL_SKILL_CONTENT)
        flags, issues, strengths = evaluate_structure(body)

        assert flags["has_overview"] is True
        assert flags["has_when_to_use"] is False
        assert "Missing when to use section" in issues


class TestEvaluatePatterns:
    """Tests for evaluate_patterns function."""

    def test_excellent_patterns(self):
        """Test evaluation of excellent patterns."""
        _, body = parse_skill_content(EXCELLENT_SKILL_CONTENT)
        metrics, issues, strengths = evaluate_patterns(body)

        assert metrics["pattern_count"] >= 5
        assert metrics["has_anti_patterns"] is True
        assert metrics["has_production_patterns"] is True
        assert metrics["has_key_insights"] is True
        assert "Excellent pattern coverage" in strengths[0]

    def test_no_patterns(self):
        """Test evaluation with no patterns."""
        _, body = parse_skill_content(MINIMAL_SKILL_CONTENT)
        metrics, issues, strengths = evaluate_patterns(body)

        assert metrics["pattern_count"] == 0
        assert "No patterns found" in issues


class TestEvaluateCodeExamples:
    """Tests for evaluate_code_examples function."""

    def test_excellent_code_examples(self):
        """Test evaluation of excellent code examples."""
        _, body = parse_skill_content(EXCELLENT_SKILL_CONTENT)
        metrics, issues, strengths = evaluate_code_examples(body)

        assert metrics["code_examples_count"] >= 10
        assert metrics["code_examples_quality"] >= 0.7
        # Check that we have strengths related to code examples
        assert any("code" in s.lower() for s in strengths)

    def test_no_code_examples(self):
        """Test evaluation with no code examples."""
        _, body = parse_skill_content(MINIMAL_SKILL_CONTENT)
        metrics, issues, strengths = evaluate_code_examples(body)

        assert metrics["code_examples_count"] == 0
        assert metrics["code_examples_quality"] == 0.0
        assert "No code examples found" in issues


class TestComputeOverallScore:
    """Tests for compute_overall_score function."""

    def test_excellent_score(self):
        """Test overall score for excellent skill."""
        scores = SkillQualityScores(
            frontmatter_completeness=0.9,
            pattern_count=5,
            has_anti_patterns=True,
            has_key_insights=True,
            has_quick_reference=True,
            has_common_mistakes=True,
            has_red_flags=True,
            has_real_world_impact=True,
            code_examples_quality=0.9,
            # Obra/superpowers quality indicators (required for high scores)
            has_core_principle=True,
            has_strong_guidance=True,
            has_good_bad_contrast=True,
            description_quality=0.8,
        )
        overall = compute_overall_score(scores)

        assert overall >= 0.8

    def test_minimal_score(self):
        """Test overall score for minimal skill."""
        scores = SkillQualityScores(
            frontmatter_completeness=0.4,
            pattern_count=0,
            has_anti_patterns=False,
            has_key_insights=False,
            has_quick_reference=False,
            has_common_mistakes=False,
            has_red_flags=False,
            has_real_world_impact=False,
            code_examples_quality=0.0,
        )
        overall = compute_overall_score(scores)

        assert overall < 0.3

    def test_custom_weights(self):
        """Test overall score with custom weights."""
        scores = SkillQualityScores(
            frontmatter_completeness=1.0,
            pattern_count=5,  # Max pattern count
            has_anti_patterns=True,
            has_key_insights=True,
            has_quick_reference=True,
            has_common_mistakes=True,
            has_red_flags=True,
            has_real_world_impact=True,
            code_examples_quality=1.0,
            # Obra/superpowers quality indicators (required for high scores)
            has_core_principle=True,
            has_strong_guidance=True,
            has_good_bad_contrast=True,
            description_quality=1.0,
        )
        # All metrics at max should give high score
        overall = compute_overall_score(scores)

        assert overall >= 0.9


class TestAssessSkillQuality:
    """Tests for assess_skill_quality function."""

    def test_excellent_skill(self):
        """Test assessment of excellent skill."""
        scores = assess_skill_quality(EXCELLENT_SKILL_CONTENT)

        assert scores.overall_score >= 0.7
        assert scores.frontmatter_completeness >= 0.8
        assert scores.pattern_count >= 5
        assert scores.has_anti_patterns is True
        assert scores.has_key_insights is True
        assert len(scores.strengths) > len(scores.issues)

    def test_minimal_skill(self):
        """Test assessment of minimal skill."""
        scores = assess_skill_quality(MINIMAL_SKILL_CONTENT)

        assert scores.overall_score < 0.5
        assert scores.pattern_count == 0
        assert len(scores.issues) > 0

    def test_incomplete_skill(self):
        """Test assessment of incomplete skill."""
        scores = assess_skill_quality(INCOMPLETE_SKILL_CONTENT)

        assert scores.overall_score < 0.3
        assert scores.frontmatter_completeness == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        scores = assess_skill_quality(EXCELLENT_SKILL_CONTENT)
        result = scores.to_dict()

        assert "overall_score" in result
        assert "frontmatter_completeness" in result
        assert "pattern_count" in result
        assert "issues" in result
        assert "strengths" in result
        assert isinstance(result["issues"], list)
        assert isinstance(result["strengths"], list)
