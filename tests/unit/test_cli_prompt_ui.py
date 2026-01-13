from typing import cast

import pytest

from skill_fleet.cli.ui.prompts import (
    OTHER_OPTION_ID,
    PromptToolkitUI,
    PromptUI,
    RichFallbackUI,
    choose_many_with_other,
    choose_one_with_other,
    get_default_ui,
)


class TestPromptToolkitUI:
    @pytest.mark.asyncio
    async def test_choose_one_returns_selected_id(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            "prompt_toolkit.shortcuts.choice",
            lambda *_, **__: "b",
        )

        ui = PromptToolkitUI()

        # Act
        selected = await ui.choose_one("Pick one", [("a", "A"), ("b", "B")], default_id="a")

        # Assert
        assert selected == "b"

    @pytest.mark.asyncio
    async def test_choose_one_cancel_falls_back_to_default(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            "prompt_toolkit.shortcuts.choice",
            lambda *_, **__: None,
        )

        ui = PromptToolkitUI()

        # Act
        selected = await ui.choose_one("Pick one", [("a", "A"), ("b", "B")], default_id="b")

        # Assert
        assert selected == "b"

    @pytest.mark.asyncio
    async def test_choose_many_returns_selected_ids(self, monkeypatch):
        # Arrange
        class _Dialog:
            async def run_async(self):
                return ["a", "c"]

        def _check(**_kwargs):
            return _Dialog()

        monkeypatch.setattr("prompt_toolkit.shortcuts.checkboxlist_dialog", _check)

        ui = PromptToolkitUI()

        # Act
        selected = await ui.choose_many("Pick many", [("a", "A"), ("b", "B"), ("c", "C")])

        # Assert
        assert selected == ["a", "c"]

    @pytest.mark.asyncio
    async def test_choose_one_radiolist_dialog_returns_selected_id(self, monkeypatch):
        # Arrange: simulate radiolist_dialog returning a dialog with run_async()
        class _Dialog:
            async def run_async(self):
                return "b"

        def _radiolist(**_kwargs):
            return _Dialog()

        # Ensure the `choice` helper is not used so the radiolist path is taken.
        monkeypatch.setattr("prompt_toolkit.shortcuts.choice", None, raising=False)
        monkeypatch.setattr("prompt_toolkit.shortcuts.radiolist_dialog", _radiolist)

        ui = PromptToolkitUI()

        # Act
        selected = await ui.choose_one("Pick one", [("a", "A"), ("b", "B")], default_id="a")

        # Assert
        assert selected == "b"


class TestRichFallbackUI:
    @pytest.mark.asyncio
    async def test_choose_many_parses_csv_and_filters_unknown_ids(self, monkeypatch):
        # Arrange
        monkeypatch.setattr(
            "skill_fleet.cli.ui.prompts.RichPrompt.ask",
            lambda *_args, **_kwargs: "a, x, c",
        )
        ui = RichFallbackUI()

        # Act
        selected = await ui.choose_many("Pick many", [("a", "A"), ("b", "B"), ("c", "C")])

        # Assert
        assert selected == ["a", "c"]


class TestChooseWithOther:
    @pytest.mark.asyncio
    async def test_choose_one_with_other_triggers_free_text(self):
        # Arrange
        class _FakeUI:
            async def ask_text(self, _prompt: str, *, default: str = "") -> str:
                return "my free text"

            async def choose_one(self, _prompt: str, _choices, *, default_id=None):
                return OTHER_OPTION_ID

            async def choose_many(self, _prompt: str, _choices, *, default_ids=None):
                raise AssertionError("not used")

        # Act
        selected, free_text = await choose_one_with_other(
            cast(PromptUI, _FakeUI()),
            "Pick one",
            [("a", "A"), ("b", "B")],
        )

        # Assert
        assert selected == []
        assert free_text == "my free text"

    @pytest.mark.asyncio
    async def test_choose_many_with_other_includes_ids_and_free_text(self):
        # Arrange
        class _FakeUI:
            async def ask_text(self, _prompt: str, *, default: str = "") -> str:
                return "extra"

            async def choose_one(self, _prompt: str, _choices, *, default_id=None):
                raise AssertionError("not used")

            async def choose_many(self, _prompt: str, _choices, *, default_ids=None):
                return ["a", OTHER_OPTION_ID]

        # Act
        selected, free_text = await choose_many_with_other(
            cast(PromptUI, _FakeUI()),
            "Pick many",
            [("a", "A"), ("b", "B")],
        )

        # Assert
        assert selected == ["a"]
        assert free_text == "extra"


def test_get_default_ui_force_plain_text():
    ui = get_default_ui(force_plain_text=True)
    assert isinstance(ui, RichFallbackUI)
