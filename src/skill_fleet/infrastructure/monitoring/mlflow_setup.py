"""MLflow setup and configuration for DSPy autologging with 3.1.2+ support."""

from __future__ import annotations

import asyncio
import contextlib
import importlib
import logging
from typing import TYPE_CHECKING, Any

mlflow: Any | None
try:
    mlflow = importlib.import_module("mlflow")
except Exception:  # pragma: no cover
    mlflow = None

if TYPE_CHECKING:
    import dspy

    pass  # Reserved for future type-only imports

logger = logging.getLogger(__name__)


def _in_async_task() -> bool:
    """Return whether the current code is running in an active asyncio task."""
    try:
        return asyncio.current_task() is not None
    except RuntimeError:
        # No event loop in this thread.
        return False


def setup_dspy_autologging(
    tracking_uri: str | None = None,
    experiment_name: str = "skill-fleet",
    disable: bool = False,
    log_compiles: bool = True,
    log_evals: bool = True,
    log_traces: bool = False,
) -> bool:
    """
    Enable MLflow autologging for DSPy operations.

    Args:
        tracking_uri: MLflow tracking server URI
        experiment_name: Name of the MLflow experiment to use/create
        disable: If True, disables MLflow autologging
        log_compiles: Track optimization/compiles
        log_evals: Track evaluations
        log_traces: Track execution traces (heavy)

    Returns:
        bool: True when autologging was enabled (or explicitly disabled), False otherwise.

    """
    if mlflow is None:
        logger.debug("MLflow not installed; skipping autologging setup.")
        return False
    mlflow_mod: Any = mlflow

    if disable:
        with contextlib.suppress(AttributeError):
            mlflow_mod.dspy.disable_autologging()
        return True

    # DSPy configuration is task-local. Running autologging setup from an async
    # task can trigger configure() in a different task than startup.
    if _in_async_task():
        logger.warning(
            "Skipping MLflow DSPy autologging setup in async task context. "
            "Initialize it during synchronous app startup."
        )
        return False

    if tracking_uri:
        mlflow_mod.set_tracking_uri(tracking_uri)

    mlflow_mod.set_experiment(experiment_name)

    try:
        # DSPy 3.1.2+ supports detailed autologging options
        mlflow_mod.dspy.autolog(
            log_compiles=log_compiles,
            log_evals=log_evals,
            log_traces_from_compile=log_traces,
        )
        logger.info(f"MLflow autologging enabled: {tracking_uri or 'default'}/{experiment_name}")
        return True
    except AttributeError:
        import warnings

        warnings.warn(
            "mlflow.dspy.autolog() not available. "
            "Ensure DSPy 3.1.2+ is installed for automatic DSPy tracking.",
            stacklevel=2,
        )
        return False
    except Exception as e:
        logger.warning(f"Failed to setup MLflow autologging: {e}")
        return False


def get_current_run_id() -> str | None:
    """Get the current MLflow run ID if an active run exists."""
    if mlflow is None:
        return None
    try:
        mlflow_mod: Any = mlflow
        run = mlflow_mod.active_run()
        return run.info.run_id if run else None
    except Exception:
        return None


def log_module_execution(
    module_name: str,
    inputs: dict[str, Any],
    outputs: dspy.Prediction,
    metrics: dict[str, float] | None = None,
) -> None:
    """
    Log module execution to MLflow.

    Args:
        module_name: Name of the module
        inputs: Input parameters
        outputs: Prediction outputs
        metrics: Optional metrics to log

    """
    if mlflow is None:
        return
    mlflow_mod: Any = mlflow
    try:
        with mlflow_mod.start_run(nested=True):
            mlflow_mod.set_tag("module", module_name)

            # Log inputs as params
            for key, value in inputs.items():
                mlflow_mod.log_param(f"input_{key}", str(value)[:250])

            # Log outputs
            for key in outputs.__dict__:
                value = getattr(outputs, key)
                mlflow_mod.log_text(str(value), f"output_{key}.txt")

            # Log metrics
            if metrics:
                mlflow_mod.log_metrics(metrics)

    except Exception as e:
        logger.debug(f"Failed to log to MLflow: {e}")


def save_compiled_module_artifact(
    module: dspy.Module,
    artifact_path: str = "compiled_module",
) -> None:
    """
    Save compiled module as MLflow artifact.

    Args:
        module: Compiled DSPy module
        artifact_path: Path for the artifact

    Note:
        This function requires module.save() to work. The old
        skill_fleet.core.dspy_utils.save_compiled_module path was removed.

    """
    if mlflow is None:
        return
    mlflow_mod: Any = mlflow
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Use DSPy's native save method
            module.save(f.name, save_program=False)
            mlflow_mod.log_artifact(f.name, artifact_path)

    except Exception as e:
        logger.warning(f"Failed to save module artifact: {e}")


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
        if mlflow is None:
            raise RuntimeError("MLflow is not installed")

        mlflow_mod: Any = mlflow
        start_run = getattr(mlflow_mod, "start_run", None)
        if start_run is None:
            raise RuntimeError("mlflow.start_run is not available")

        self._run = start_run(
            run_name=self.run_name,
            tags=self.tags,
            description=self.description,
        )
        return self._run

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and end MLflow run."""
        if mlflow is None:
            return False

        mlflow_mod: Any = mlflow
        if exc_type is not None:
            mlflow_mod.set_tag("status", "failed")
            mlflow_mod.set_tag("error", str(exc_val))
        else:
            mlflow_mod.set_tag("status", "completed")

        mlflow_mod.end_run()
        return False
