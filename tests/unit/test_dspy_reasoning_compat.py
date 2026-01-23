import dspy

from skill_fleet.common.dspy_compat import coerce_reasoning_text


def test_coerce_reasoning_text_handles_none() -> None:
    assert coerce_reasoning_text(None) == ""


def test_coerce_reasoning_text_handles_str() -> None:
    assert coerce_reasoning_text(" hi ") == "hi"


def test_coerce_reasoning_text_handles_dspy_reasoning() -> None:
    reasoning = dspy.Reasoning(content=" hello ")
    assert coerce_reasoning_text(reasoning) == "hello"
