from types import SimpleNamespace

import dspy

from skill_fleet.core.dspy.modules.conversation.understanding import GenerateQuestionModule


def test_generate_question_module_coerces_reasoning() -> None:
    module = GenerateQuestionModule()

    class StubGenerate:
        def __call__(self, **_: object) -> SimpleNamespace:
            return SimpleNamespace(
                question="What do you need?",
                question_options=["A"],
                reasoning=dspy.Reasoning(content=" because "),
            )

    module.generate = StubGenerate()
    result = module.forward(task_description="Test")

    assert result.reasoning == "because"
