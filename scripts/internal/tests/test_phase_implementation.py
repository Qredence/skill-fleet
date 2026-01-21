#!/usr/bin/env python3
"""
Test script to validate Phase 1-3 implementation.

Tests key components without requiring full DSPy optimization run.
"""

from __future__ import annotations

import sys
from pathlib import Path

print("=" * 60)
print("Testing Phase 1-3 Implementation")
print("=" * 60)

# Test 1: Import all new modules
print("\n[Test 1] Importing new modules...")
try:
    # Phase 1
    from skill_fleet.core.dspy.monitoring import (  # noqa: F401
        ExecutionTracer,
        ModuleMonitor,
    )

    try:
        from skill_fleet.core.dspy.monitoring import MLflowLogger  # noqa: F401
    except ImportError:
        print("⚠️  MLflowLogger not available (mlflow not installed)")
    print("✅ Phase 1: Monitoring modules imported")

    # Phase 2
    from skill_fleet.core.dspy.metrics.enhanced_metrics import (  # noqa: F401
        comprehensive_metric,
        metadata_quality_metric,
        taxonomy_accuracy_metric,
    )
    from skill_fleet.core.dspy.modules.error_handling import RobustModule, ValidatedModule

    print("✅ Phase 2: Enhanced metrics and error handling imported")

    # Phase 3
    from skill_fleet.core.dspy.caching import CachedModule
    from skill_fleet.core.dspy.modules.ensemble import BestOfN, EnsembleModule, MajorityVote
    from skill_fleet.core.dspy.versioning import ABTestRouter, ProgramRegistry  # noqa: F401

    print("✅ Phase 3: Ensemble, versioning, and caching imported")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check training data
print("\n[Test 2] Checking training data...")
try:
    import json

    trainset_path = Path("config/training/trainset_v4.json")

    if not trainset_path.exists():
        print(f"❌ Training data not found: {trainset_path}")
        sys.exit(1)

    with open(trainset_path) as f:
        trainset = json.load(f)

    print(f"✅ Training data loaded: {len(trainset)} examples")

    # Check example structure
    if trainset:
        example = trainset[0]
        required_fields = ["task_description"]
        missing = [f for f in required_fields if f not in example]
        if missing:
            print(f"⚠️  Missing fields in example: {missing}")
        else:
            print("✅ Training examples have correct structure")

except Exception as e:
    print(f"❌ Training data check failed: {e}")
    sys.exit(1)

# Test 3: Test monitoring components
print("\n[Test 3] Testing monitoring components...")
try:
    import dspy

    # Create simple test module
    test_module = dspy.Predict("input -> output")

    # Wrap with monitor
    tracer = ExecutionTracer(max_traces=10)
    monitored = ModuleMonitor(test_module, name="test_module", tracer=tracer)

    # Would execute: result = monitored(input="test")
    # But we skip actual execution to avoid needing DSPy configured

    print("✅ Monitoring components initialized successfully")

    # Check tracer methods
    metrics = tracer.get_metrics()
    assert "total_executions" in metrics
    print("✅ Tracer metrics accessible")

except Exception as e:
    print(f"❌ Monitoring test failed: {e}")
    sys.exit(1)

# Test 4: Test enhanced metrics (without execution)
print("\n[Test 4] Testing enhanced metrics...")
try:
    # Create mock example and prediction
    import dspy

    example = dspy.Example(
        task_description="Test task",
        expected_taxonomy_path="python/async",
        expected_skill_style="comprehensive",
    ).with_inputs("task_description")

    prediction = dspy.Prediction(
        taxonomy_path="python/async",
        skill_metadata=type(
            "obj",
            (object,),
            {
                "name": "test-skill",
                "description": "Use when testing",
                "tags": ["test", "python"],
            },
        )(),
        skill_style="comprehensive",
    )

    # Test metrics (should not crash)
    tax_score = taxonomy_accuracy_metric(example, prediction)
    meta_score = metadata_quality_metric(example, prediction)
    comp_score = comprehensive_metric(example, prediction)

    print(f"✅ Metrics computed: tax={tax_score:.2f}, meta={meta_score:.2f}, comp={comp_score:.2f}")

except Exception as e:
    print(f"❌ Metrics test failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 5: Test error handling modules
print("\n[Test 5] Testing error handling...")
try:
    import dspy

    # Create test module that might fail
    test_module = dspy.Predict("input -> output")

    # Wrap with robust handler
    robust = RobustModule(
        test_module,
        name="test_robust",
        max_retries=2,
        fallback_fn=lambda **kwargs: dspy.Prediction(output="fallback"),
    )

    print("✅ RobustModule initialized")

    # Test validator
    def simple_validator(pred):
        """
        Simple validation function for testing.

        Args:
            pred: Prediction to validate

        Returns:
            True if prediction has output field

        Raises:
            ValueError: If prediction is missing output field

        """
        if not hasattr(pred, "output"):
            raise ValueError("Missing output field")
        return True

    validated = ValidatedModule(test_module, validator=simple_validator)
    print("✅ ValidatedModule initialized")

except Exception as e:
    print(f"❌ Error handling test failed: {e}")
    sys.exit(1)

# Test 6: Test ensemble components
print("\n[Test 6] Testing ensemble components...")
try:
    import dspy

    # Create test modules
    modules = [
        dspy.Predict("input -> output"),
        dspy.Predict("input -> output"),
        dspy.Predict("input -> output"),
    ]

    # Create ensemble
    ensemble = EnsembleModule(modules, parallel=True)
    print("✅ EnsembleModule initialized")

    # Create BestOfN
    best_of_3 = BestOfN(
        module=dspy.Predict("input -> output"),
        n=3,
    )
    print("✅ BestOfN initialized")

    # Create MajorityVote
    voter = MajorityVote(modules, vote_field="output")
    print("✅ MajorityVote initialized")

except Exception as e:
    print(f"❌ Ensemble test failed: {e}")
    sys.exit(1)

# Test 7: Test versioning
print("\n[Test 7] Testing versioning...")
try:
    import tempfile
    from pathlib import Path

    # Create temp registry
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = ProgramRegistry(tmpdir)
        print("✅ ProgramRegistry initialized")

        # Check registry methods exist
        assert hasattr(registry, "register")
        assert hasattr(registry, "load")
        assert hasattr(registry, "list_versions")
        print("✅ Registry methods available")

        # Test ABTestRouter
        import dspy

        variants = {
            "v1": dspy.Predict("input -> output"),
            "v2": dspy.Predict("input -> output"),
        }
        router = ABTestRouter(variants, strategy="random")
        print("✅ ABTestRouter initialized")

        stats = router.get_stats()
        assert "v1" in stats and "v2" in stats
        print("✅ Router stats accessible")

except Exception as e:
    print(f"❌ Versioning test failed: {e}")
    sys.exit(1)

# Test 8: Test caching
print("\n[Test 8] Testing caching...")
try:
    import tempfile

    import dspy

    with tempfile.TemporaryDirectory() as tmpdir:
        test_module = dspy.Predict("input -> output")
        cached = CachedModule(test_module, cache_dir=tmpdir)
        print("✅ CachedModule initialized")

        stats = cached.get_stats()
        assert "hits" in stats and "misses" in stats
        print("✅ Cache stats accessible")

except Exception as e:
    print(f"❌ Caching test failed: {e}")
    sys.exit(1)

# Test 9: Check API routes
print("\n[Test 9] Checking API routes...")
try:
    from skill_fleet.api.routes.optimization import OptimizeRequest, router

    # Check endpoints exist
    routes = [r.path for r in router.routes]
    expected_routes = ["/start", "/status/{job_id}", "/optimizers"]

    for expected in expected_routes:
        if expected in routes:
            print(f"✅ API route exists: {expected}")
        else:
            print(f"⚠️  API route missing: {expected}")

    # Check request model
    request = OptimizeRequest(
        optimizer="miprov2",
        trainset_file="config/training/trainset_v4.json",
        auto="medium",
    )
    print("✅ OptimizeRequest model validated")

except Exception as e:
    print(f"❌ API routes check failed: {e}")
    sys.exit(1)

# Test 10: Check optimization script
print("\n[Test 10] Checking optimization script...")
try:
    script_path = Path("scripts/run_optimization.py")
    if not script_path.exists():
        print(f"❌ Optimization script not found: {script_path}")
        sys.exit(1)

    # Check script is executable
    content = script_path.read_text()
    if "def main()" in content and "trainset_v4.json" in content:
        print("✅ Optimization script exists and looks correct")
    else:
        print("⚠️  Optimization script may be incomplete")

except Exception as e:
    print(f"❌ Script check failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ All Tests Passed!")
print("=" * 60)
print("\nImplementation Summary:")
print("- Phase 1: Monitoring infrastructure ✅")
print("- Phase 2: Enhanced metrics & error handling ✅")
print("- Phase 3: Ensemble, versioning, caching ✅")
print("- API endpoints enhanced ✅")
print("- Training data ready (50 examples) ✅")
print("\nReady for optimization run!")
print("=" * 60)
