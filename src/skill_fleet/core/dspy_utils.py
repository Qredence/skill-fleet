"""
DSPy utility functions for skill-fleet.

Provides helper functions for module introspection, serialization,
and LM configuration management.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import dspy


def _settings_delattr(self, name: str) -> None:
    try:
        object.__delattr__(self, name)
    except AttributeError:
        pass


dspy.settings.__class__.__delattr__ = _settings_delattr  # type: ignore[assignment]

from dspy.utils.callback import with_callbacks  # noqa: E402

logger = logging.getLogger(__name__)


def get_module_info(module: dspy.Module) -> dict[str, Any]:
    """
    Get information about a DSPy module.

    Extracts module metadata including name, signatures, and nested modules.
    Useful for debugging, logging, and module registry.

    Args:
        module: DSPy module to inspect

    Returns:
        Dictionary with module information:
        - name: Module class name
        - signatures: List of signature names used by the module
        - nested_modules: List of nested module names
        - lm: Name of the configured language model (if any)

    Example:
        >>> module = MyModule()
        >>> info = get_module_info(module)
        >>> print(info["name"])
        'MyModule'
        >>> print(info["signatures"])
        ['MySignature']

    """
    info: dict[str, Any] = {
        "name": module.__class__.__name__,
        "signatures": [],
        "nested_modules": [],
        "lm": None,
    }

    # Try to get LM info from settings
    try:
        if hasattr(dspy.settings, "lm") and dspy.settings.lm is not None:
            lm = dspy.settings.lm
            info["lm"] = getattr(lm, "model", str(lm))
    except Exception as e:
        logger.debug(f"Could not get LM info: {e}")

    # Extract signatures from module attributes
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, dspy.Predict):
                # Get signature from predictor
                sig = getattr(attr, "signature", None)
                if sig is not None:
                    sig_name = getattr(sig, "__name__", str(sig))
                    info["signatures"].append(sig_name)
            elif isinstance(attr, dspy.Module):
                # Nested module
                info["nested_modules"].append(attr.__class__.__name__)
        except Exception as e:
            logger.debug(f"Error inspecting attribute {attr_name}: {e}")

    return info


def save_compiled_module(
    module: dspy.Module,
    filepath: str | Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """
    Save a compiled DSPy module to disk.

    Saves the module's compiled state including optimized prompts and
    demonstration examples. The saved file can be loaded later with
    `load_compiled_module()`.

    Args:
        module: Compiled DSPy module to save
        filepath: Path where to save the module (directory will be created)
        metadata: Optional metadata to include with the saved module

    Returns:
        Path to the saved module file

    Raises:
        ValueError: If module is not compiled
        OSError: If file cannot be written

    Example:
        >>> module = MyModule()
        >>> compiled = teleprompter.compile(module, trainset)
        >>> path = save_compiled_module(
        ...     compiled,
        ...     "models/my_module_v1.json",
        ...     metadata={"version": "1.0", "accuracy": 0.95}
        ... )

    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Check if module appears to be compiled
    # A compiled module typically has demonstrations or optimized prompts
    is_compiled = False
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, dspy.Predict):
                # Check for demonstrations
                demos = getattr(attr, "demos", [])
                if demos:
                    is_compiled = True
                    break
        except Exception:
            continue  # nosec B112

    if not is_compiled:
        logger.warning(
            f"Module {module.__class__.__name__} may not be compiled. "
            "Saving anyway, but load behavior may differ."
        )

    # Prepare save data
    save_data: dict[str, Any] = {
        "module_class": module.__class__.__name__,
        "module_state": {},
        "metadata": metadata or {},
    }

    # Extract module state
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(module, attr_name)
            if isinstance(attr, dspy.Predict):
                # Save predictor state
                predictor_state: dict[str, Any] = {
                    "signature": str(getattr(attr, "signature", "")),
                }
                if hasattr(attr, "demos"):
                    predictor_state["demos"] = attr.demos
                if hasattr(attr, "lm"):
                    predictor_state["lm"] = str(getattr(attr, "lm", ""))
                save_data["module_state"][attr_name] = predictor_state
        except Exception as e:
            logger.debug(f"Error saving attribute {attr_name}: {e}")

    # Write to file
    with open(filepath, "w") as f:
        json.dump(save_data, f, indent=2, default=str)

    logger.info(f"Saved module {module.__class__.__name__} to {filepath}")
    return filepath


def load_compiled_module(
    filepath: str | Path,
    module_class: type[dspy.Module] | None = None,
) -> dspy.Module:
    """
    Load a compiled DSPy module from disk.

    Restores a module's compiled state including optimized prompts and
    demonstration examples. The module class must be available at load time.

    Args:
        filepath: Path to the saved module file
        module_class: Optional module class to instantiate. If not provided,
            will try to load from the saved class name.

    Returns:
        Loaded DSPy module with restored state

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If module class cannot be found or instantiated

    Example:
        >>> # Load with known class
        >>> module = load_compiled_module("models/my_module_v1.json", MyModule)
        >>>
        >>> # Load with class name from file
        >>> module = load_compiled_module("models/my_module_v1.json")

    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Module file not found: {filepath}")

    with open(filepath) as f:
        save_data = json.load(f)

    module_class_name = save_data.get("module_class")
    if module_class is None:
        # Try to find the class
        # This is a simplified version - in production, you'd want proper
        # module path resolution
        raise ValueError(
            f"Module class {module_class_name} not provided. "
            "Please provide the module_class argument."
        )

    # Instantiate module
    try:
        module = module_class()
    except Exception as e:
        raise ValueError(f"Failed to instantiate {module_class.__name__}: {e}") from e

    # Restore module state
    module_state = save_data.get("module_state", {})
    for attr_name, predictor_state in module_state.items():
        if not hasattr(module, attr_name):
            logger.warning(f"Module doesn't have attribute {attr_name}, skipping")
            continue

        predictor = getattr(module, attr_name)
        if not isinstance(predictor, dspy.Predict):
            logger.warning(f"Attribute {attr_name} is not a Predictor, skipping")
            continue

        # Restore demonstrations
        if "demos" in predictor_state:
            try:
                predictor.demos = predictor_state["demos"]
            except Exception as e:
                logger.warning(f"Failed to restore demos for {attr_name}: {e}")

    metadata = save_data.get("metadata", {})
    logger.info(f"Loaded module {module.__class__.__name__} from {filepath} (metadata: {metadata})")

    return module


@contextmanager
def fast_generation(lm: dspy.LM | None = None):
    """
    Context manager for fast/temperature-based generation.

    Temporarily switches to a faster, more creative generation mode
    by using a higher temperature. Useful for brainstorming or
    generating diverse candidates.

    Args:
        lm: Optional LM to use. If not provided, uses current LM.

    Yields:
        The configured LM

    Example:
        >>> with fast_generation() as lm:
        ...     # Generate creative, diverse ideas
        ...     result = module.brainstorm(topic="AI applications")

    """
    # Store current settings
    original_lm = dspy.settings.lm

    # Use provided LM or current
    active_lm = lm or original_lm

    if active_lm is None:
        logger.warning("No LM configured for fast_generation")
        yield None
        return

    # Configure for fast generation (higher temperature)
    original_temp: float | None = None
    try:
        # Try to set temperature if LM supports it
        active_kwargs = getattr(active_lm, "kwargs", None)
        if isinstance(active_kwargs, dict):
            temp_value = active_kwargs.get("temperature", 0.7)
            if isinstance(temp_value, int | float):
                original_temp = float(temp_value)
            active_kwargs["temperature"] = 0.9
        elif hasattr(active_lm, "temperature"):
            temp_value = getattr(active_lm, "temperature", None)
            if isinstance(temp_value, int | float):
                original_temp = float(temp_value)
            active_lm.temperature = 0.9  # type: ignore[assignment]

        with dspy.context(lm=active_lm):
            yield active_lm

    finally:
        # Restore original temperature
        active_kwargs = getattr(active_lm, "kwargs", None)
        if isinstance(active_kwargs, dict) and original_temp is not None:
            active_kwargs["temperature"] = original_temp
        elif hasattr(active_lm, "temperature") and original_temp is not None:
            active_lm.temperature = original_temp  # type: ignore[assignment]


@contextmanager
def high_quality_generation(lm: dspy.LM | None = None):
    """
    Context manager for high-quality/low-temperature generation.

    Temporarily switches to a more deterministic, high-quality generation
    mode by using a lower temperature. Useful for final outputs or
    when consistency is important.

    Args:
        lm: Optional LM to use. If not provided, uses current LM.

    Yields:
        The configured LM

    Example:
        >>> with high_quality_generation() as lm:
        ...     # Generate final, polished output
        ...     result = module.finalize(content=draft)

    """
    # Store current settings
    original_lm = dspy.settings.lm

    # Use provided LM or current
    active_lm = lm or original_lm

    if active_lm is None:
        logger.warning("No LM configured for high_quality_generation")
        yield None
        return

    # Configure for high-quality generation (lower temperature)
    original_temp: float | None = None
    try:
        # Try to set temperature if LM supports it
        active_kwargs = getattr(active_lm, "kwargs", None)
        if isinstance(active_kwargs, dict):
            temp_value = active_kwargs.get("temperature", 0.7)
            if isinstance(temp_value, int | float):
                original_temp = float(temp_value)
            active_kwargs["temperature"] = 0.2
        elif hasattr(active_lm, "temperature"):
            temp_value = getattr(active_lm, "temperature", None)
            if isinstance(temp_value, int | float):
                original_temp = float(temp_value)
            active_lm.temperature = 0.2  # type: ignore[assignment]

        with dspy.context(lm=active_lm):
            yield active_lm

    finally:
        # Restore original temperature
        active_kwargs = getattr(active_lm, "kwargs", None)
        if isinstance(active_kwargs, dict) and original_temp is not None:
            active_kwargs["temperature"] = original_temp
        elif hasattr(active_lm, "temperature") and original_temp is not None:
            active_lm.temperature = original_temp  # type: ignore[assignment]


class ModuleRegistry:
    """
    Registry for managing compiled DSPy modules.

    Provides a simple key-value store for modules with versioning
    and metadata tracking. Useful for A/B testing and model management.

    Example:
        >>> registry = ModuleRegistry("models/")
        >>> registry.register("intent_v1", compiled_module, accuracy=0.95)
        >>> module = registry.load("intent_v1")
        >>> versions = registry.list_versions()

    """

    def __init__(self, base_path: str | Path):
        """
        Initialize the registry.

        Args:
            base_path: Directory where modules will be stored

        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._index_file = self.base_path / "registry_index.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load registry index from disk."""
        if self._index_file.exists():
            with open(self._index_file) as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        """Save registry index to disk."""
        with open(self._index_file, "w") as f:
            json.dump(self._index, f, indent=2)

    def register(
        self,
        name: str,
        module: dspy.Module,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """
        Register a module in the registry.

        Args:
            name: Unique name for the module
            module: Module to register
            metadata: Optional metadata (accuracy, training set, etc.)

        Returns:
            Path where module was saved

        """
        filepath = self.base_path / f"{name}.json"
        save_compiled_module(module, filepath, metadata)

        self._index[name] = {
            "filepath": str(filepath),
            "module_class": module.__class__.__name__,
            "metadata": metadata or {},
        }
        self._save_index()

        logger.info(f"Registered module '{name}' at {filepath}")
        return filepath

    def load(self, name: str, module_class: type[dspy.Module] | None = None) -> dspy.Module:
        """
        Load a registered module.

        Args:
            name: Name of the registered module
            module_class: Optional module class (required if not stored in index)

        Returns:
            Loaded module

        Raises:
            KeyError: If module not found in registry

        """
        if name not in self._index:
            raise KeyError(f"Module '{name}' not found in registry")

        entry = self._index[name]
        filepath = entry["filepath"]

        # Use stored class name if no class provided
        if module_class is None:
            raise ValueError(f"module_class required for '{name}'")

        return load_compiled_module(filepath, module_class)

    def list_versions(self) -> dict[str, dict[str, Any]]:
        """
        List all registered modules and their metadata.

        Returns:
            Dictionary mapping names to their metadata

        """
        return {
            name: {
                "module_class": entry["module_class"],
                "metadata": entry["metadata"],
            }
            for name, entry in self._index.items()
        }

    def unregister(self, name: str) -> None:
        """
        Remove a module from the registry.

        Args:
            name: Name of the module to remove

        Raises:
            KeyError: If module not found

        """
        if name not in self._index:
            raise KeyError(f"Module '{name}' not found in registry")

        entry = self._index.pop(name)
        filepath = Path(entry["filepath"])

        if filepath.exists():
            filepath.unlink()

        self._save_index()
        logger.info(f"Unregistered module '{name}'")


def create_ensemble_predictor(
    modules: list[dspy.Module],
    aggregation: str = "majority",
) -> dspy.Module:
    """
    Create an ensemble predictor from multiple modules.

    Combines predictions from multiple modules using various aggregation
    strategies. Useful for improving reliability through model ensembling.

    Args:
        modules: List of modules to ensemble
        aggregation: Aggregation strategy ("majority", "average", "best")

    Returns:
        Ensemble predictor module

    Example:
        >>> ensemble = create_ensemble_predictor(
        ...     [module_v1, module_v2, module_v3],
        ...     aggregation="majority"
        ... )
        >>> result = ensemble.predict(input="test")

    """

    class EnsembleModule(dspy.Module):
        """Ensemble predictor combining multiple modules."""

        def __init__(self, modules: list[dspy.Module], aggregation: str):
            super().__init__()
            self.modules = modules
            self.aggregation = aggregation

        @with_callbacks
        def forward(self, **kwargs) -> dspy.Prediction:
            """Run ensemble prediction."""
            if self.aggregation not in {"majority", "average", "best"}:
                raise ValueError(f"Unknown aggregation: {self.aggregation}")

            # Get predictions from all modules
            predictions = []
            for module in self.modules:
                try:
                    pred = module(**kwargs)
                    predictions.append(pred)
                except Exception as e:
                    logger.warning(f"Module {module.__class__.__name__} failed: {e}")

            if not predictions:
                raise RuntimeError("All modules in ensemble failed")

            # Aggregate predictions
            if self.aggregation == "majority":
                return self._majority_vote(predictions)
            if self.aggregation == "average":
                return self._average(predictions)
            return self._best(predictions)

        def _majority_vote(self, predictions: list[dspy.Prediction]) -> dspy.Prediction:
            """Simple majority voting for categorical outputs."""
            # Get all output fields from first prediction
            prediction_dicts = [dict(p) for p in predictions]
            keys = {key for d in prediction_dicts for key in d}
            result: dict[str, Any] = {}

            for key in keys:
                values = [d[key] for d in prediction_dicts if key in d]
                if not values:
                    continue

                # For strings, use most common
                if isinstance(values[0], str):
                    result[key] = max(set(values), key=values.count)
                # For numbers, use mean
                elif isinstance(values[0], int | float):
                    result[key] = sum(values) / len(values)
                else:
                    # For other types, use first
                    result[key] = values[0]

            return dspy.Prediction(**result)

        def _average(self, predictions: list[dspy.Prediction]) -> dspy.Prediction:
            """Average numeric outputs."""
            prediction_dicts = [dict(p) for p in predictions]
            keys = {key for d in prediction_dicts for key in d}
            result: dict[str, Any] = {}

            for key in keys:
                values = [d[key] for d in prediction_dicts if key in d]
                if not values:
                    continue

                # Average numeric values
                if isinstance(values[0], int | float):
                    result[key] = sum(values) / len(values)
                else:
                    # For non-numeric, use first
                    result[key] = values[0]

            return dspy.Prediction(**result)

        def _best(self, predictions: list[dspy.Prediction]) -> dspy.Prediction:
            """Select best prediction based on confidence if available."""
            # If predictions have confidence scores, use highest
            for pred in predictions:
                if hasattr(pred, "confidence"):
                    return max(predictions, key=lambda p: getattr(p, "confidence", 0))

            # Otherwise use first
            return predictions[0]

    return EnsembleModule(modules, aggregation)


class ValidationReward:
    """
    Reward function for validation results.

    Scores validation predictions based on compliance and issue severity.
    Returns a score between 0.0 and 1.0.

    Example:
        >>> reward = ValidationReward()
        >>> result = dspy.Prediction(
        ...     passed=True,
        ...     compliance_score=0.9,
        ...     issues=[],
        ... )
        >>> score = reward(result)
        >>> print(score)  # 0.9 or higher

    """

    def __call__(self, result: dspy.Prediction | dict[str, Any]) -> float:
        """
        Calculate reward score for validation result.

        Args:
            result: Validation result as Prediction or dict

        Returns:
            Score between 0.0 and 1.0

        """
        # Convert Prediction to dict if needed
        if isinstance(result, dspy.Prediction):
            result_dict = {
                "passed": getattr(result, "passed", False),
                "compliance_score": getattr(result, "compliance_score", 0.0),
                "issues": getattr(result, "issues", []),
                "critical_issues": getattr(result, "critical_issues", []),
                "warnings": getattr(result, "warnings", []),
            }
        else:
            result_dict = result

        # Base score from compliance
        base_score_value = result_dict.get("compliance_score", 0.0)
        base_score = float(base_score_value) if isinstance(base_score_value, int | float) else 0.0

        # Adjust for issues
        issues_value = result_dict.get("issues", [])
        critical_issues_value = result_dict.get("critical_issues", [])
        warnings_value = result_dict.get("warnings", [])

        issues = issues_value if isinstance(issues_value, list) else []
        critical_issues = critical_issues_value if isinstance(critical_issues_value, list) else []
        warnings = warnings_value if isinstance(warnings_value, list) else []

        # Penalize critical issues heavily
        critical_penalty = len(critical_issues) * 0.3

        # Penalize regular issues
        issue_penalty = len(issues) * 0.1

        # Small penalty for warnings
        warning_penalty = len(warnings) * 0.02

        # Calculate final score
        score = base_score - critical_penalty - issue_penalty - warning_penalty

        # Ensure passed results have minimum score
        if result_dict.get("passed", False) and score < 0.5:
            score = 0.5

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))
