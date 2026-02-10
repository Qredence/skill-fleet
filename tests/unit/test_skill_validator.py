import json
from pathlib import Path

import pytest

from skill_fleet.validators import SkillValidator


@pytest.fixture
def temp_skills_root(tmp_path: Path) -> Path:
    """Create a temporary skills root with v2 template configuration."""
    skills_root = tmp_path / "skills"
    (skills_root / "_templates").mkdir(parents=True)

    # v2 Golden Standard: SKILL.md is required, metadata.json is optional
    template = {
        "metadata_template": {"skill_id": "{{taxonomy_path}}"},
        "directory_structure": ["references/", "guides/", "templates/", "scripts/", "examples/"],
        "required_files": ["SKILL.md"],  # v2: Only SKILL.md required
    }
    (skills_root / "_templates" / "skill_template.json").write_text(
        json.dumps(template), encoding="utf-8"
    )

    return skills_root


@pytest.fixture
def temp_skills_root_v1(tmp_path: Path) -> Path:
    """Create a temporary skills root with v1 template configuration."""
    skills_root = tmp_path / "skills_v1"
    (skills_root / "_templates").mkdir(parents=True)

    # v1: Both metadata.json and SKILL.md required
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
    """Test v2 skill validation - just SKILL.md with proper frontmatter, no subdirectories needed.

    v2 Golden Standard: A skill can be as simple as skill-name/SKILL.md
    Subdirectories are completely optional and only created when needed.
    """
    skill_dir = temp_skills_root / "technical_skills/programming/python"
    skill_dir.mkdir(parents=True)
    # NOTE: No subdirectories created - they are optional in v2

    # v2 SKILL.md with agentskills.io frontmatter and required sections
    skill_md = """---
name: python-basics
description: Use when learning Python fundamentals, writing basic scripts, or understanding core Python concepts.
---

# Python Skill

## Overview
This skill covers Python programming fundamentals.

## When to Use This Skill
Use this skill when:
- Learning Python basics
- Writing simple scripts
- Understanding core concepts

## Quick Start
```python
print('hello')
```

## Patterns
### Basic Pattern
Simple Python usage.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []


def test_validate_minimal_skill_just_skill_md(temp_skills_root: Path) -> None:
    """Test minimal v2 skill - just skill-name/SKILL.md, no subdirectories.

    This is the simplest valid v2 skill structure, similar to:
    - vibe-coding/SKILL.md
    - frontend-ui-integration/SKILL.md

    v2 Golden Standard allows skills to be as simple as a single SKILL.md file.
    Subdirectories are only created when there's actual content to put in them.
    """
    skill_dir = temp_skills_root / "guidelines/vibe-coding"
    skill_dir.mkdir(parents=True)
    # NO subdirectories - this is intentionally minimal

    # Minimal but complete SKILL.md with required frontmatter and "When to Use"
    skill_md = """---
name: vibe-coding
description: Rapidly prototype web apps with modern frameworks. Use when you want to quickly build something with creative flow.
---

# Vibe Coding

## Purpose
Rapidly prototype modern web applications.

## When to Use This Skill
- You want to **rapidly prototype** a new web application.
- You're in a **creative flow** and want to build quickly.
- You prefer **local development** with full control.

## Key Principles
1. Research current best practices before implementing
2. Initialize properly with all necessary tooling
3. Build and test features incrementally
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []
    # Minimal skill may have warnings about missing optional sections, but should pass


def test_validate_directory_skill_v1(temp_skills_root_v1: Path) -> None:
    """Test v1 skill validation - requires metadata.json."""
    skill_dir = temp_skills_root_v1 / "technical_skills/programming/python"
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

    skill_md = """---
name: python-basics
description: Python fundamentals
---

# Python Skill

## Overview
Python fundamentals.

## When to Use
Learning Python.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root_v1)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []


def test_validate_file_skill(temp_skills_root: Path) -> None:
    """Test validating a single .json file skill (legacy format)."""
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
    """Test v2 skill validation with missing optional sections generates warnings."""
    skill_dir = temp_skills_root / "general/testing"
    skill_dir.mkdir(parents=True)
    # NOTE: No subdirectories - they are optional in v2

    # v2: SKILL.md with frontmatter and required "When to Use" section
    # Missing: Overview, Quick Start (these generate warnings, not errors)
    skill_md = """---
name: test-skill
description: A test skill for validation.
---

# Test Skill

## When to Use This Skill
Use this when testing the validator.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []
    # Should have warnings about missing Overview, Quick Start, etc.
    assert results["warnings"]


def test_validation_failure_for_missing_when_to_use(temp_skills_root: Path) -> None:
    """Test v2 skill validation fails when 'When to Use' section is missing."""
    skill_dir = temp_skills_root / "general/bad_skill"
    skill_dir.mkdir(parents=True)
    # NOTE: No subdirectories - they are optional in v2

    # v2: SKILL.md with frontmatter but missing required "When to Use" section
    skill_md = """---
name: bad-skill
description: A skill missing the When to Use section.
---

# Bad Skill

## Overview
This skill is missing required sections.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is False
    # Should have error about missing "When to Use" section
    assert any("When to Use" in error for error in results["errors"])


def test_validation_failure_for_missing_fields_v1(temp_skills_root_v1: Path) -> None:
    """Test v1 skill validation fails when metadata.json is missing required fields."""
    skill_dir = temp_skills_root_v1 / "general/bad_skill"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    metadata = {"skill_id": "general/bad_skill"}
    (skill_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (skill_dir / "SKILL.md").write_text("# Bad Skill\n\n## Overview\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root_v1)
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
    # NOTE: No subdirectories - they are optional in v2

    # v2 SKILL.md with proper frontmatter and sections
    skill_md = """---
name: test-skill
description: A test skill.
---

# Test Skill

## When to Use This Skill
Use for testing.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # Inject malicious path traversal in required_files
    validator.required_files = ["SKILL.md", "../../../etc/passwd"]
    results = validator.validate_structure(skill_dir)

    # Should fail due to invalid path component
    assert not results.passed
    assert any("Invalid required file" in error for error in results.errors)


def test_validate_complete_blocks_metadata_symlink_escape(temp_skills_root_v1: Path) -> None:
    """Ensure metadata.json symlinks are rejected (avoid reading outside skills_root).

    Note: This test uses v1 template which requires metadata.json.
    """
    # Arrange
    validator = SkillValidator(temp_skills_root_v1)

    skill_dir = temp_skills_root_v1 / "general/symlink_metadata"
    skill_dir.mkdir(parents=True)
    for dirname in ["capabilities", "examples", "tests", "resources"]:
        (skill_dir / dirname).mkdir()

    outside_file = temp_skills_root_v1.parent / "outside-metadata.json"
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
    # NOTE: No subdirectories - they are optional in v2

    outside_md = temp_skills_root.parent / "outside-skill.md"
    outside_md.write_text(
        """---
name: outside-skill
description: A skill outside the skills root.
---

# Outside Skill

## When to Use This Skill
Never use this.
""",
        encoding="utf-8",
    )

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


def test_validate_frontmatter_optional_fields(temp_skills_root: Path) -> None:
    """Validate optional Claude/open-standard frontmatter fields are accepted."""
    skill_dir = temp_skills_root / "general/optional_frontmatter"
    skill_dir.mkdir(parents=True)

    skill_md = """---
name: optional-frontmatter
description: A skill with optional frontmatter fields.
model: claude-3-5
allowed-tools:
  - Read
  - Write
context: fork
agent: code-reviewer
hooks:
  - name: pre
    command: echo hi
disable-model-invocation: true
user-invocable: false
argument-hint: "path=/tmp/logs.txt"
license: MIT
---

# Optional Frontmatter Skill

## When to Use This Skill
Use this skill for testing optional frontmatter fields.
"""
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_complete(skill_dir)

    assert results["passed"] is True
    assert results["errors"] == []
    assert any("allowed-tools should be a space-delimited string" in w for w in results["warnings"])
