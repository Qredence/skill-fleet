"""DSPy module monitoring and tracing infrastructure.

This package provides observability for DSPy modules in production:
- ModuleMonitor: Wrapper for tracking module execution metrics
- ExecutionTracer: Detailed execution tracing with timing and token counts
- MLflowLogger: Optional MLflow integration for experiment tracking

Usage:
    from skill_fleet.core.dspy.monitoring import ModuleMonitor
    
    # Wrap any DSPy module
    monitored = ModuleMonitor(my_module, name="skill_generator")
    result = monitored(input="test")
    
    # Check metrics
    print(monitored.get_metrics())
"""

from __future__ import annotations

from .module_monitor import ModuleMonitor
from .execution_tracer import ExecutionTracer, TraceEntry
from .mlflow_logger import MLflowLogger, configure_mlflow

__all__ = [
    "ModuleMonitor",
    "ExecutionTracer",
    "TraceEntry",
    "MLflowLogger",
    "configure_mlflow",
]
