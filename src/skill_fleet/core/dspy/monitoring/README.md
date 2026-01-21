# DSPy Module Monitoring & Tracing

Production-ready observability for DSPy modules in skills-fleet.

## Components

### 1. ModuleMonitor
Wraps any DSPy module for automatic monitoring.

**Features:**
- Execution timing and success rate tracking
- Input/output logging with configurable verbosity
- Quality scoring integration
- Error tracking with stack traces
- Thread-safe for concurrent executions

**Usage:**
```python
from skill_fleet.core.dspy.monitoring import ModuleMonitor

# Wrap any DSPy module
generator = dspy.ChainOfThought("task -> output")
monitored = ModuleMonitor(
    generator,
    name="skill_generator",
    quality_metric=lambda x: score_quality(x.output),
)

# Use normally
result = monitored(task="Create a Python async skill")

# Access metrics
metrics = monitored.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Avg duration: {metrics['avg_duration_ms']:.1f}ms")
print(f"Avg quality: {metrics['avg_quality_score']:.3f}")
```

### 2. ExecutionTracer
Detailed execution tracing for debugging and analysis.

**Features:**
- Per-execution trace entries
- Timing and token usage tracking
- Quality score history
- Validation error tracking
- Export to JSON for analysis

**Usage:**
```python
from skill_fleet.core.dspy.monitoring import ExecutionTracer

tracer = ExecutionTracer(max_traces=1000)

# Automatic tracing with context manager
with tracer.trace("my_module", inputs={"query": "test"}) as trace:
    result = module(query="test")
    trace.outputs = {"result": str(result)}
    trace.quality_score = 0.85

# Get aggregate metrics
metrics = tracer.get_metrics()
print(f"Total executions: {metrics['total_executions']}")
print(f"Success rate: {metrics['success_rate']:.2%}")

# Export traces for analysis
tracer.export_traces("execution_history.json")
```

### 3. MLflowLogger (Optional)
Integration with MLflow for experiment tracking.

**Features:**
- Track optimization runs
- Log parameters, metrics, and artifacts
- Model versioning
- Compare experiments

**Usage:**
```python
from skill_fleet.core.dspy.monitoring import configure_mlflow, MLflowLogger

# One-time setup
configure_mlflow(experiment_name="skill-optimization")

# Track optimization run
with MLflowLogger(run_name="miprov2_v1") as logger:
    # Log configuration
    logger.log_params({
        "optimizer": "MIPROv2",
        "auto": "medium",
        "trainset_size": 50,
    })
    
    # Run optimization
    optimized = optimizer.compile(program, trainset=trainset)
    
    # Log results
    logger.log_metrics({
        "quality_score": 0.85,
        "examples_used": 50,
        "optimization_time_s": 120,
    })
    
    # Save artifacts
    logger.log_artifact("optimized_program.pkl")
    logger.log_dict(results, "optimization_results.json")
```

## Integration Examples

### Monitoring Phase 2 Generation

```python
from skill_fleet.core.dspy.monitoring import ModuleMonitor, ExecutionTracer
from skill_fleet.core.dspy.modules.phase2_generation import GenerateSkillContentModule

# Create shared tracer
tracer = ExecutionTracer()

# Wrap generator module
generator = GenerateSkillContentModule()
monitored_generator = ModuleMonitor(
    generator,
    name="skill_content_generator",
    tracer=tracer,
    quality_metric=lambda x: score_skill_quality(x.skill_content),
)

# Use in workflow
for task in tasks:
    result = monitored_generator(
        skill_metadata=task.metadata,
        content_plan=task.plan,
    )
    
    # Metrics automatically tracked
    print(f"Generated skill in {tracer.get_traces(limit=1)[0].duration_ms:.0f}ms")
```

### Optimization Tracking with MLflow

```python
from skill_fleet.core.dspy.monitoring import configure_mlflow, MLflowLogger

# Configure once at startup
configure_mlflow(
    tracking_uri="http://localhost:5000",  # Or None for local
    experiment_name="skill-fleet-optimization",
)

# Track optimization runs
def optimize_with_tracking(program, trainset, config):
    with MLflowLogger(run_name=f"optimization_{config['optimizer']}") as logger:
        # Log configuration
        logger.log_params(config)
        logger.set_tags({"phase": "optimization", "model": config["model"]})
        
        # Run optimization
        optimizer = create_optimizer(config)
        optimized = optimizer.compile(program, trainset=trainset)
        
        # Evaluate and log metrics
        eval_results = evaluate(optimized, testset)
        logger.log_metrics(eval_results)
        
        # Save optimized program
        import pickle
        with open("optimized.pkl", "wb") as f:
            pickle.dump(optimized, f)
        logger.log_artifact("optimized.pkl")
        
        return optimized
```

## Configuration

### Environment Variables

```bash
# MLflow tracking URI (optional)
export MLFLOW_TRACKING_URI=http://localhost:5000

# MLflow experiment name
export MLFLOW_EXPERIMENT_NAME=skill-fleet-optimization

# Monitoring log level
export MONITORING_LOG_LEVEL=INFO
```

### Logging Configuration

```python
import logging

# Configure monitoring logger
logging.getLogger("skill_fleet.core.dspy.monitoring").setLevel(logging.INFO)

# Configure module-specific loggers
logging.getLogger("skill_fleet.core.dspy.monitoring.skill_generator").setLevel(logging.DEBUG)
```

## Performance Considerations

### Memory Management
- `ExecutionTracer` uses FIFO eviction (default: 1000 traces)
- Configure `max_traces` based on available memory
- Export traces periodically for long-running processes

### Logging Overhead
- Input/output logging adds ~5-10ms per execution
- Disable with `log_inputs=False`, `log_outputs=False` if needed
- Quality metrics add additional overhead (depends on metric)

### MLflow Performance
- Asynchronous logging reduces overhead
- Local tracking is faster than remote servers
- Batch artifact uploads when possible

## Best Practices

### 1. Use Shared Tracers
```python
# ✅ Good: Share tracer across modules
tracer = ExecutionTracer()
module1 = ModuleMonitor(mod1, name="phase1", tracer=tracer)
module2 = ModuleMonitor(mod2, name="phase2", tracer=tracer)

# ❌ Bad: Separate tracers lose correlation
module1 = ModuleMonitor(mod1, name="phase1")  # New tracer
module2 = ModuleMonitor(mod2, name="phase2")  # Another new tracer
```

### 2. Set Appropriate Log Levels
```python
# ✅ Good: INFO for production, DEBUG for development
ModuleMonitor(module, name="generator", log_level=logging.INFO)

# ⚠️ Caution: DEBUG can be very verbose
ModuleMonitor(module, name="generator", log_level=logging.DEBUG)
```

### 3. Export Metrics Regularly
```python
# ✅ Good: Periodic exports prevent memory growth
if execution_count % 100 == 0:
    tracer.export_traces(f"traces_{execution_count}.json")
    tracer.clear()  # Free memory after export
```

### 4. Use MLflow for Experiments Only
```python
# ✅ Good: MLflow for optimization and evaluation
with MLflowLogger(run_name="experiment_1"):
    run_optimization()

# ❌ Bad: MLflow for every production request (too slow)
for request in production_requests:
    with MLflowLogger():  # Don't do this
        handle_request(request)
```

## Troubleshooting

### "MLflow not available" Warning
```bash
# Install MLflow (optional dependency)
pip install mlflow
```

### High Memory Usage
```python
# Reduce max_traces
tracer = ExecutionTracer(max_traces=100)  # Default: 1000

# Or export and clear regularly
if len(tracer._traces) > 500:
    tracer.export_traces("backup.json")
    tracer.clear()
```

### Slow Performance
```python
# Disable input/output logging
ModuleMonitor(module, name="fast", log_inputs=False, log_outputs=False)

# Or remove quality metric
ModuleMonitor(module, name="fast", quality_metric=None)
```

## API Reference

See docstrings in source files for complete API documentation:
- `execution_tracer.py`: TraceEntry, ExecutionTracer
- `module_monitor.py`: ModuleMonitor
- `mlflow_logger.py`: MLflowLogger, configure_mlflow
