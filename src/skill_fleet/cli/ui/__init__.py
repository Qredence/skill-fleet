"""CLI UI helpers.

This package contains small, testable UI abstractions used by Typer commands.
The primary goal is to support richer terminal UX (arrow-key selection) while
retaining a safe fallback for non-interactive environments.
"""

from .prompts import (
    OTHER_OPTION_ID,
    PromptToolkitUI,
    PromptUI,
    RichFallbackUI,
    choose_many_with_other,
    choose_one_with_other,
    get_default_ui,
)

__all__ = [
    "OTHER_OPTION_ID",
    "PromptUI",
    "PromptToolkitUI",
    "RichFallbackUI",
    "choose_many_with_other",
    "choose_one_with_other",
    "get_default_ui",
]
