"""Tests for refined content generation module."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import dspy
import pytest

from skill_fleet.core.modules.generation.refined_content import (
    RefinedContentModule,
    SkillQualityReward,
    generate_refined_skill_content,
)


class TestSkillQualityReward:
    """Tests for SkillQualityReward class."""

    @pytest.fixture
    def reward_fn(self):
        """Create a skill quality reward function."""
        return SkillQualityReward()

    def test_returns_score_between_0_and_1(self, reward_fn):
        """Test that reward returns score in valid range."""
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

## Instructions
Do something useful.

## Examples
```python
print("hello")
```

## When to Use
Use when testing.
"""
        score = reward_fn(content)
        assert 0.0 <= score <= 1.0

    def test_complete_skill_gets_higher_score(self, reward_fn):
        """Test that complete skill gets higher score."""
        complete = """---
name: complete-skill
description: A complete skill
---

# Complete Skill

## Instructions
Step 1: Do this.
Step 2: Do that.

## Examples
```python
# Example 1
print("hello")
```

```python
# Example 2
print("world")
```

## When to Use
Use this skill when you need to test things.
"""

        incomplete = "This is just some text without structure."

        complete_score = reward_fn(complete)
        incomplete_score = reward_fn(incomplete)

        assert complete_score > incomplete_score

    def test_skill_with_frontmatter_gets_higher_score(self, reward_fn):
        """Test that skill with frontmatter gets higher score."""
        with_frontmatter = """---
name: test-skill
description: A test skill
---

# Test Skill

## Instructions
Do something.

## Examples
Example here.

## When to Use
Use when testing.
"""

        without_frontmatter = """# Test Skill

## Instructions
Do something.

## Examples
Example here.

## When to Use
Use when testing.
"""

        with_score = reward_fn(with_frontmatter)
        without_score = reward_fn(without_frontmatter)

        assert with_score > without_score

    def test_optimal_length_gets_higher_score(self, reward_fn):
        """Test that optimal length content gets higher score."""
        # Very short content
        short = """---
name: short
description: Short
---

# Short

Brief."""

        # Very long content (simulated)
        long = (
            """---
name: long
description: Long skill
---

# Long Skill

"""
            + "word " * 6000
        )  # Over 5000 words

        # Optimal length
        optimal = (
            """---
name: optimal
description: Optimal skill
---

# Optimal Skill

## Instructions
"""
            + "Detailed instructions here. " * 500
            + """

## Examples
```python
print("example")
```

## When to Use
Use this skill for optimal results.
"""
        )

        short_score = reward_fn(short)
        long_score = reward_fn(long)
        optimal_score = reward_fn(optimal)

        assert optimal_score > short_score
        assert optimal_score > long_score


class TestRefinedContentModule:
    """Tests for RefinedContentModule class."""

    @pytest.fixture
    def module(self):
        """Create a refined content module."""
        return RefinedContentModule()

    @pytest.fixture
    def sample_plan(self):
        """Create a sample skill plan."""
        return {
            "skill_name": "test-skill",
            "skill_description": "A test skill",
            "content_outline": ["Introduction", "Instructions", "Examples"],
            "taxonomy_path": "testing/test-skill",
        }

    @pytest.fixture
    def sample_understanding(self):
        """Create a sample understanding."""
        return {
            "requirements": {"domain": "technical"},
            "skill_category": "other",
        }

    @pytest.fixture
    def mock_generated_content(self):
        """Create mock generated content."""
        return dspy.Prediction(
            skill_content="""---
name: test-skill
description: A test skill
---

# Test Skill

## Instructions
Do something useful.

## Examples
```python
print("hello")
```

## When to Use
Use when testing.
""",
            sections_generated=["Instructions", "Examples", "When to Use"],
            code_examples_count=1,
            estimated_reading_time=5,
        )

    @pytest.mark.asyncio
    async def test_aforward_returns_prediction(
        self, module, sample_plan, sample_understanding, mock_generated_content
    ):
        """Test that aforward returns a Prediction."""
        with patch.object(
            module.generator, "acall", AsyncMock(return_value=mock_generated_content)
        ):
            result = await module.aforward(
                plan=sample_plan,
                understanding=sample_understanding,
            )

        assert isinstance(result, dspy.Prediction)
        assert hasattr(result, "skill_content")
        assert hasattr(result, "quality_score")

    @pytest.mark.asyncio
    async def test_quality_score_in_result(
        self, module, sample_plan, sample_understanding, mock_generated_content
    ):
        """Test that quality score is included in result."""
        with patch.object(
            module.generator, "acall", AsyncMock(return_value=mock_generated_content)
        ):
            result = await module.aforward(
                plan=sample_plan,
                understanding=sample_understanding,
            )

        assert hasattr(result, "quality_score")
        assert 0.0 <= result.quality_score <= 1.0

    @pytest.mark.asyncio
    async def test_includes_iterations(
        self, module, sample_plan, sample_understanding, mock_generated_content
    ):
        """Test that result includes iteration count."""
        with patch.object(
            module.generator, "acall", AsyncMock(return_value=mock_generated_content)
        ):
            result = await module.aforward(
                plan=sample_plan,
                understanding=sample_understanding,
                target_quality=0.99,  # High target to trigger iterations
                max_iterations=2,
            )

        assert hasattr(result, "iterations")
        assert result.iterations >= 0

    @pytest.mark.asyncio
    async def test_target_met_when_quality_sufficient(
        self, module, sample_plan, sample_understanding, mock_generated_content
    ):
        """Test that target_met is True when quality is sufficient."""
        with patch.object(
            module.generator, "acall", AsyncMock(return_value=mock_generated_content)
        ):
            result = await module.aforward(
                plan=sample_plan,
                understanding=sample_understanding,
                target_quality=0.5,  # Low target should be met
            )

        assert hasattr(result, "target_met")
        # With good content and low target, should be met
        assert result.target_met is True

    @pytest.mark.asyncio
    async def test_includes_improvements(
        self, module, sample_plan, sample_understanding, mock_generated_content
    ):
        """Test that result includes improvements list."""
        with patch.object(
            module.generator, "acall", AsyncMock(return_value=mock_generated_content)
        ):
            result = await module.aforward(
                plan=sample_plan,
                understanding=sample_understanding,
            )

        assert hasattr(result, "improvements")
        assert isinstance(result.improvements, list)

    def test_forward_runs_async(self, module, sample_plan, sample_understanding):
        """Test that forward runs async version."""
        with patch.object(module, "aforward", AsyncMock(return_value=dspy.Prediction())) as mock:
            module.forward(
                plan=sample_plan,
                understanding=sample_understanding,
            )
            mock.assert_called_once()


class TestGenerateRefinedSkillContent:
    """Tests for generate_refined_skill_content convenience function."""

    def test_returns_prediction(self):
        """Test that function returns a Prediction."""
        mock_result = dspy.Prediction(
            skill_content="# Test Skill",
            quality_score=0.85,
        )

        with patch.object(RefinedContentModule, "forward", return_value=mock_result):
            result = generate_refined_skill_content(
                plan={"skill_name": "test"},
                understanding={"requirements": {}},
                target_quality=0.8,
            )

        assert isinstance(result, dspy.Prediction)
        assert result.quality_score == 0.85
