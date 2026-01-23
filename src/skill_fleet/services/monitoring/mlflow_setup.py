"""MLflow setup and configuration for DSPy autologging."""

import mlflow


def setup_dspy_autologging(
    tracking_uri: str | None = None,
    experiment_name: str = "skill-fleet",
    disable: bool = False,
) -> None:
    """
    Enable MLflow autologging for DSPy operations.

    Args:
        tracking_uri: MLflow tracking server URI
        experiment_name: Name of the MLflow experiment to use/create
        disable: If True, disables MLflow autologging

    """
    if disable:
        mlflow.dspy.disable_autologging()
        return

    if tracking_uri:
        mlflow.set_tracking_uri(tracking_uri)

    mlflow.set_experiment(experiment_name)

    try:
        mlflow.dspy.autolog()
    except AttributeError:
        import warnings

        warnings.warn(
            "mlflow.dspy.autolog() not available. "
            "Ensure DSPy 3.1.2+ is installed for automatic DSPy tracking.",
            stacklevel=2,
        )


def get_current_run_id() -> str | None:
    """Get the current MLflow run ID if an active run exists."""
    try:
        run = mlflow.active_run()
        return run.info.run_id if run else None
    except Exception:
        return None


class MLflowContext:
    """Context manager for MLflow runs with automatic cleanup."""

    def __init__(
        self,
        run_name: str | None = None,
        tags: dict | None = None,
        description: str | None = None,
    ):
        """
        Initialize MLflow context.

        Args:
            run_name: Name for the MLflow run
            tags: Tags to add to the run
            description: Run description

        """
        self.run_name = run_name
        self.tags = tags or {}
        self.description = description
        self._run = None

    def __enter__(self):
        """Enter context manager and start MLflow run."""
        self._run = mlflow.start_run(
            run_name=self.run_name,
            tags=self.tags,
            description=self.description,
        )
        return self._run

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and end MLflow run."""
        if exc_type is not None:
            mlflow.set_tag("status", "failed")
            mlflow.set_tag("error", str(exc_val))
        else:
            mlflow.set_tag("status", "completed")

        mlflow.end_run()
        return False
