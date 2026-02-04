from __future__ import annotations

import pytest

from skill_fleet.core.models import SkillMetadata, ValidationReport


def test_skillmetadata_dictlike_access():
    meta = SkillMetadata(
        skill_id="testing/test-skill",
        name="test-skill",
        description="A test skill",
        type="technical",
        weight="medium",
    )

    assert meta.get("name") == "test-skill"
    assert meta.get("missing", "default") == "default"
    assert meta["name"] == "test-skill"
    with pytest.raises(AttributeError):
        _ = meta["missing"]


def test_validationreport_dictlike_access():
    report = ValidationReport(passed=True)

    assert report.get("passed") is True
    assert report.get("missing", 123) == 123
    assert report["passed"] is True
    with pytest.raises(AttributeError):
        _ = report["missing"]
