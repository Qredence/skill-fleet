from types import SimpleNamespace

from skill_fleet.core.optimization.evaluation import (
    content_quality_metric,
    metadata_metric,
    skill_creation_metric,
    split_dataset,
    taxonomy_path_metric,
)


def test_split_dataset_splits_by_ratio() -> None:
    examples = list(range(10))
    train, val = split_dataset(examples, train_ratio=0.8)
    assert train == list(range(8))
    assert val == list(range(8, 10))


def test_taxonomy_path_metric_exact_match() -> None:
    gold = SimpleNamespace(expected_taxonomy_path="general/testing")
    pred = SimpleNamespace(understanding={"taxonomy_path": "general/testing"})
    assert taxonomy_path_metric(gold, pred) == 1.0


def test_taxonomy_path_metric_partial_match_same_root() -> None:
    gold = SimpleNamespace(expected_taxonomy_path="general/testing")
    pred = SimpleNamespace(understanding={"taxonomy_path": "general/other"})
    assert 0.0 < taxonomy_path_metric(gold, pred) < 1.0


def test_metadata_metric_scores_matches() -> None:
    gold = SimpleNamespace(
        expected_name="python-decorators",
        expected_type="technical",
        expected_weight="lightweight",
        expected_capabilities=["cap_one", "cap_two"],
    )
    pred = SimpleNamespace(
        plan={
            "skill_metadata": {
                "name": "python-decorators",
                "type": "technical",
                "weight": "lightweight",
                "capabilities": ["cap_one", "cap_two"],
            }
        }
    )

    assert metadata_metric(gold, pred) > 0.7


def test_content_quality_metric_requires_sections_and_code() -> None:
    pred = SimpleNamespace(
        content={
            "skill_content": """# Title

## Overview

## Capabilities

## Dependencies

## Usage Examples

```python
print('hello')
```
"""
        }
    )
    assert content_quality_metric(SimpleNamespace(), pred) > 0.3


def test_skill_creation_metric_combines_components() -> None:
    gold = SimpleNamespace(
        expected_taxonomy_path="general/testing",
        expected_name="workflow-testing",
        expected_type="technical",
        expected_weight="lightweight",
        expected_capabilities=["cap_one"],
    )
    pred = SimpleNamespace(
        understanding={"taxonomy_path": "general/testing"},
        plan={
            "skill_metadata": {
                "name": "workflow-testing",
                "type": "technical",
                "weight": "lightweight",
                "capabilities": ["cap_one"],
            }
        },
        content={
            "skill_content": """# Title

## Overview

## Capabilities

## Dependencies

## Usage Examples

```python
pass
```
"""
        },
    )

    score = skill_creation_metric(gold, pred)
    assert 0.0 <= score <= 1.0
    assert score > 0.5
