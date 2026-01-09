import pytest


def test_get_lm_rejects_unapproved_models() -> None:
    pytest.importorskip("dspy")
    from agentic_fleet.agentic_skills_system.workflow.optimize import get_lm

    with pytest.raises(ValueError):
        get_lm("not-a-real-model")


def test_get_lm_constructs_dspy_lm_with_approved_model(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("dspy")
    from agentic_fleet.agentic_skills_system.workflow import optimize

    class DummyLM:
        def __init__(self, model: str, temperature: float = 0.0, **kwargs):
            self.model = model
            self.temperature = temperature
            self.kwargs = kwargs

    monkeypatch.setattr(optimize.dspy, "LM", DummyLM)

    lm = optimize.get_lm("gemini-3-flash-preview", temperature=0.12, max_tokens=123)
    assert isinstance(lm, DummyLM)
    assert lm.model == "gemini/gemini-3-flash-preview"
    assert lm.temperature == 0.12
    assert lm.kwargs["max_tokens"] == 123
