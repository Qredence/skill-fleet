"""Prompt UI abstraction for Typer CLI commands.

`skill-fleet chat` needs a better UX than typed `Prompt.ask(...)` choices.
This module provides:
- A small PromptUI protocol
- A prompt-toolkit implementation for arrow-key selection
- A Rich fallback for non-interactive terminals

The abstraction is intentionally minimal so it can be unit tested without
requiring a real TTY.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from rich.prompt import Prompt as RichPrompt

_T = TypeVar("_T")

logger = logging.getLogger(__name__)

OTHER_OPTION_ID = "__other__"


class PromptUI(Protocol):
    """Minimal interface for interactive prompts."""

    async def ask_text(self, prompt: str, *, default: str = "") -> str:
        """Ask for free-form text."""

    async def choose_one(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_id: str | None = None,
    ) -> str:
        """Select exactly one choice by arrow keys or typed fallback."""

    async def choose_many(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_ids: list[str] | None = None,
    ) -> list[str]:
        """Select multiple choices by arrow keys or typed fallback."""


@dataclass(slots=True)
class PromptToolkitUI:
    """Prompt UI backed by prompt-toolkit dialogs."""

    async def ask_text(self, prompt: str, *, default: str = "") -> str:
        """Ask for free-form text using prompt-toolkit when available."""
        try:
            from prompt_toolkit.shortcuts import prompt
        except ImportError:
            logger.debug("prompt_toolkit not available, using Rich fallback")
            # RichPrompt.ask accepts keyword arguments
            def _rich_ask_wrapper(p: str, d: str) -> Any:
                return RichPrompt.ask(p, default=d)
            result = await asyncio.to_thread(_rich_ask_wrapper, str(prompt), default)
            return str(result) if result is not None else default
        except Exception as e:
            logger.warning(f"prompt_toolkit import failed unexpectedly: {e}")
            def _rich_ask_wrapper(p: str, d: str) -> Any:
                return RichPrompt.ask(p, default=d)
            result = await asyncio.to_thread(_rich_ask_wrapper, str(prompt), default)
            return str(result) if result is not None else default

        # prompt_toolkit's prompt function is not async, so we run it in a thread
        def _prompt_wrapper(p: str, d: str) -> Any:
            return prompt(p, default=d)
        result = await asyncio.to_thread(_prompt_wrapper, f"{prompt}: ", default)
        return str(result) if result is not None else default

    async def choose_one(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_id: str | None = None,
    ) -> str:
        """Choose a single option using prompt-toolkit `choice()`.

        This follows the official prompt-toolkit documentation:
        https://python-prompt-toolkit.readthedocs.io/en/3.0.52/pages/asking_for_a_choice.html

        Note: `choice()` is synchronous, so we run it in a worker thread to
        keep the surrounding asyncio-based CLI responsive.
        """
        if not choices:
            return ""

        # First, prefer the (older) `choice()` helper if available; tests and
        # some prompt-toolkit versions monkeypatch or expose it. If it's not
        # present, fall back to a radiolist_dialog which provides a similar
        # single-choice UX. Any import/runtime error falls back to Rich.
        default = default_id or (choices[0][0] if choices else "")

        pt_choice: Callable[..., _T] | None = None
        try:
            from prompt_toolkit.shortcuts import choice as _pt_choice_impl
            pt_choice = _pt_choice_impl
        except ImportError:
            logger.debug("choice() helper not available, trying radiolist_dialog")
            pt_choice = None
        except Exception as e:
            logger.warning(f"choice() import failed unexpectedly: {e}")
            pt_choice = None

        if pt_choice is not None:
            try:
                # Create a wrapper function that matches asyncio.to_thread's signature
                def _choice_wrapper(msg: str, opts: list[tuple[str, str]], def_val: str) -> Any:
                    return pt_choice(message=msg, options=opts, default=def_val)

                selected = await asyncio.to_thread(
                    _choice_wrapper,
                    prompt,
                    choices,
                    default,
                )
            except (ImportError, AttributeError, RuntimeError) as e:
                logger.debug(f"choice() failed ({type(e).__name__}), using Rich fallback: {e}")
                return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)
            except Exception as e:
                logger.warning(f"choice() failed unexpectedly: {e}")
                return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)

            return str(selected) if selected is not None else default

        # choice() not available — try radiolist_dialog next
        try:
            from prompt_toolkit.shortcuts import radiolist_dialog
        except ImportError:
            logger.debug("radiolist_dialog not available, using Rich fallback")
            return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)
        except Exception as e:
            logger.warning(f"radiolist_dialog import failed unexpectedly: {e}")
            return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)

        dialog = radiolist_dialog(title="", text=prompt, values=choices)
        try:
            if hasattr(dialog, "run_async"):
                selected = await dialog.run_async()
            else:
                selected = await asyncio.to_thread(dialog.run)
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug(f"radiolist_dialog failed ({type(e).__name__}), using Rich fallback: {e}")
            return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)
        except Exception as e:
            logger.warning(f"radiolist_dialog failed unexpectedly: {e}")
            return await RichFallbackUI().choose_one(prompt, choices, default_id=default_id)

        return str(selected) if selected is not None else default

    async def choose_many(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_ids: list[str] | None = None,
    ) -> list[str]:
        """Choose multiple options via arrow keys (checkbox dialog)."""
        if not choices:
            return []

        try:
            from prompt_toolkit.shortcuts import checkboxlist_dialog
        except ImportError:
            logger.debug("checkboxlist_dialog not available, using Rich fallback")
            return await RichFallbackUI().choose_many(prompt, choices, default_ids=default_ids)
        except Exception as e:
            logger.warning(f"checkboxlist_dialog import failed unexpectedly: {e}")
            return await RichFallbackUI().choose_many(prompt, choices, default_ids=default_ids)

        dialog = checkboxlist_dialog(title="", text=prompt, values=choices)
        selected = None
        try:
            if hasattr(dialog, "run_async"):
                selected = await dialog.run_async()
            else:
                selected = None
        except (ImportError, AttributeError, RuntimeError) as e:
            logger.debug(
                f"checkboxlist_dialog failed ({type(e).__name__}), using Rich fallback: {e}"
            )
            return await RichFallbackUI().choose_many(prompt, choices, default_ids=default_ids)
        except Exception as e:
            logger.warning(f"checkboxlist_dialog failed unexpectedly: {e}")
            return await RichFallbackUI().choose_many(prompt, choices, default_ids=default_ids)

        if selected is None:
            # Cancel => fall back to defaults, otherwise empty.
            if default_ids:
                return list(default_ids)
            return []
        return [str(x) for x in selected]


@dataclass(slots=True)
class RichFallbackUI:
    """Prompt UI backed by Rich typed prompts."""

    async def ask_text(self, prompt: str, *, default: str = "") -> str:
        """Ask for free-form text using Rich prompt."""
        def _rich_ask_wrapper(p: str, d: str) -> Any:
            return RichPrompt.ask(p, default=d)
        result = await asyncio.to_thread(_rich_ask_wrapper, prompt, default)
        return str(result) if result is not None else default

    async def choose_one(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_id: str | None = None,
    ) -> str:
        """Choose a single option by typing an id (Rich fallback)."""
        if not choices:
            return ""
        ids = [c[0] for c in choices]
        default = default_id or ids[0]
        # RichPrompt.ask accepts keyword arguments
        def _rich_choose_wrapper(p: str, c: list[str], d: str, sc: bool) -> Any:
            return RichPrompt.ask(p, choices=c, default=d, show_choices=sc)
        result = await asyncio.to_thread(
            _rich_choose_wrapper,
            prompt,
            ids,
            default,
            True,
        )
        return str(result) if result is not None else default

    async def choose_many(
        self,
        prompt: str,
        choices: list[tuple[str, str]],
        *,
        default_ids: list[str] | None = None,
    ) -> list[str]:
        """Choose multiple options by entering comma-separated ids (Rich fallback)."""
        if not choices:
            return []

        ids = [c[0] for c in choices]
        default_str = ",".join(default_ids) if default_ids else ""
        # RichPrompt.ask accepts keyword arguments
        def _rich_ask_wrapper(p: str, d: str) -> Any:
            return RichPrompt.ask(p, default=d)
        raw = await asyncio.to_thread(
            _rich_ask_wrapper,
            f"{prompt} (comma-separated, options: {', '.join(ids)})",
            default_str,
        )
        selected = [part.strip() for part in raw.split(",") if part.strip()]
        # Keep only known ids to avoid surprising downstream behavior.
        valid_selections = [s for s in selected if s in ids]
        if valid_selections != selected:
            unknown = set(selected) - set(valid_selections)
            if unknown:
                logger.debug(f"Filtered unknown selections: {unknown}")
        return valid_selections


def get_default_ui(*, force_plain_text: bool = False) -> PromptUI:
    """Return the best available UI implementation for this environment."""

    env_force_plain = os.environ.get("SKILL_FLEET_FORCE_PLAIN_TEXT", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if force_plain_text or env_force_plain:
        return RichFallbackUI()

    # Non-interactive environments (CI, pipes) should never attempt PT dialogs.
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return RichFallbackUI()

    try:
        import prompt_toolkit  # noqa: F401

        return PromptToolkitUI()
    except ImportError:
        logger.debug("prompt_toolkit not available, using Rich fallback")
        return RichFallbackUI()
    except Exception as e:
        logger.warning(f"prompt_toolkit import failed unexpectedly: {e}")
        return RichFallbackUI()


async def choose_one_with_other(
    ui: PromptUI,
    prompt: str,
    choices: list[tuple[str, str]],
    *,
    default_id: str | None = None,
    other_label: str = "Other (type my own)",
    other_prompt: str = "Type your answer",
) -> tuple[list[str], str]:
    """Choose one option or provide free text.

    Returns:
        (selected_ids, free_text)
    """

    extended = list(choices) + [(OTHER_OPTION_ID, other_label)]
    selected = await ui.choose_one(prompt, extended, default_id=default_id)
    if selected == OTHER_OPTION_ID:
        return ([], await ui.ask_text(other_prompt, default=""))
    return ([selected] if selected else [], "")


async def choose_many_with_other(
    ui: PromptUI,
    prompt: str,
    choices: list[tuple[str, str]],
    *,
    default_ids: list[str] | None = None,
    other_label: str = "Other (type my own)",
    other_prompt: str = "Type your answer",
) -> tuple[list[str], str]:
    """Choose many options and optionally provide free text.

    Returns:
        (selected_ids, free_text)
    """

    extended = list(choices) + [(OTHER_OPTION_ID, other_label)]
    selected = await ui.choose_many(prompt, extended, default_ids=default_ids)
    free_text = ""
    if OTHER_OPTION_ID in selected:
        selected = [s for s in selected if s != OTHER_OPTION_ID]
        free_text = await ui.ask_text(other_prompt, default="")
    return (selected, free_text)
