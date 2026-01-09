import pytest


def test_get_lm_rejects_unapproved_models() -> None:
    pytest.importorskip("dspy")
    from agentic_fleet.agentic_skills_system.workflow.optimize import get_lm

    with pytest.raises(ValueError):
        get_lm("unapproved-test-model")


def test_get_lm_constructs_dspy_lm_with_approved_model(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("dspy")
    from agentic_fleet.agentic_skills_system.workflow import optimize

    class DummyLM:
        def __init__(self, model: str, temperature: float = 0.0, **kwargs):
            self.model = model
            self.temperature = temperature
            self.kwargs = kwargs

    monkeypatch.setattr(optimize.dspy, "LM", DummyLM)

    # Arbitrary but fixed values to verify that get_lm forwards parameters correctly.
    test_temperature = 0.12
    test_max_tokens = 123

    language_model = optimize.get_lm(
        "gemini-3-flash-preview",
        temperature=test_temperature,
        max_tokens=test_max_tokens,
    )
    assert isinstance(language_model, DummyLM)
    assert language_model.model == "gemini/gemini-3-flash-preview"
    assert language_model.temperature == test_temperature
    assert language_model.kwargs["max_tokens"] == test_max_tokens
