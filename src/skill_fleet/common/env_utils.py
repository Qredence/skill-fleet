"""Environment helpers for resolving preferred LLM API credentials.

Provides a small utility to prefer LiteLLM proxy credentials (LITELLM_API_KEY
and LITELLM_BASE_URL) when present, and fall back to Google/Gemini keys
(`GOOGLE_API_KEY` / `GEMINI_API_KEY`) otherwise.

This centralizes credential resolution so the rest of the codebase can
consistently prefer the proxy when configured.
"""

from __future__ import annotations

import os
from typing import TypedDict


class APICredentials(TypedDict, total=False):
    """Resolved API credential bundle.

    Keys are present only when available (TypedDict `total=False`).
    """

    api_key: str
    base_url: str
    source: str


def resolve_api_credentials(
    prefer_litellm: bool = True, requested_env: str | None = None
) -> APICredentials:
    """Resolve API key and optional base URL.

    Resolution rules:
    - If `requested_env` is provided, try that env var first. If it is
      `LITELLM_API_KEY` and present, include `LITELLM_BASE_URL` (if any).
    - Otherwise, when `prefer_litellm` is True, prefer `LITELLM_API_KEY`
      (and `LITELLM_BASE_URL`) if set; fallback to `GOOGLE_API_KEY` or
      `GEMINI_API_KEY`.
    - When `prefer_litellm` is False, prefer Google/Gemini first.

    Returns a dict with optional keys: `api_key`, `base_url`, `source`.
    """
    creds: APICredentials = {}

    def _litellm_present() -> bool:
        return bool(os.environ.get("LITELLM_API_KEY"))

    def _google_present() -> bool:
        return bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))

    # If a specific env var was requested, try that first
    if requested_env:
        val = os.environ.get(requested_env)
        if val:
            creds["api_key"] = val
            creds["source"] = requested_env
            if requested_env == "LITELLM_API_KEY":
                base = os.environ.get("LITELLM_BASE_URL", "")
                if base:
                    creds["base_url"] = base
            return creds

    # Preference logic
    if prefer_litellm:
        if _litellm_present():
            creds["api_key"] = os.environ.get("LITELLM_API_KEY", "")
            base = os.environ.get("LITELLM_BASE_URL", "")
            if base:
                creds["base_url"] = base
            creds["source"] = "LITELLM_API_KEY"
            return creds
        if _google_present():
            creds["api_key"] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            creds["source"] = "GOOGLE/GEMINI"
            return creds
    else:
        if _google_present():
            creds["api_key"] = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            creds["source"] = "GOOGLE/GEMINI"
            return creds
        if _litellm_present():
            creds["api_key"] = os.environ.get("LITELLM_API_KEY", "")
            base = os.environ.get("LITELLM_BASE_URL", "")
            if base:
                creds["base_url"] = base
            creds["source"] = "LITELLM_API_KEY"
            return creds

    # Nothing found
    return creds
