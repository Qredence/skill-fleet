"""HITL (Human-in-the-Loop) schema models.

This module provides structured models for HITL interactions, ensuring
the API returns consistent, typed data that CLI clients can consume
without additional parsing or normalization.

Following the API-first principle: data transformation happens server-side,
CLI is a thin client that only renders pre-structured data.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
    """A single option for a multiple-choice question."""

    id: str = Field(..., description="Unique identifier for the option")
    label: str = Field(..., description="Display label for the option")
    description: str | None = Field(default=None, description="Optional description")


class StructuredQuestion(BaseModel):
    """A structured question for HITL clarification.

    This model ensures questions are always in a consistent format,
    regardless of how they were generated (string, dict, or list).
    """

    text: str = Field(..., description="The question text")
    options: list[QuestionOption] | None = Field(
        default=None, description="Optional list of choices for multiple-choice questions"
    )
    allows_multiple: bool = Field(
        default=False, description="Whether multiple options can be selected"
    )
    rationale: str | None = Field(default=None, description="Why this question is being asked")


def normalize_questions(questions: Any) -> list[StructuredQuestion]:
    """Normalize raw questions into a list of StructuredQuestion objects.

    This function handles the various formats that questions may arrive in:
    - None -> empty list
    - Single string -> split numbered lists, create StructuredQuestion for each
    - List of strings -> normalize each string
    - List of dicts -> convert to StructuredQuestion
    - Already StructuredQuestion -> pass through

    This logic was previously in the CLI (runner.py::_normalize_questions).
    Moving it server-side ensures consistent API responses.

    Args:
        questions: Raw questions in any supported format

    Returns:
        List of StructuredQuestion objects
    """
    if questions is None:
        return []

    if isinstance(questions, str):
        return _normalize_string_questions(questions)

    if isinstance(questions, list):
        result: list[StructuredQuestion] = []
        for q in questions:
            if isinstance(q, StructuredQuestion):
                result.append(q)
            elif isinstance(q, str):
                result.extend(_normalize_string_questions(q))
            elif isinstance(q, dict):
                result.append(_dict_to_structured_question(q))
            else:
                # Unknown type, convert to string
                result.append(StructuredQuestion(text=str(q)))
        return result

    # Single unknown object
    return [StructuredQuestion(text=str(questions))]


def _normalize_string_questions(text: str) -> list[StructuredQuestion]:
    """Split a string that may contain numbered questions into individual questions.

    Handles formats like:
    - "1. First question\n2. Second question"
    - "Single question without numbering"
    """
    text = text.strip()
    if not text:
        return []

    # Check if it looks like a numbered list ("1. ...\n2. ...")
    matches = list(re.finditer(r"(?m)^\s*\d+\.\s+", text))

    if len(matches) <= 1:
        # Single question or no numbering
        return [StructuredQuestion(text=text)]

    # Split numbered list into individual questions
    parts: list[StructuredQuestion] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        # Remove the number prefix (e.g., "1. ")
        chunk = re.sub(r"^\s*\d+\.\s*", "", chunk)
        if chunk:
            parts.append(StructuredQuestion(text=chunk))

    return parts


def _dict_to_structured_question(data: dict[str, Any]) -> StructuredQuestion:
    """Convert a dictionary to a StructuredQuestion.

    Handles various dict formats that may come from DSPy modules:
    - {"question": "...", "rationale": "..."}
    - {"text": "...", "options": [...]}
    - {"q": "..."}
    """
    # Extract question text from various possible keys
    text = data.get("text") or data.get("question") or data.get("q") or str(data)

    # Extract options if present
    options: list[QuestionOption] | None = None
    raw_options = data.get("options")
    if isinstance(raw_options, list) and raw_options:
        options = []
        for opt in raw_options:
            if isinstance(opt, dict):
                opt_id = str(opt.get("id") or opt.get("value") or "")
                label = str(opt.get("label") or opt.get("text") or opt_id)
                desc = opt.get("description")
                if opt_id:
                    options.append(
                        QuestionOption(
                            id=opt_id,
                            label=label,
                            description=str(desc) if desc else None,
                        )
                    )
            elif isinstance(opt, str):
                options.append(QuestionOption(id=opt, label=opt))

    return StructuredQuestion(
        text=text,
        options=options if options else None,
        allows_multiple=bool(data.get("allows_multiple", False)),
        rationale=data.get("rationale"),
    )


__all__ = [
    "QuestionOption",
    "StructuredQuestion",
    "normalize_questions",
]
