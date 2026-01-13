"""Tests for user onboarding system."""

import json
from unittest.mock import MagicMock, patch

import pytest

from skill_fleet.core.creator import TaxonomySkillCreator
from skill_fleet.onboarding.bootstrap import SkillBootstrapper
from skill_fleet.taxonomy.manager import TaxonomyManager


@pytest.fixture
def mock_taxonomy():
    taxonomy = MagicMock(spec=TaxonomyManager)
    taxonomy.skill_exists.return_value = False
    return taxonomy


@pytest.fixture
def mock_creator():
    return MagicMock(spec=TaxonomySkillCreator)


@pytest.fixture
def profiles_path(tmp_path):
    path = tmp_path / "bootstrap_profiles.json"
    profiles = {
        "bootstrap_profiles": {
            "web_developer": {"required": ["skill1"], "on_demand": ["skill2"]},
            "general_purpose": {"required": ["base_skill"], "on_demand": []},
        },
        "tech_stack_mapping": {"Python": ["python_skill"]},
        "task_mapping": {"Debugging": ["debug_skill"]},
    }
    with open(path, "w") as f:
        json.dump(profiles, f)
    return path


def test_analyze_responses(profiles_path):
    bootstrapper = SkillBootstrapper(MagicMock(), MagicMock(), profiles_path)
    responses = {
        "role": "backend_developer",
        "tech_stack": ["Python", "Docker"],
        "common_tasks": ["Building APIs"],
        "experience_level": "senior",
    }
    profile = bootstrapper.analyze_responses(responses)
    assert profile["primaryRole"] == "backend_developer"
    assert "Python" in profile["techStack"]
    assert profile["experience_level"] == "senior"


def test_generate_skill_plan(mock_taxonomy, mock_creator, profiles_path):
    bootstrapper = SkillBootstrapper(mock_taxonomy, mock_creator, profiles_path)
    profile = {
        "primaryRole": "web_developer",
        "techStack": ["Python"],
        "commonTasks": ["Debugging"],
        "experience_level": "mid-level",
    }
    plan = bootstrapper.generate_skill_plan(profile)

    assert "skill1" in plan["required"]
    assert "python_skill" in plan["required"]
    assert "debug_skill" in plan["required"]
    assert "skill2" in plan["onDemand"]


@pytest.mark.anyio
async def test_onboard_user(mock_taxonomy, mock_creator, profiles_path):
    bootstrapper = SkillBootstrapper(mock_taxonomy, mock_creator, profiles_path)

    mock_creator.forward.return_value = {
        "status": "approved",
        "skill_id": "generated.skill",
        "path": "path/to/skill",
    }

    responses = {"role": "web_developer", "tech_stack": [], "common_tasks": []}

    # We mock _save_user_profile and register_on_demand_skills to avoid I/O or further logic
    with (
        patch.object(bootstrapper, "_save_user_profile"),
        patch.object(bootstrapper, "register_on_demand_skills"),
    ):
        profile = await bootstrapper.onboard_user("user123", responses)

    assert profile["user_id"] == "user123"
    assert "generated.skill" in profile["mounted_skills"]
    assert mock_creator.forward.called
