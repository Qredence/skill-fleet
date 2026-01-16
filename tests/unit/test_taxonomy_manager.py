import json
from pathlib import Path

import pytest

from skill_fleet.taxonomy.manager import TaxonomyManager


@pytest.fixture
def temp_taxonomy(tmp_path: Path) -> Path:
    skills_root = tmp_path / "skills"
    (skills_root / "_core").mkdir(parents=True)

    # Minimal taxonomy meta
    meta = {
        "version": "0.1.0",
        "created_at": "2026-01-06T00:00:00Z",
        "last_updated": "2026-01-06T00:00:00Z",
        "schema_version": "1.0.0",
        "total_skills": 0,
        "generation_count": 0,
        "statistics": {"by_type": {}, "by_weight": {}, "by_priority": {}},
    }
    (skills_root / "taxonomy_meta.json").write_text(json.dumps(meta), encoding="utf-8")

    # Core skill definition (single-file JSON)
    core_skill = {
        "skill_id": "_core/reasoning",
        "version": "1.0.0",
        "type": "cognitive",
        "weight": "lightweight",
        "load_priority": "always",
        "always_loaded": True,
        "dependencies": [],
        "capabilities": ["logical_inference"],
    }
    (skills_root / "_core" / "reasoning.json").write_text(json.dumps(core_skill), encoding="utf-8")

    return skills_root


def test_taxonomy_manager_initialization(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    assert manager.meta["version"] == "0.1.0"
    assert "_core/reasoning" in manager.metadata_cache
    assert manager.metadata_cache["_core/reasoning"].always_loaded is True


def test_skill_exists_check_for_file_skills(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    assert manager.skill_exists("_core/reasoning") is True
    assert manager.skill_exists("_core/does_not_exist") is False


def test_skill_exists_check_for_directory_skills(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    skill_dir = temp_taxonomy / "technical_skills/programming/languages/python"
    skill_dir.mkdir(parents=True)
    (skill_dir / "metadata.json").write_text("{}", encoding="utf-8")

    assert manager.skill_exists("technical_skills/programming/languages/python") is True


def test_skill_exists_rejects_traversal_paths(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    assert manager.skill_exists("../etc/passwd") is False
    assert manager.skill_exists("/absolute/path") is False


def test_register_skill_rejects_traversal_paths(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    success = manager.register_skill(
        path="../evil",
        metadata={},
        content="# Evil\n",
        evolution={},
        overwrite=False,
    )

    assert success is False


def test_dependency_validation(temp_taxonomy: Path) -> None:
    manager = TaxonomyManager(temp_taxonomy)

    valid, missing = manager.validate_dependencies(["_core/reasoning"])
    assert valid is True
    assert missing == []

    valid, missing = manager.validate_dependencies(["nonexistent/skill"])
    assert valid is False
    assert missing == ["nonexistent/skill"]
