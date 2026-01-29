# MLflow Setup for DSPy Autologging

**Last Updated**: 2026-01-25

## Quick Start

### 1. Start MLflow UI Server

```bash
# Option 1: Simple start (default)
./scripts/start-mlflow.sh

# Option 2: External access (port 5001, recommended)
./scripts/start-mlflow-public.sh

# Option 3: Custom configuration
uv run mlflow ui \
    --host localhost \
    --port 5001 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts
```

**Note:** Port 5000 is often used by macOS AirPlay/ControlCenter. Use port 5001 if needed.

### 2. Open MLflow UI

Navigate to: **http://localhost:5001**

**Note:** If port 5001 doesn't work, check:
```bash
# See what's using port 5001
lsof -i :5001

# Try alternative ports
uv run mlflow ui --port 5002
```

### 3. Test DSPy Autologging

```bash
# Run the test script
uv run python scripts/test_mlflow_tracking.py

# Check the run in MLflow UI
# Experiment: "skill-fleet-test"
# Run: "test-dspy-tracking"
```

---

## What Gets Tracked

With `mlflow.dspy.autolog()` enabled (DSPy 3.1.2+), MLflow automatically tracks:

### DSPy Operations
- **Module calls**: Every DSPy module invocation
- **Signatures**: Input/output for each signature
- **LM calls**: Language model requests and responses
- **Parameters**: Model settings, temperature, max_tokens
- **Metrics**: Performance metrics and evaluation scores

### Hierarchical Runs (NEW)
Skill creation workflows now use **parent-child run hierarchies**:

```
skill_creation_job_abc123 (parent)
├── understanding (child)
│   ├── LM calls: 5
│   ├── Tokens: 2,340
│   └── Duration: 12.3s
├── generation (child)
│   ├── LM calls: 3
│   ├── Tokens: 1,890
│   └── Duration: 8.7s
└── validation (child)
    ├── Quality score: 0.85
    ├── Tokens: 456
    └── Duration: 3.2s
```

### Tag Organization (ENHANCED)
Runs are automatically tagged with:

| Tag | Description | Example |
|-----|-------------|---------|
| `user_id` | User who initiated the job | `user_123` |
| `job_id` | Unique job identifier | `job_abc123` |
| `skill_type` | Type of skill being created | `guide`, `tool_integration` |
| `model` | LLM model used | `gemini-3-flash` |
| `phase` | Current workflow phase | `understanding`, `generation`, `validation` |
| `service` | Service creating the run | `SkillService` |

### Complete Artifact Logging (ENHANCED)
All skill artifacts are automatically logged:

| Artifact | Description | Location |
|----------|-------------|----------|
| `skill_content.md` | Generated SKILL.md content | Artifacts/ |
| `metadata.json` | Skill metadata | Artifacts/ |
| `validation_report.json` | Quality validation results | Artifacts/ |
| `conversation_history.json` | HITL conversation transcript | Artifacts/ |

### LM Usage Tracking (DSPy 3.1.2)
DSPy 3.1.2 provides complete LM usage tracking:

```python
# Automatically tracked metrics
mlflow.log_metric("lm_calls", 15)           # Total LM calls
mlflow.log_metric("lm_tokens_total", 5432)  # Total tokens used
mlflow.log_metric("lm_tokens_input", 2341)  # Input tokens
mlflow.log_metric("lm_tokens_output", 3091) # Output tokens
mlflow.log_metric("lm_duration", 45.2)      # Total LM time (seconds)
```

### Optimization Workflows
- **MIPROv2**: Prompt optimization iterations
- **GEPA**: Reflection cycles and improvements
- **BootstrapFewShot**: Few-shot example selection
- **Evaluation**: Metric scores and comparisons

### Custom Tags
You can add custom tags for filtering:
```python
with MLflowContext(
    run_name="skill-creation",
    tags={"phase": "generation", "skill_type": "python"}
):
    result = program.forward(...)
```

---

## Using MLflow During Development

### Track Skill Creation Workflows (ENHANCED)

```python
from skill_fleet.services.monitoring import MLflowContext, setup_dspy_autologging

# Setup at application startup
setup_dspy_autologging(experiment_name="skill-creation")

# Parent run for the entire skill creation job
with mlflow.start_run(run_name=f"skill_creation_{job_id}") as parent_run:
    # Parent-level tags
    mlflow.set_tag("user_id", user_id)
    mlflow.set_tag("job_id", job_id)
    mlflow.set_tag("service", "SkillService")

    # Child run for Phase 1: Understanding
    with mlflow.start_run(run_name="understanding", nested=True):
        mlflow.set_tag("phase", "understanding")
        result = understanding_program.forward(...)
        # LM metrics auto-logged by DSPy 3.1.2

    # Child run for Phase 2: Generation
    with mlflow.start_run(run_name="generation", nested=True):
        mlflow.set_tag("phase", "generation")
        result = generation_program.forward(...)
        # Artifacts auto-logged
        mlflow.log_text(content, "skill_content.md")

    # Child run for Phase 3: Validation
    with mlflow.start_run(run_name="validation", nested=True):
        mlflow.set_tag("phase", "validation")
        report = validate_skill(result.skill)
        mlflow.log_dict(report.to_dict(), "validation_report.json")
        mlflow.log_metric("quality_score", report.score)
```

### Compare Optimizers

```python
# MIPROv2
with MLflowContext(run_name="miprov2-run", tags={"optimizer": "miprov2"}):
    optimized = teleprompter.compile(program, trainset)

# GEPA
with MLflowContext(run_name="gepa-run", tags={"optimizer": "gepa"}):
    optimized = teleprompter.compile(program, trainset)

# Compare in MLflow UI side-by-side
```

### Track Evaluation Metrics

```python
from dspy.evaluate import Evaluate

# Metrics are automatically logged with autologging
evaluator = Evaluate(
    metric=your_metric,
    devset=dev_set,
    num_threads=4,
)

evaluator(program)
# All results automatically tracked in MLflow!
```

---

## MLflow UI Features

### Experiments Page
- View all experiments
- Compare runs across experiments
- Filter by tags and parameters

### Run Details
- **Parameters**: LLM settings, model info
- **Metrics**: DSPy performance scores
- **Artifacts**: Saved models, prompts, plots
- **Traces**: Detailed execution timeline

### Comparing Runs
- Select multiple runs
- View metrics side-by-side
- Compare parameters
- Visualize performance differences

---

## Troubleshooting

### MLflow UI Won't Start
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill existing MLflow process
killall mlflow

# Use different port
uv run mlflow ui --port 5001
```

### Can't See Runs in UI
```bash
# Verify backend store
ls -la mlflow.db

# Check if runs exist
sqlite3 mlflow.db "SELECT run_uuid, status FROM runs ORDER BY start_time DESC LIMIT 5;"

# Reset (WARNING: deletes all data)
rm mlflow.db
```

### DSPy Autologging Not Working
```python
# Verify DSPy version
uv run python -c "import dspy; print(dspy.__version__)"
# Should be 3.1.2+

# Check if MLflow autologging is enabled
import mlflow
mlflow.dspy.autolog()  # Should return None (no error)

# Verify experiment
import mlflow
mlflow.set_experiment("test")
print("Experiment set successfully")
```

---

## Advanced Configuration

### Remote MLflow Server

```python
# Setup for remote tracking
setup_dspy_autologging(
    tracking_uri="http://your-mlflow-server:5000",
    experiment_name="skill-creation-prod"
)
```

### Custom Artifact Location

```python
# Run with custom artifact root
with MLflowContext(
    run_name="my-run",
    tags={"artifact_type": "model"}
):
    # Artifacts saved to: ./mlartifacts/<run_uuid>/
    result = program.forward(...)
```

### Environment Variables

```bash
# MLflow configuration
export MLFLOW_TRACKING_URI=http://localhost:5000
export MLFLOW_EXPERIMENT_NAME=skill-creation
export MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow.db
```

---

## Best Practices

1. **One Experiment Per Project**: Use descriptive experiment names (e.g., "skill-creation", "optimization")

2. **Descriptive Run Names**: Include what you're testing
   ```python
   run_name="miprov2-skill-creation-python-decorators"
   ```

3. **Use Tags for Filtering**:
   ```python
   tags={
       "phase": "generation",
       "optimizer": "miprov2",
       "model": "gemini-3-flash"
   }
   ```

4. **Log Parameters Manually** (if needed):
   ```python
   mlflow.log_param("temperature", 0.7)
   mlflow.log_param("max_tokens", 4096)
   ```

5. **Log Metrics Manually** (if needed):
   ```python
   mlflow.log_metric("quality_score", 0.85)
   mlflow.log_metric("validation_passed", 1)
   ```

---

## Files Created

- ✅ `scripts/start-mlflow.sh`: MLflow UI starter script
- ✅ `scripts/test_mlflow_tracking.py`: DSPy autologging test
- ✅ `src/skill_fleet/services/monitoring/mlflow_setup.py`: MLflow integration utilities

---

## Next Steps

1. **Start MLflow UI**: `./scripts/start-mlflow.sh`
2. **Run skill creation**: Your DSPy workflows will be automatically tracked
3. **View results**: Check http://localhost:5000
4. **Compare runs**: Use MLflow UI to compare different configurations

Happy tracking! 🚀
