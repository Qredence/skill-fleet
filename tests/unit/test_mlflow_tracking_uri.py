from __future__ import annotations


def test_mlflow_tracking_uri_default(monkeypatch):
    monkeypatch.delenv("SKILL_FLEET_MLFLOW_TRACKING_URI", raising=False)
    monkeypatch.delenv("MLFLOW_TRACKING_URI", raising=False)

    from skill_fleet.infrastructure.tracing import mlflow as mlflow_tracing

    assert mlflow_tracing._get_tracking_uri() == mlflow_tracing.DEFAULT_TRACKING_URI
    assert mlflow_tracing.DEFAULT_TRACKING_URI.startswith("sqlite:///")


def test_mlflow_tracking_uri_env_precedence(monkeypatch):
    from skill_fleet.infrastructure.tracing import mlflow as mlflow_tracing

    monkeypatch.setenv("MLFLOW_TRACKING_URI", "sqlite:///from-mlflow-env.db")
    monkeypatch.setenv("SKILL_FLEET_MLFLOW_TRACKING_URI", "sqlite:///from-skill-fleet-env.db")

    assert mlflow_tracing._get_tracking_uri() == "sqlite:///from-skill-fleet-env.db"
