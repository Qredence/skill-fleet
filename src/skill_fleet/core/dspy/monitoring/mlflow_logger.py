"""MLflow integration for DSPy experiment tracking.

Optional integration with MLflow for comprehensive experiment tracking and model versioning.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# MLflow is optional dependency
try:
    import mlflow  # type: ignore[import-untyped]

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.debug("MLflow not available - experiment tracking disabled")


def configure_mlflow(
    tracking_uri: str | None = None,
    experiment_name: str = "skill-fleet-dspy",
    artifact_location: str | None = None,
) -> bool:
    """Configure MLflow tracking.

    Args:
        tracking_uri: MLflow tracking server URI (None uses local ./mlruns)
        experiment_name: Name for MLflow experiment
        artifact_location: Custom artifact storage location

    Returns:
        True if MLflow configured successfully, False otherwise
    """
    if not MLFLOW_AVAILABLE:
        logger.warning("MLflow not installed - install with: pip install mlflow")
        return False

    try:
        # Set tracking URI
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
            logger.info(f"MLflow tracking URI: {tracking_uri}")
        else:
            # Use local mlruns directory
            mlruns_path = Path.cwd() / "mlruns"
            mlflow.set_tracking_uri(f"file://{mlruns_path.absolute()}")
            logger.info(f"MLflow tracking: local at {mlruns_path}")

        # Create or get experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(
                experiment_name,
                artifact_location=artifact_location,
            )
            logger.info(f"Created MLflow experiment: {experiment_name} (ID: {experiment_id})")
        else:
            mlflow.set_experiment(experiment_name)
            logger.info(f"Using existing MLflow experiment: {experiment_name}")

        return True

    except Exception as e:
        logger.error(f"Failed to configure MLflow: {e}")
        return False


class MLflowLogger:
    """Logger for DSPy experiments to MLflow.

    Tracks DSPy optimization runs, model performance, and artifacts.

    Example:
        # Configure MLflow
        configure_mlflow(experiment_name="skill-optimization")

        # Use logger
        with MLflowLogger(run_name="miprov2_v1") as logger:
            logger.log_params({"optimizer": "MIPROv2", "auto": "medium"})

            # Run optimization
            optimized = optimizer.compile(program, trainset=trainset)

            # Log metrics
            logger.log_metrics({"quality_score": 0.85, "examples_used": 50})

            # Save artifacts
            logger.log_artifact("optimized_program.pkl")
    """

    def __init__(
        self,
        run_name: str | None = None,
        nested: bool = False,
    ) -> None:
        """Initialize MLflow logger.

        Args:
            run_name: Name for this MLflow run
            nested: Whether this is a nested run (for sub-experiments)
        """
        if not MLFLOW_AVAILABLE:
            logger.warning("MLflow not available - logging will be no-op")

        self.run_name = run_name
        self.nested = nested
        self.run = None
        self.enabled = MLFLOW_AVAILABLE

    def __enter__(self) -> MLflowLogger:
        """Start MLflow run."""
        if self.enabled:
            self.run = mlflow.start_run(run_name=self.run_name, nested=self.nested)
            logger.info(f"Started MLflow run: {self.run_name or 'unnamed'}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End MLflow run."""
        if self.enabled and self.run:
            mlflow.end_run()
            logger.info(f"Ended MLflow run: {self.run_name or 'unnamed'}")

    def log_params(self, params: dict[str, Any]) -> None:
        """Log parameters to MLflow.

        Args:
            params: Dictionary of parameters to log
        """
        if not self.enabled:
            return

        try:
            # MLflow requires string/number values
            clean_params = {
                k: v if isinstance(v, (str, int, float, bool)) else str(v)
                for k, v in params.items()
            }
            mlflow.log_params(clean_params)
            logger.debug(f"Logged {len(clean_params)} params to MLflow")
        except Exception as e:
            logger.warning(f"Failed to log params to MLflow: {e}")

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log metrics to MLflow.

        Args:
            metrics: Dictionary of metric name -> value
            step: Optional step number for time series metrics
        """
        if not self.enabled:
            return

        try:
            mlflow.log_metrics(metrics, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow")
        except Exception as e:
            logger.warning(f"Failed to log metrics to MLflow: {e}")

    def log_artifact(self, local_path: str | Path, artifact_path: str | None = None) -> None:
        """Log artifact file to MLflow.

        Args:
            local_path: Path to local file to upload
            artifact_path: Optional subdirectory in artifact store
        """
        if not self.enabled:
            return

        try:
            mlflow.log_artifact(str(local_path), artifact_path=artifact_path)
            logger.debug(f"Logged artifact: {local_path}")
        except Exception as e:
            logger.warning(f"Failed to log artifact to MLflow: {e}")

    def log_dict(self, dictionary: dict[str, Any], filename: str) -> None:
        """Log dictionary as JSON artifact.

        Args:
            dictionary: Dictionary to save
            filename: Filename for artifact (should end in .json)
        """
        if not self.enabled:
            return

        try:
            import json
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
            ) as f:
                json.dump(dictionary, f, indent=2)
                temp_path = f.name

            mlflow.log_artifact(temp_path, artifact_path=filename)
            Path(temp_path).unlink()  # Clean up temp file
            logger.debug(f"Logged dict as artifact: {filename}")
        except Exception as e:
            logger.warning(f"Failed to log dict to MLflow: {e}")

    def log_text(self, text: str, filename: str) -> None:
        """Log text content as artifact.

        Args:
            text: Text content to save
            filename: Filename for artifact
        """
        if not self.enabled:
            return

        try:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=Path(filename).suffix,
                delete=False,
            ) as f:
                f.write(text)
                temp_path = f.name

            mlflow.log_artifact(temp_path, artifact_path=filename)
            Path(temp_path).unlink()  # Clean up temp file
            logger.debug(f"Logged text as artifact: {filename}")
        except Exception as e:
            logger.warning(f"Failed to log text to MLflow: {e}")

    def set_tags(self, tags: dict[str, Any]) -> None:
        """Set tags on current run.

        Args:
            tags: Dictionary of tag name -> value
        """
        if not self.enabled:
            return

        try:
            # Convert all values to strings
            clean_tags = {k: str(v) for k, v in tags.items()}
            mlflow.set_tags(clean_tags)
            logger.debug(f"Set {len(clean_tags)} tags on MLflow run")
        except Exception as e:
            logger.warning(f"Failed to set tags on MLflow: {e}")
