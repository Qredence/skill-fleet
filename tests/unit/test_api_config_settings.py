from __future__ import annotations


def test_api_settings_mlflow_tracking_uri_default(monkeypatch):
    from skill_fleet.api.config import APISettings

    monkeypatch.delenv("SKILL_FLEET_MLFLOW_TRACKING_URI", raising=False)

    settings = APISettings()

    assert settings.mlflow_tracking_uri == "sqlite:///mlflow.db"


def test_api_settings_mlflow_tracking_uri_override(monkeypatch):
    from skill_fleet.api.config import APISettings

    monkeypatch.setenv("SKILL_FLEET_MLFLOW_TRACKING_URI", "sqlite:///override.db")

    settings = APISettings()

    assert settings.mlflow_tracking_uri == "sqlite:///override.db"
