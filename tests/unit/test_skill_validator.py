import json
from pathlib import Path

import pytest

from skill_fleet.validators import SkillValidator


@pytest.fixture
def temp_skills_root(tmp_path: Path) -> Path:
    skills_root = tmp_path / "skills"
    (skills_root / "_templates").mkdir(parents=True)

    template = {
        "metadata_template": {"skill_id": "{{taxonomy_path}}"},
        "directory_structure": ["capabilities/", "examples/", "tests/", "resources/"],
        "required_files": ["metadata.json", "SKILL.md"],
    }
    (skills_root / "_templates" / "skill_template.json").write_text(
        json.dumps(template), encoding="utf-8"
    )

    return skills_root


def test_validate_directory_skill(temp_skills_root: Path) -> None:
    skill_dir = temp_skills_root / "technical_skills/programming/python"
    skill_dir.mkdir(parents=True)
    (skill_dir / "capabilities").mkdir()
    (skill_dir / "examples").mkdir()
    (skill_dir / "tests").mkdir()
    (skill_dir / "resources").mkdir()

    metadata = {
        "skill_id": "technical_skills/programming/python",
        "version": "1.0.0",
        "type": "technical",
        "weight": "lightweight",
        "load_priority": "on_demand",
        "dependencies": [],
        "capabilities": ["python_basics"],
    }
    (skill_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    skill_md = """# Python Skill

## Overview

## Capabilities

## Dependencies

## Usage Examples

```python
print('hello')
```
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []


def test_validate_file_skill(temp_skills_root: Path) -> None:
    skill_file = temp_skills_root / "_core" / "reasoning.json"
    skill_file.parent.mkdir(parents=True)
    metadata = {
        "skill_id": "_core/reasoning",
        "version": "1.0.0",
        "type": "cognitive",
        "weight": "lightweight",
        "load_priority": "always",
        "dependencies": [],
        "capabilities": ["logical_inference"],
    }
    skill_file.write_text(json.dumps(metadata), encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_file)

    assert results["passed"] is True
    assert results["errors"] == []


def test_validation_warnings_for_missing_sections(temp_skills_root: Path) -> None:
    skill_dir = temp_skills_root / "general/testing"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    metadata = {
        "skill_id": "general/testing",
        "version": "1.0.0",
        "type": "technical",
        "weight": "lightweight",
        "load_priority": "on_demand",
        "dependencies": [],
        "capabilities": ["test"],
    }
    (skill_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# Test Skill\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []
    assert results["warnings"]


def test_validation_failure_for_missing_fields(temp_skills_root: Path) -> None:
    skill_dir = temp_skills_root / "general/bad_skill"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    metadata = {"skill_id": "general/bad_skill"}
    (skill_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# Bad Skill\n\n## Overview\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is False
    assert results["errors"]
