from skill_fleet.core.modules.generation.content import GenerateSkillContentModule


def test_create_skill_understanding_normalizes_dependency_dict():
    module = GenerateSkillContentModule()

    understanding = {
        "domain": "technical",
        "category": "general",
        "target_level": "intermediate",
        "topics": ["grep", "ripgrep"],
        "dependencies": {
            "prerequisite_skills": ["technical/programming/shell-basics", "technical/tools/rg"],
            "complementary_skills": ["technical/tools/fzf"],
        },
    }

    parsed = module._create_skill_understanding(understanding)
    assert parsed.dependencies == ["technical/programming/shell-basics", "technical/tools/rg"]
