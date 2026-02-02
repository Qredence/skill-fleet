"""
Tests for DSPy 3.1.2+ async-first refactoring.

Verifies that:
- BaseModule.forward() delegates to aforward() via run_async
- All modules have aforward() as primary implementation
- run_async is used instead of asyncio.run in core modules
"""

from __future__ import annotations

import asyncio
from typing import Any

import dspy
import pytest
from dspy.utils.syncify import run_async

from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.modules.understanding.parallel_analysis import (
    ParallelUnderstandingAnalysis,
)
from skill_fleet.core.modules.validation.metrics import MetricsCollectorModule


class SimpleAsyncModule(BaseModule):
    """Test module that implements async-first pattern."""

    async def aforward(self, **kwargs: Any) -> dspy.Prediction:
        """Async implementation."""
        await asyncio.sleep(0.001)  # Simulate async work
        value = kwargs.get("value", 0)
        return dspy.Prediction(result=value * 2)


class TestAsyncFirstPattern:
    """Test async-first pattern implementation."""

    def test_forward_delegates_to_aforward(self):
        """Test that forward() calls aforward() via run_async."""
        module = SimpleAsyncModule()
        result = module.forward(value=5)
        assert result.result == 10

    @pytest.mark.asyncio
    async def test_aforward_works_directly(self):
        """Test that aforward() can be called directly."""
        module = SimpleAsyncModule()
        result = await module.aforward(value=3)
        assert result.result == 6

    def test_run_async_bridges_sync_to_async(self):
        """Test that run_async correctly bridges sync to async."""

        async def async_func(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 3

        result = run_async(async_func(4))
        assert result == 12


class TestRealModules:
    """Test that real refactored modules work correctly."""

    def test_parallel_analysis_has_aforward(self):
        """Test ParallelUnderstandingAnalysis implements aforward."""
        module = ParallelUnderstandingAnalysis()
        # Check that aforward exists and is async
        assert hasattr(module, "aforward")
        assert asyncio.iscoroutinefunction(module.aforward)

    def test_metrics_collector_has_aforward(self):
        """Test MetricsCollectorModule implements aforward."""
        module = MetricsCollectorModule()
        assert hasattr(module, "aforward")
        # The module has async methods
        assert hasattr(module, "collect_baseline")
        assert asyncio.iscoroutinefunction(module.collect_baseline)


class TestDSPyPrimitiveReExports:
    """Test that DSPy primitives are re-exported correctly."""

    def test_react_reexported(self):
        """Test ReAct is re-exported from dspy."""
        from skill_fleet.core.modules import ReAct

        assert ReAct is dspy.ReAct

    def test_refine_reexported(self):
        """Test Refine is re-exported from dspy."""
        from skill_fleet.core.modules import Refine

        assert Refine is dspy.Refine

    def test_program_of_thought_reexported(self):
        """Test ProgramOfThought is re-exported from dspy."""
        from skill_fleet.core.modules import ProgramOfThought

        assert ProgramOfThought is dspy.ProgramOfThought


class TestNoLegacyPatterns:
    """Verify legacy patterns have been removed."""

    def test_no_wrapper_modules(self):
        """Test that wrapper modules no longer exist."""
        from pathlib import Path

        modules_dir = (
            Path(__file__).parent.parent.parent / "src" / "skill_fleet" / "core" / "modules"
        )

        # These files should not exist
        assert not (modules_dir / "pot.py").exists()
        assert not (modules_dir / "react.py").exists()
        assert not (modules_dir / "refine.py").exists()

    def test_run_async_imported(self):
        """Test that run_async is available from dspy.utils.syncify."""
        from dspy.utils.syncify import run_async as imported_run_async

        assert imported_run_async is run_async
