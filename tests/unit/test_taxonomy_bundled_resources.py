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
    return skills_root


def test_bundled_resources_registration(temp_taxonomy: Path) -> None:
    """Verify that bundled resources (scripts, assets, resources) are saved correctly."""
    manager = TaxonomyManager(temp_taxonomy)

    skill_path = "test/bundled_resource_skill"
    metadata = {
        "version": "1.0.0",
        "type": "technical",
        "description": "A test skill with bundled resources.",
    }
    content = "# Test Skill\n\nThis is a test."
    evolution = {"history": []}

    extra_files = {
        "scripts": {
            "setup.py": "print('setup')",
            "utils/helper.py": "def help(): pass",
        },
        "assets": {
            "logo.png": "fake_png_content",  # Text content simulating binary/text asset
            "data/config.json": '{"key": "value"}',
        },
        "resources": {
            "dataset.csv": "col1,col2\n1,2",
        },
    }

    success = manager.register_skill(
        path=skill_path,
        metadata=metadata,
        content=content,
        evolution=evolution,
        extra_files=extra_files,
    )

    assert success is True

    # Verify directory structure and content
    skill_dir = temp_taxonomy / skill_path

    # Check scripts
    assert (skill_dir / "scripts" / "setup.py").exists()
    assert (skill_dir / "scripts" / "setup.py").read_text() == "print('setup')"

    assert (skill_dir / "scripts" / "utils" / "helper.py").exists()
    assert (skill_dir / "scripts" / "utils" / "helper.py").read_text() == "def help(): pass"

    # Check assets
    assert (skill_dir / "assets" / "logo.png").exists()
    assert (skill_dir / "assets" / "logo.png").read_text() == "fake_png_content"

    assert (skill_dir / "assets" / "data" / "config.json").exists()
    assert (skill_dir / "assets" / "data" / "config.json").read_text() == '{"key": "value"}'

    # Check resources
    assert (skill_dir / "resources" / "dataset.csv").exists()
    assert (skill_dir / "resources" / "dataset.csv").read_text() == "col1,col2\n1,2"


def test_bundled_resources_binary_assets(temp_taxonomy: Path) -> None:
    """Verify that binary assets are saved correctly."""
    manager = TaxonomyManager(temp_taxonomy)

    skill_path = "test/binary_asset_skill"
    metadata = {"description": "Test binary assets"}
    content = "# Binary Test"
    evolution = {}

    binary_content = b"\x89PNG\r\n\x1a\n"

    extra_files = {"assets": {"image.png": binary_content}}

    success = manager.register_skill(
        path=skill_path,
        metadata=metadata,
        content=content,
        evolution=evolution,
        extra_files=extra_files,
    )

    assert success is True

    skill_dir = temp_taxonomy / skill_path
    assert (skill_dir / "assets" / "image.png").read_bytes() == binary_content
