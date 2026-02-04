from skill_fleet.core.workflows.models import (
    DependencyOutput,
    Phase1UnderstandingOutput,
    PlanOutput,
)


def test_phase1_to_generation_input_emits_dependency_list():
    phase1 = Phase1UnderstandingOutput(
        status="completed",
        dependencies=DependencyOutput(
            prerequisite_skills=["technical/programming/shell-basics"],
            complementary_skills=["technical/tools/fzf"],
            dependency_rationale="Need shell basics for rg usage",
        ),
        plan=PlanOutput(
            skill_name="grep-skill",
            skill_description="Use when searching text",
            taxonomy_path="technical/tools/grep",
            content_outline=[],
        ),
    )

    payload = phase1.to_generation_input()
    assert payload["understanding"]["dependencies"] == ["technical/programming/shell-basics"]
    assert payload["understanding"]["dependency_analysis"]["prerequisite_skills"] == [
        "technical/programming/shell-basics"
    ]
