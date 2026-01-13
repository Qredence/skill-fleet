from types import SimpleNamespace

from skill_fleet.core.optimization.rewards import (
    capabilities_reward,
    combined_edit_reward,
    combined_package_reward,
    combined_plan_reward,
    metadata_completeness_reward,
    quality_score_reward,
    skill_content_reward,
    taxonomy_path_reward,
    usage_examples_reward,
    validation_report_reward,
)


def test_taxonomy_path_reward_valid_path_scores_high() -> None:
    pred = SimpleNamespace(
        taxonomy_path="technical_skills/programming/languages/python",
        confidence_score=0.85,
    )
    score = taxonomy_path_reward(None, pred)
    assert 0.9 <= score <= 1.0


def test_taxonomy_path_reward_invalid_path_with_low_confidence_scores_low() -> None:
    pred = SimpleNamespace(taxonomy_path="Bad Path", confidence_score=0.0)
    assert taxonomy_path_reward(None, pred) <= 0.2


def test_taxonomy_path_reward_depth_one_gets_partial_credit() -> None:
    pred = SimpleNamespace(taxonomy_path="general", confidence_score=0.6)
    score = taxonomy_path_reward(None, pred)
    assert score > 0.0


def test_metadata_completeness_reward_valid_metadata_scores_higher() -> None:
    good = SimpleNamespace(
        skill_metadata={
            "skill_id": "general/testing",
            "name": "workflow-testing",
            "description": "A" * 60,
            "capabilities": ["a", "b"],
            "type": "technical",
            "weight": "lightweight",
        }
    )
    bad = SimpleNamespace(skill_metadata={"name": "Not Kebab"})

    assert metadata_completeness_reward(None, good) > metadata_completeness_reward(None, bad)


def test_capabilities_reward_prefers_snake_case_with_descriptions() -> None:
    pred = SimpleNamespace(
        capabilities=[
            {"name": "one_capability", "description": "description long enough"},
            {"name": "two_capability", "description": "description long enough"},
            {"name": "three_capability", "description": "description long enough"},
        ]
    )

    score = capabilities_reward(None, pred)
    assert score > 0.7


def test_skill_content_reward_checks_required_sections_and_code() -> None:
    content = """# Title

## Overview

Some overview.

## Capabilities

- One

## Dependencies

No dependencies.

## Usage Examples

```python
print('hello')
```

```bash
echo hi
```
"""
    pred = SimpleNamespace(skill_content=content)
    score = skill_content_reward(None, pred)
    assert score > 0.5


def test_usage_examples_reward_scores_structure() -> None:
    pred = SimpleNamespace(
        usage_examples=[
            {"code": "print('a' * 25)", "description": "demonstrates printing a"},
            {"code": "print('b' * 25)", "description": "demonstrates printing b"},
        ]
    )
    assert usage_examples_reward(None, pred) > 0.6


def test_validation_report_reward_and_quality_score_reward() -> None:
    pred = SimpleNamespace(
        validation_report={"status": "passed", "passed": True, "errors": [], "warnings": []},
        quality_score=0.75,
    )
    assert validation_report_reward(None, pred) >= 0.7
    assert quality_score_reward(None, pred) == 1.0


def test_composite_rewards_return_in_unit_interval() -> None:
    plan_pred = SimpleNamespace(
        skill_metadata={
            "skill_id": "general/testing",
            "name": "workflow-testing",
            "description": "A" * 60,
            "capabilities": ["a", "b"],
            "type": "technical",
            "weight": "lightweight",
        },
        capabilities=[
            {"name": "cap_one", "description": "desc"},
            {"name": "cap_two", "description": "desc"},
        ],
    )
    edit_pred = SimpleNamespace(
        skill_content="# Title\n\n## Overview\n\n## Capabilities\n\n## Dependencies\n\n## Usage Examples\n\n```python\npass\n```\n",
        usage_examples=[{"code": "print('x')", "description": "desc"}],
    )
    package_pred = SimpleNamespace(
        validation_report={"status": "passed", "passed": True, "errors": [], "warnings": []},
        quality_score=0.9,
    )

    for fn, pred in [
        (combined_plan_reward, plan_pred),
        (combined_edit_reward, edit_pred),
        (combined_package_reward, package_pred),
    ]:
        score = fn(None, pred)
        assert 0.0 <= score <= 1.0
