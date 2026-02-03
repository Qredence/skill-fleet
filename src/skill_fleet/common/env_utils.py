"""
Environment helpers for resolving preferred LLM API credentials.

Provides a small utility to prefer LiteLLM proxy credentials (LITELLM_API_KEY
and LITELLM_BASE_URL) when present, and fall back to Google/Gemini keys
(`GOOGLE_API_KEY` / `GEMINI_API_KEY`) otherwise.

This centralizes credential resolution so the rest of the codebase can
consistently prefer the proxy when configured.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict, cast
from urllib.parse import urlparse

from dotenv import dotenv_values


class APICredentials(TypedDict, total=False):
    """
    Resolved API credential bundle.

    Keys are present only when available (TypedDict `total=False`).
    """

    api_key: str
    base_url: str
    source: str


_INVALID_LITELLM_SEGMENTS = (
    "generatecontent",
    "v1beta",
    "aiplatform.googleapis.com",
    "generativelanguage.googleapis.com",
)
_LITELLM_BASE_URL_DOCS = "https://docs.litellm.ai/docs/providers/openai_compatible"


def _normalize_litellm_base_url(base_url: str) -> str:
    """
    Validate and normalize LiteLLM proxy base URL.

    Expected format: http(s)://host[:port] or http(s)://host[:port]/v1
    """
    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(
            "LITELLM_BASE_URL must be the LiteLLM proxy root, e.g. http://localhost:4000. "
            f"See {_LITELLM_BASE_URL_DOCS}"
        )

    lowered = base_url.lower()
    if any(segment in lowered for segment in _INVALID_LITELLM_SEGMENTS):
        raise ValueError(
            "LITELLM_BASE_URL must be the LiteLLM proxy root, e.g. http://localhost:4000. "
            "Do not set provider endpoints like generateContent or generativelanguage.googleapis.com. "
            "If you need /v1 for upstream providers, configure it in the proxy model config instead. "
            f"See {_LITELLM_BASE_URL_DOCS}"
        )

    path = parsed.path.rstrip("/")
    if path and path != "/v1":
        raise ValueError(
            "LITELLM_BASE_URL must be the LiteLLM proxy root, e.g. http://localhost:4000 "
            "or http://localhost:4000/v1. "
            f"See {_LITELLM_BASE_URL_DOCS}"
        )

    normalized = f"{parsed.scheme}://{parsed.netloc}{path}"
    return normalized.rstrip("/")


def _dotenv_values() -> dict[str, str]:
    values: dict[str, str] = {}
    repo_root = Path(__file__).resolve().parents[3]
    candidates = []
    repo_env = repo_root / ".env"
    cwd_env = Path.cwd() / ".env"
    if repo_env.exists():
        candidates.append(repo_env)
    if cwd_env.exists() and cwd_env != repo_env:
        candidates.append(cwd_env)
    for path in candidates:
        loaded = dotenv_values(path)
        values.update({k: v for k, v in loaded.items() if v is not None})
    return values


def _get_env_value(key: str) -> str | None:
    values = _dotenv_values()
    if key in values and values[key] != "":
        return values[key]
    return os.environ.get(key)


def resolve_api_credentials(
    prefer_litellm: bool = True, requested_env: str | None = None
) -> APICredentials:
    """
    Resolve API key and optional base URL.

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

    base = _get_env_value("LITELLM_BASE_URL") or ""
    normalized_base = _normalize_litellm_base_url(base) if base else ""

    def _litellm_present() -> bool:
        return bool(_get_env_value("LITELLM_API_KEY"))

    def _google_present() -> bool:
        return bool(_get_env_value("GOOGLE_API_KEY") or _get_env_value("GEMINI_API_KEY"))

    # If a specific env var was requested, try that first
    if requested_env:
        val = _get_env_value(requested_env)
        if val:
            creds["api_key"] = val
            creds["source"] = requested_env
            if requested_env == "LITELLM_API_KEY" and normalized_base:
                creds["base_url"] = normalized_base
            return creds

    # Preference logic
    if prefer_litellm:
        if _litellm_present():
            creds["api_key"] = _get_env_value("LITELLM_API_KEY") or ""
            if normalized_base:
                creds["base_url"] = normalized_base
            creds["source"] = "LITELLM_API_KEY"
            return creds
        if _google_present():
            google_key = _get_env_value("GOOGLE_API_KEY") or _get_env_value("GEMINI_API_KEY")
            creds["api_key"] = cast("str", google_key)
            creds["source"] = "GOOGLE/GEMINI"
            return creds
    else:
        if _google_present():
            google_key = _get_env_value("GOOGLE_API_KEY") or _get_env_value("GEMINI_API_KEY")
            creds["api_key"] = cast("str", google_key)
            creds["source"] = "GOOGLE/GEMINI"
            return creds
        if _litellm_present():
            creds["api_key"] = _get_env_value("LITELLM_API_KEY") or ""
            if normalized_base:
                creds["base_url"] = normalized_base
            creds["source"] = "LITELLM_API_KEY"
            return creds

    # Nothing found
    return creds
