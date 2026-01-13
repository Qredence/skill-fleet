from pathlib import Path

from skill_fleet.core.optimization import WorkflowOptimizer


def test_optimizer_cache_hits_and_misses(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    optimizer = WorkflowOptimizer(cache_dir)

    inputs = {"task": "example", "step": 1}
    assert optimizer.get_cached("step_one", inputs) is None

    optimizer.cache_result("step_one", inputs, {"ok": True})
    cached = optimizer.get_cached("step_one", inputs)

    assert cached == {"ok": True}

    stats = optimizer.get_cache_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["cache_size"] == 1


def test_optimizer_clear_cache(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    optimizer = WorkflowOptimizer(cache_dir)

    optimizer.cache_result("step_one", {"task": "a"}, {"ok": True})
    optimizer.cache_result("step_two", {"task": "b"}, {"ok": False})

    assert optimizer.get_cache_stats()["cache_size"] == 2

    optimizer.clear_cache()

    assert optimizer.get_cache_stats()["cache_size"] == 0
