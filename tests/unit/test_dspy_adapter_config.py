"""Tests for DSPy adapter configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import dspy
import pytest

from skill_fleet.llm.dspy_config import configure_dspy


@pytest.fixture(autouse=True)
def reset_dspy_adapter() -> Iterator[None]:
    original_adapter = dspy.settings.adapter
    try:
        dspy.settings.configure(adapter=None)
        yield
    finally:
        dspy.settings.configure(adapter=original_adapter)


def test_configure_dspy_sets_adapter_from_config(monkeypatch: pytest.MonkeyPatch) -> None:
    config = {"dspy": {"adapter": "json"}}

    monkeypatch.delenv("DSPY_ADAPTER", raising=False)

    lm = dspy.LM("test", model_type="chat")

    with (
        patch("skill_fleet.llm.dspy_config.load_fleet_config", return_value=config),
        patch(
            "skill_fleet.llm.dspy_config.build_lm_for_task",
            return_value=lm,
        ),
    ):
        configure_dspy(config_path=Path("config.yaml"))

    assert isinstance(dspy.settings.adapter, dspy.JSONAdapter)


def test_configure_dspy_sets_chat_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    config = {"dspy": {"adapter": "chat"}}

    monkeypatch.delenv("DSPY_ADAPTER", raising=False)

    lm = dspy.LM("test", model_type="chat")

    with (
        patch("skill_fleet.llm.dspy_config.load_fleet_config", return_value=config),
        patch(
            "skill_fleet.llm.dspy_config.build_lm_for_task",
            return_value=lm,
        ),
    ):
        configure_dspy(config_path=Path("config.yaml"))

    assert isinstance(dspy.settings.adapter, dspy.ChatAdapter)


def test_configure_dspy_sets_two_step_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    config = {"dspy": {"adapter": "two_step"}}

    monkeypatch.delenv("DSPY_ADAPTER", raising=False)

    lm = dspy.LM("test", model_type="chat")

    with (
        patch("skill_fleet.llm.dspy_config.load_fleet_config", return_value=config),
        patch(
            "skill_fleet.llm.dspy_config.build_lm_for_task",
            return_value=lm,
        ),
    ):
        configure_dspy(config_path=Path("config.yaml"))

    assert isinstance(dspy.settings.adapter, dspy.TwoStepAdapter)


def test_configure_dspy_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    config = {"dspy": {"adapter": "chat"}}

    monkeypatch.setenv("DSPY_ADAPTER", "two_step")

    lm = dspy.LM("test", model_type="chat")

    with (
        patch("skill_fleet.llm.dspy_config.load_fleet_config", return_value=config),
        patch(
            "skill_fleet.llm.dspy_config.build_lm_for_task",
            return_value=lm,
        ),
    ):
        configure_dspy(config_path=Path("config.yaml"))

    assert isinstance(dspy.settings.adapter, dspy.TwoStepAdapter)
