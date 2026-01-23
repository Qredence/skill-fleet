import dspy

from skill_fleet.core.dspy.signatures.conversational_interface import DeepUnderstandingSignature


def test_reasoning_field_type_is_dspy_reasoning() -> None:
    assert DeepUnderstandingSignature.model_fields["reasoning"].annotation is dspy.Reasoning
