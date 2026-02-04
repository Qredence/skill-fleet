"""Tests for environment helpers."""

import pytest

from skill_fleet.common.env_utils import resolve_api_credentials


def test_resolve_prefers_litellm(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("LITELLM_API_KEY=litellm-dotenv\nLITELLM_BASE_URL=http://localhost:4000\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LITELLM_API_KEY", "litellm-os")
    monkeypatch.setenv("LITELLM_BASE_URL", "http://localhost:9999")

    creds = resolve_api_credentials(prefer_litellm=True)

    assert creds["api_key"] == "litellm-dotenv"
    assert creds["base_url"] == "http://localhost:4000"
    assert creds["source"] == "LITELLM_API_KEY"


def test_resolve_accepts_v1_suffix(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "LITELLM_API_KEY=litellm-dotenv\nLITELLM_BASE_URL=http://localhost:4000/v1\n"
    )
    monkeypatch.chdir(tmp_path)

    creds = resolve_api_credentials(prefer_litellm=True)

    assert creds["api_key"] == "litellm-dotenv"
    assert creds["base_url"] == "http://localhost:4000/v1"


def test_resolve_rejects_provider_endpoint(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "LITELLM_API_KEY=litellm-dotenv\n"
        "LITELLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/foo:generateContent\n"
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="LITELLM_BASE_URL must be the LiteLLM proxy root"):
        resolve_api_credentials(prefer_litellm=True)


def test_resolve_rejects_provider_endpoint_without_key(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "LITELLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/models/foo:generateContent\n"
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="LITELLM_BASE_URL must be the LiteLLM proxy root"):
        resolve_api_credentials(prefer_litellm=True)


def test_resolve_rejects_missing_scheme(monkeypatch, tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("LITELLM_API_KEY=litellm-dotenv\nLITELLM_BASE_URL=localhost:4000\n")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="LITELLM_BASE_URL must be the LiteLLM proxy root"):
        resolve_api_credentials(prefer_litellm=True)
