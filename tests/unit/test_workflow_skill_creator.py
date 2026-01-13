import contextlib

import pytest

from skill_fleet.core import creator as skill_creator_module


class _FakeTaxonomy:
    def __init__(self, skills_root):
        self.skills_root = skills_root
        self._exists = False
        self._has_cycle = False
        self._register_ok = True
        self.track_calls = []
        self.register_calls = []

    def get_mounted_skills(self, user_id: str):
        return []

    def get_relevant_branches(self, task_description: str):
        return {}

    def get_parent_skills(self, taxonomy_path: str):
        return []

    def skill_exists(self, taxonomy_path: str) -> bool:
        return self._exists

    def validate_dependencies(self, dep_ids: list[str]):
        return True, []

    def detect_circular_dependencies(self, skill_id: str, dep_ids: list[str]):
        if self._has_cycle:
            return True, [skill_id, *dep_ids]
        return False, []

    def register_skill(self, **kwargs):
        self.register_calls.append(kwargs)
        return self._register_ok

    def track_usage(self, **kwargs):
        self.track_calls.append(kwargs)


def _base_creation_result(passed: bool = True):
    return {
        "understanding": {
            "taxonomy_path": "general/testing",
            "parent_skills": [],
        },
        "plan": {
            "dependencies": [],
            "skill_metadata": {"skill_id": "general/testing", "version": "1.0.0"},
            "composition_strategy": "",
            "resource_requirements": {},
        },
        "skeleton": {"skill_skeleton": {}},
        "content": {
            "skill_content": "# Title\n\n## Overview\n\n## Capabilities\n\n## Dependencies\n\n## Usage Examples\n",
            "capability_implementations": [],
            "usage_examples": [],
            "best_practices": [],
            "integration_guide": "",
        },
        "package": {
            "validation_report": {
                "passed": passed,
                "status": "passed" if passed else "failed",
                "errors": ["e"] if not passed else [],
            },
            "packaging_manifest": {},
            "quality_score": 0.9,
        },
    }


def test_create_skill_returns_exists(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("dspy")
    monkeypatch.setattr(
        skill_creator_module.dspy, "context", lambda **kwargs: contextlib.nullcontext()
    )

    taxonomy = _FakeTaxonomy(tmp_path)
    taxonomy._exists = True

    creator = skill_creator_module.TaxonomySkillCreator(
        taxonomy_manager=taxonomy, feedback_handler=None, validator=object(), verbose=False
    )
    creator.creation_program = lambda **kwargs: _base_creation_result(passed=True)

    result = creator.create_skill(task_description="x", user_context={"user_id": "u"})
    assert result["status"] == "exists"


def test_create_skill_returns_validation_failed(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("dspy")
    monkeypatch.setattr(
        skill_creator_module.dspy, "context", lambda **kwargs: contextlib.nullcontext()
    )

    taxonomy = _FakeTaxonomy(tmp_path)
    creator = skill_creator_module.TaxonomySkillCreator(
        taxonomy_manager=taxonomy, feedback_handler=None, validator=object(), verbose=False
    )
    creator.creation_program = lambda **kwargs: _base_creation_result(passed=False)

    result = creator.create_skill(task_description="x", user_context={"user_id": "u"})
    assert result["status"] == "validation_failed"
    assert result["errors"]


def test_create_skill_rejects_circular_dependency(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("dspy")
    monkeypatch.setattr(
        skill_creator_module.dspy, "context", lambda **kwargs: contextlib.nullcontext()
    )

    taxonomy = _FakeTaxonomy(tmp_path)
    taxonomy._has_cycle = True

    creator = skill_creator_module.TaxonomySkillCreator(
        taxonomy_manager=taxonomy, feedback_handler=None, validator=object(), verbose=False
    )
    creation = _base_creation_result(passed=True)
    creation["plan"]["dependencies"] = ["_core/reasoning"]
    creation["plan"]["skill_metadata"]["skill_id"] = "general/testing"
    creator.creation_program = lambda **kwargs: creation

    result = creator.create_skill(task_description="x", user_context={"user_id": "u"})
    assert result["status"] == "error"
    assert "Invalid dependencies" in result["message"]


def test_create_skill_approved_tracks_usage_and_updates_stats(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("dspy")
    monkeypatch.setattr(
        skill_creator_module.dspy, "context", lambda **kwargs: contextlib.nullcontext()
    )

    taxonomy = _FakeTaxonomy(tmp_path)
    creator = skill_creator_module.TaxonomySkillCreator(
        taxonomy_manager=taxonomy, feedback_handler=None, validator=object(), verbose=False
    )

    creator.creation_program = lambda **kwargs: _base_creation_result(passed=True)
    creator.iterate_module = lambda **kwargs: {
        "approval_status": "approved",
        "revision_plan": {},
        "evolution_metadata": {"status": "approved"},
        "next_steps": "",
    }

    result = creator.create_skill(task_description="x", user_context={"user_id": "u"})
    assert result["status"] == "approved"
    assert creator.stats["successful"] == 1
    assert taxonomy.track_calls and taxonomy.track_calls[0]["success"] is True
    assert taxonomy.register_calls


def test_create_skill_max_iterations_when_needs_revision_repeats(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("dspy")
    monkeypatch.setattr(
        skill_creator_module.dspy, "context", lambda **kwargs: contextlib.nullcontext()
    )

    taxonomy = _FakeTaxonomy(tmp_path)
    creator = skill_creator_module.TaxonomySkillCreator(
        taxonomy_manager=taxonomy, feedback_handler=None, validator=object(), verbose=False
    )

    creator.creation_program = lambda **kwargs: _base_creation_result(passed=True)

    creator.iterate_module = lambda **kwargs: {
        "approval_status": "needs_revision",
        "revision_plan": {"changes": ["x"]},
        "evolution_metadata": {"status": "needs_revision"},
        "next_steps": "",
    }
    creator.revision_program = lambda **kwargs: {
        "content": _base_creation_result(passed=True)["content"],
        "package": _base_creation_result(passed=True)["package"],
    }

    result = creator.create_skill(
        task_description="x", user_context={"user_id": "u"}, max_iterations=2
    )
    assert result["status"] == "max_iterations"
