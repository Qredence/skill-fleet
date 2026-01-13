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


def test_path_injection_protection(temp_skills_root: Path) -> None:
    """Test that path traversal attacks in required_files and required_dirs are blocked."""
    validator = SkillValidator(temp_skills_root)

    # Test that path traversal patterns are rejected
    assert not validator._is_safe_path_component("../../../etc/passwd")
    assert not validator._is_safe_path_component("..\\..\\..\\windows\\system32")
    assert not validator._is_safe_path_component("..")
    assert not validator._is_safe_path_component(".")
    assert not validator._is_safe_path_component("/absolute/path")
    assert not validator._is_safe_path_component("C:\\windows\\path")
    assert not validator._is_safe_path_component("file\x00name")  # Null byte
    assert not validator._is_safe_path_component("")  # Empty string

    # Test that valid filenames are accepted
    assert validator._is_safe_path_component("metadata.json")
    assert validator._is_safe_path_component("SKILL.md")
    assert validator._is_safe_path_component("capabilities")
    assert validator._is_safe_path_component("file-name")
    assert validator._is_safe_path_component("file_name")
    assert validator._is_safe_path_component("file.multiple.dots")

    # Test actual validation with malicious required_files
    skill_dir = temp_skills_root / "general/test_skill"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    metadata = {
        "skill_id": "general/test_skill",
        "version": "1.0.0",
        "type": "technical",
        "weight": "lightweight",
        "load_priority": "on_demand",
        "dependencies": [],
        "capabilities": ["test"],
    }
    (skill_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# Test Skill\n\n## Overview\n", encoding="utf-8")

    # Inject malicious path traversal in required_files
    validator.required_files = ["metadata.json", "../../../etc/passwd"]
    results = validator.validate_structure(skill_dir)

    # Should fail due to invalid path component
    assert not results.passed
    assert any("Invalid required file" in error for error in results.errors)


def test_validate_complete_blocks_metadata_symlink_escape(temp_skills_root: Path) -> None:
    """Ensure metadata.json symlinks are rejected (avoid reading outside skills_root)."""
    # Arrange
    validator = SkillValidator(temp_skills_root)

    skill_dir = temp_skills_root / "general/symlink_metadata"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    outside_file = temp_skills_root.parent / "outside-metadata.json"
    outside_file.write_text(
        json.dumps(
            {
                "skill_id": "general/symlink_metadata",
                "version": "1.0.0",
                "type": "technical",
                "weight": "lightweight",
                "load_priority": "on_demand",
                "dependencies": [],
                "capabilities": ["test"],
            }
        ),
        encoding="utf-8",
    )

    metadata_link = skill_dir / "metadata.json"
    try:
        metadata_link.symlink_to(outside_file)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported in this environment")

    (skill_dir / "SKILL.md").write_text("# Test Skill\n\n## Overview\n", encoding="utf-8")

    # Act
    results = validator.validate_complete(skill_dir)

    # Assert
    assert results["passed"] is False
    assert any("metadata.json must not be a symlink" in e for e in results["errors"])


def test_validate_complete_blocks_skill_md_symlink_escape(temp_skills_root: Path) -> None:
    """Ensure SKILL.md symlinks are rejected (avoid reading outside skills_root)."""
    # Arrange
    validator = SkillValidator(temp_skills_root)

    skill_dir = temp_skills_root / "general/symlink_skill_md"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    (skill_dir / "metadata.json").write_text(
        json.dumps(
            {
                "skill_id": "general/symlink_skill_md",
                "version": "1.0.0",
                "type": "technical",
                "weight": "lightweight",
                "load_priority": "on_demand",
                "dependencies": [],
                "capabilities": ["test"],
            }
        ),
        encoding="utf-8",
    )

    outside_md = temp_skills_root.parent / "outside-skill.md"
    outside_md.write_text("---\nname: x\ndescription: y\n---\n", encoding="utf-8")

    skill_md_link = skill_dir / "SKILL.md"
    try:
        skill_md_link.symlink_to(outside_md)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported in this environment")

    # Act
    results = validator.validate_complete(skill_dir)

    # Assert
    assert results["passed"] is False
    assert any("SKILL.md must not be a symlink" in e for e in results["errors"])
