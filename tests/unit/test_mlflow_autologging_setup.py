from __future__ import annotations

import asyncio
from unittest.mock import MagicMock


def test_setup_dspy_autologging_returns_true_on_success(monkeypatch):
    from skill_fleet.infrastructure.monitoring import mlflow_setup

    mlflow_stub = MagicMock()
    mlflow_stub.dspy = MagicMock()
    monkeypatch.setattr(mlflow_setup, "mlflow", mlflow_stub)

    enabled = mlflow_setup.setup_dspy_autologging(
        tracking_uri="sqlite:///tracking.db",
        experiment_name="skill-fleet-tests",
    )

    assert enabled is True
    mlflow_stub.set_tracking_uri.assert_called_once_with("sqlite:///tracking.db")
    mlflow_stub.set_experiment.assert_called_once_with("skill-fleet-tests")
    mlflow_stub.dspy.autolog.assert_called_once()


def test_setup_dspy_autologging_returns_false_on_failure(monkeypatch):
    from skill_fleet.infrastructure.monitoring import mlflow_setup

    mlflow_stub = MagicMock()
    mlflow_stub.dspy = MagicMock()
    mlflow_stub.dspy.autolog.side_effect = RuntimeError("autolog failed")
    monkeypatch.setattr(mlflow_setup, "mlflow", mlflow_stub)

    enabled = mlflow_setup.setup_dspy_autologging()

    assert enabled is False
    mlflow_stub.set_experiment.assert_called_once()


def test_setup_dspy_autologging_skips_async_task(monkeypatch):
    from skill_fleet.infrastructure.monitoring import mlflow_setup

    mlflow_stub = MagicMock()
    mlflow_stub.dspy = MagicMock()
    monkeypatch.setattr(mlflow_setup, "mlflow", mlflow_stub)

    async def _run() -> bool:
        return mlflow_setup.setup_dspy_autologging()

    enabled = asyncio.run(_run())

    assert enabled is False
    mlflow_stub.set_experiment.assert_not_called()
    mlflow_stub.dspy.autolog.assert_not_called()
