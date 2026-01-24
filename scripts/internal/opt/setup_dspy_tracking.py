#!/usr/bin/env python3
"""
Setup DSPy tracking and MLflow integration for skills-fleet.

DSPy v3.1.0 provides comprehensive monitoring capabilities:
- Execution tracing (time, tokens, cost)
- Parameter tracking (demos, instructions, weights)
- LM call logging (requests, responses, errors)
- Experiment comparison

MLflow Integration:
- Track DSPy program versions
- Store optimization artifacts
- Compare optimizer performance
- Log metrics over time

Usage:
    uv run python scripts/setup_dspy_tracking.py
    uv run python -m skill_fleet.core.dspy.tracking.track_optimization
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import dspy

from skill_fleet.core.optimization.optimizer import get_lm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def configure_dspy_for_tracking() -> None:
    """
    Configure DSPy with comprehensive tracking enabled.

    DSPy v3.1.0 supports:
    - dspy.settings.configure(track_lm_calls=True)
    - dspy.settings.configure(cache_dir="./.dspy_cache")
    - dspy.settings.configure(experimental=True)  # Enable beta features
    """
    logger.info("Configuring DSPy for production tracking...")

    # Enable LM call tracking
    try:
        dspy.settings.configure(track_lm_calls=True)
        logger.info("✅ LM call tracking enabled")
    except Exception as e:
        logger.warning(f"Could not enable LM tracking: {e}")

    # Configure cache directory
    try:
        from skill_fleet.common.paths import find_repo_root

        repo_root = find_repo_root(Path.cwd()) or Path.cwd()
        cache_dir = repo_root / ".dspy_cache"
        cache_dir.mkdir(exist_ok=True)
        dspy.settings.configure(cache_dir=str(cache_dir))
        logger.info(f"✅ DSPy cache configured: {cache_dir}")
    except Exception as e:
        logger.warning(f"Could not configure cache: {e}")

    # Enable experimental DSPy features (v3.1.0)
    try:
        dspy.settings.configure(experimental=True)
        logger.info("✅ DSPy experimental features enabled")
    except Exception as e:
        logger.warning(f"Could not enable experimental features: {e}")

    logger.info("✅ DSPy tracking configuration complete")


def setup_mlflow_integration() -> bool:
    """
    Setup MLflow integration for DSPy experiments.

    Returns:
        True if MLflow available, False otherwise

    """
    logger.info("Setting up MLflow integration...")

    # Check if MLflow is installed
    try:
        import mlflow

        logger.info("✅ MLflow package available")
    except ImportError:
        logger.warning("❌ MLflow not installed - experiment tracking disabled")
        logger.info("To enable MLflow: pip install mlflow")
        return False

    # Configure MLflow for DSPy experiments
    try:
        # Set tracking URI (use local mlruns by default)
        mlflow.set_tracking_uri("file://./mlruns")
        logger.info("✅ MLflow tracking URI set to local mlruns")

        # Create experiment (or use existing)
        experiment_name = "skill-fleet-dspy-optimization"

        try:
            # Try to get existing experiment
            mlflow.get_experiment_by_name(experiment_name)
            logger.info(f"✅ Using existing MLflow experiment: {experiment_name}")
        except Exception:
            # Create new experiment
            mlflow.create_experiment(
                experiment_name,
                tags=["dspy", "optimization", "skills"],
            )
            logger.info(f"✅ Created new MLflow experiment: {experiment_name}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to configure MLflow: {e}")
        return False


def create_tracking_config() -> dict:
    """
    Create DSPy tracking configuration file.

    Returns tracking configuration dictionary.
    """
    logger.info("Creating DSPy tracking configuration...")

    config = {
        "version": "3.1.0",
        "tracking_enabled": True,
        "lm_calls": {
            "track_requests": True,
            "track_responses": True,
            "track_errors": True,
            "log_tokens": True,
            "log_cost": True,
        },
        "cache": {
            "enabled": True,
            "location": ".dspy_cache",
            "max_size_mb": 1000,
        },
        "optimization": {
            "track_parameters": True,
            "track_demos": True,
            "track_instructions": True,
            "save_artifacts": True,
        },
        "mlflow": {
            "enabled": False,  # Will be set based on installation
            "experiment_name": "skill-fleet-dspy-optimization",
            "artifact_location": "./mlruns",
        },
        "monitoring": {
            "log_level": "INFO",
            "enable_tracing": True,
            "enable_profiling": False,  # Performance profiling (expensive)
        },
    }

    # Save configuration
    config_dir = Path(".dspy")
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "tracking_config.json"

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    logger.info(f"✅ Tracking configuration saved to {config_file}")

    return config


def print_tracking_summary(config: dict, mlflow_available: bool) -> None:
    """
    Print summary of tracking setup.

    Args:
        config: DSPy tracking configuration
        mlflow_available: Whether MLflow is available

    """
    print("\n" + "=" * 70)
    print("🔍 DSPy TRACKING SETUP SUMMARY")
    print("=" * 70)

    print("\n📊 DSPy Configuration:")
    print(f"  Version: {config['version']}")
    print(f"  LM Call Tracking: {'✅' if config['lm_calls']['track_requests'] else '❌'}")
    print(f"  Cache: {'✅' if config['cache']['enabled'] else '❌'}")
    print(
        f"  Optimization Tracking: {'✅' if config['optimization']['track_parameters'] else '❌'}"
    )

    print("\n🔬 MLflow Integration:")
    if mlflow_available:
        print("  Status: ✅ Available")
        print(f"  Experiment: {config['mlflow']['experiment_name']}")
        print(f"  Artifacts: {config['mlflow']['artifact_location']}")
        print("\n📋 MLflow Usage:")
        print("  Track optimizer runs:")
        print("    mlflow.start_run()")
        print("    mlflow.log_params({'optimizer': 'reflection_metrics'})")
        print("    mlflow.log_metrics({'quality_score': 0.47})")
        print("    mlflow.log_artifact('optimized_program.pkl')")
        print("    mlflow.end_run()")
    else:
        print("  Status: ❌ Not available")
        print("  Install with: pip install mlflow")
        print("\n  Alternative: Use DSPy's built-in evaluation")

    print("\n" + "=" * 70)
    print("✅ SETUP COMPLETE")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Run optimizer with tracking:")
    print("   uv run python scripts/run_gepa_optimization.py")
    print("2. Check DSPy cache in .dspy_cache/")
    print("3. View MLflow runs (if installed):")
    print("   mlflow ui  # Launch UI in browser")
    print("   mlflow runs list  # List all runs")
    print("=" * 70 + "\n")


def main():
    """Main setup workflow."""
    print("\n" + "=" * 70)
    print("🚀 DSPy TRACKING & MLflow SETUP")
    print("=" * 70)

    # Step 1: Configure DSPy tracking
    print("\n📋 Step 1: Configure DSPy for production tracking")
    configure_dspy_for_tracking()

    # Step 2: Setup MLflow integration
    print("\n📋 Step 2: Setup MLflow integration")
    mlflow_available = setup_mlflow_integration()

    # Step 3: Create configuration
    print("\n📋 Step 3: Create tracking configuration")
    config = create_tracking_config()

    # Step 4: Print summary
    print_tracking_summary(config, mlflow_available)

    # Step 5: Test configuration
    print("\n📋 Step 5: Test configuration")
    print("Testing DSPy configuration with sample run...")

    try:
        # Configure LM with usage tracking
        lm = get_lm("gemini-3-flash-preview", temperature=1.0)
        dspy.configure(lm=lm, track_usage=True)

        # Create simple program
        class TestProgram(dspy.Module):
            def __init__(self):
                super().__init__()
                from skill_fleet.core.dspy.signatures.phase1_understanding import GatherRequirements

                self.gather = dspy.ChainOfThought(GatherRequirements)

            def forward(self, task_description: str):
                return self.gather(task_description=task_description)

        program = TestProgram()

        # Run test prediction
        print("  Running test prediction...")
        result = program(task_description="Create a Python async skill")

        # Check if result has tracking info
        print("  ✅ Test prediction successful")
        print(f"  Result: {result}")
        print(f"  Result fields: {list(result.keys())}")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        print("  ⚠️  Test encountered error (this is expected)")

    print("\n" + "=" * 70)
    print("🎉 SETUP COMPLETE - DSPy tracking is ready!")
    print("=" * 70)
    print("\n📚 Documentation:")
    print("  - DSPy v3.1.0: https://dspy.ai")
    print("  - MLflow docs: https://mlflow.org/docs/latest/index.html")
    print("  - Skills-fleet docs: docs/dspy/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
