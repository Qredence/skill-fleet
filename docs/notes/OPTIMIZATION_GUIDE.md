# DSPy Optimization Guide for Skills-Fleet

**Last Updated**: January 19, 2026  
**Status**: Production Ready ✅

## Quick Start

### Run Baseline + Optimization

```bash
# Execute optimization with BootstrapFewShot (fastest)
uv run python scripts/run_optimization.py

# Expected output:
#   Baseline score: 80.0
#   Optimized score: 80.0-85.0
#   Results saved to: config/optimized/
```

### Optimization Script Features

The `scripts/run_optimization.py` script provides:
- **Training data loading** from `config/training/trainset_v4.json` (50 examples)
- **Train/test split** (80/20 by default)
- **Baseline evaluation** before optimization
- **Multiple optimizer support**: BootstrapFewShot, MIPROv2, GEPA
- **Result tracking** with JSON reports
- **Program serialization** (when possible)

## Optimizer Selection

### Quick Decision Matrix

| Optimizer | Speed | Quality | Cost | Best For |
|-----------|-------|---------|------|----------|
| **BootstrapFewShot** | ⚡ Fast | ⭐⭐ Good | 💰 Cheap | Quick baselines, testing |
| **MIPROv2** | 🐢 Slow | ⭐⭐⭐ Excellent | 💵 Medium | Production optimization |
| **GEPA** | 🚀 Very Fast | ⭐⭐ Good | 💵 Medium | Reflection-based improvement |

### Optimizer Details

#### 1. BootstrapFewShot (Recommended for Testing)

**When to use**: Quick iteration, testing, baseline establishment

```python
optimizer = dspy.BootstrapFewShot(
    metric=your_metric,
    max_bootstrapped_demos=2,      # Few-shot examples
    max_labeled_demos=1,            # Labeled examples from data
)
optimized = optimizer.compile(program, trainset=trainset)
```

**Characteristics**:
- ✅ Simplest to use
- ✅ No additional LM needed
- ✅ Fastest execution
- ⚠️ Lower quality improvements (5-10%)

#### 2. MIPROv2 (Recommended for Production)

**When to use**: Maximum quality, production systems, thorough optimization

```python
optimizer = dspy.MIPROv2(
    metric=your_metric,
    auto="medium",                  # light, medium, heavy
    num_threads=8,                  # Parallel optimization
)
optimized = optimizer.compile(
    program,
    trainset=trainset,
    max_bootstrapped_demos=2,
    max_labeled_demos=2,
    num_candidate_programs=16,
)
```

**Characteristics**:
- ✅ Best quality improvements (15-25%)
- ✅ Systematic search over instructions + demos
- ⚠️ Slower execution (10-30 minutes typical)
- ⚠️ Higher cost (depends on `auto` setting)

**Budget Modes**:
- `"light"`: ~5 min, ~$2-5, good for testing
- `"medium"`: ~15 min, ~$10-15, recommended default
- `"heavy"`: ~30 min, ~$20-30, maximum quality

#### 3. GEPA (Recommended for Reflection-Based Optimization)

**When to use**: When you have rich feedback, prefer reflection-based optimization

```python
# Important: GEPA requires a reflection LM
reflection_lm = dspy.LM(model='gpt-4o', temperature=1.0, max_tokens=32000)

def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """GEPA metric must accept 5 parameters."""
    score = your_simple_metric(gold, pred, trace)
    feedback = f"Score: {score:.2f}"  # Optional: add rich feedback
    return {"score": score, "feedback": feedback}

optimizer = dspy.GEPA(
    metric=gepa_metric,
    reflection_lm=reflection_lm,
    auto="light",                   # light, medium, heavy
)
optimized = optimizer.compile(program, trainset=trainset)
```

**Characteristics**:
- ✅ Good quality improvements (10-15%)
- ✅ Reflection-based (LLM analyzes failures)
- ✅ Supports rich textual feedback
- ⚠️ Requires a reflection LM

## Metric Design

### Basic Metric (Works with All Optimizers)

```python
def simple_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """
    Simple metric returns 0.0-1.0 score.
    
    Args:
        example: Gold example with expected outputs
        prediction: Model's prediction
        trace: Execution trace (optional)
    
    Returns:
        float: Score between 0.0 and 1.0
    """
    score = 0.0
    
    # Check quality dimensions
    if hasattr(prediction, "field1") and prediction.field1:
        score += 0.25
    if hasattr(prediction, "field2") and prediction.field2:
        score += 0.25
    if hasattr(prediction, "field3") and prediction.field3:
        score += 0.25
    if hasattr(prediction, "field4") and prediction.field4:
        score += 0.25
    
    return score
```

### GEPA-Enhanced Metric (With Feedback)

```python
def gepa_metric(gold, pred, trace=None, pred_name=None, pred_trace=None):
    """
    GEPA metric with optional feedback.
    
    Args:
        gold: Gold example
        pred: Prediction
        trace: Full execution trace
        pred_name: Name of predictor being optimized (GEPA-specific)
        pred_trace: Trace of specific predictor (GEPA-specific)
    
    Returns:
        dict: {"score": float, "feedback": str}
    """
    score = simple_metric(gold, pred, trace)
    
    # Optional: Add feedback for GEPA's reflection
    feedback = ""
    if not hasattr(pred, "field1") or not pred.field1:
        feedback += "Missing field1. "
    if score < 0.5:
        feedback += "Score below threshold. "
    
    return {
        "score": score,
        "feedback": feedback or "Good performance"
    }
```

## Training Data Requirements

### Minimum Size
- **BootstrapFewShot**: 10-50 examples (can work with less)
- **MIPROv2**: 50-500 examples (recommended 100+)
- **GEPA**: 20-100 examples

### Quality Guidelines
1. **Diversity**: Cover different scenarios and edge cases
2. **Correctness**: Examples should have correct expected outputs
3. **Balance**: Mix easy and hard examples
4. **Distribution**: Match your production distribution

### Current Training Data

Located at: `config/training/trainset_v4.json`

```
✅ 50 examples (meets DSPy 50-100 recommendation)
✅ 19 different categories
✅ 3 skill styles: comprehensive (38), navigation_hub (11), minimal (1)
✅ 3 sources: synthetic (26), golden (15), extracted (9)
```

## Running Optimization

### Command Line

```bash
# With default BootstrapFewShot
uv run python scripts/run_optimization.py

# Expected output:
# ============================================================
# Phase 2: DSPy Optimization with Expanded Training Data
# ============================================================
# 
# Baseline Evaluation (before optimization)
# Evaluating on 10 test examples...
# Evaluation score: 80.000
# 
# Running Optimization
# Running BootstrapFewShot optimization (fastest)...
# ✅ Optimization complete!
# 
# Post-Optimization Evaluation
# Evaluating on 10 test examples...
# Evaluation score: 80.000
# 
# ============================================================
# Optimization Results Summary
# ============================================================
# Training examples: 40
# Test examples: 10
# Baseline score: 80.000
# Optimized score: 80.000
# Improvement: +0.000 (+0.0%)
# 
# ✅ Results saved to: config/optimized/optimization_results_bootstrap_v1.json
```

### Programmatic Usage

```python
import dspy
from skill_fleet.core.dspy.metrics.skill_quality import skill_quality_metric
from skill_fleet.core.optimization.optimizer import get_lm

# 1. Configure LM
lm = get_lm("gemini-3-flash-preview", temperature=1.0)
dspy.configure(lm=lm)

# 2. Load training data
import json
with open("config/training/trainset_v4.json") as f:
    data = json.load(f)

examples = [
    dspy.Example(
        task_description=item["task_description"],
        expected_taxonomy_path=item.get("expected_taxonomy_path", ""),
    ).with_inputs("task_description")
    for item in data
]

# 3. Create program
class SimpleProgram(dspy.Module):
    def __init__(self):
        super().__init__()
        self.cot = dspy.ChainOfThought("task_description -> output")
    
    def forward(self, task_description: str):
        return self.cot(task_description=task_description)

program = SimpleProgram()

# 4. Define metric
def metric(example, pred, trace=None):
    return 0.8  # Placeholder

# 5. Optimize
optimizer = dspy.BootstrapFewShot(metric=metric)
optimized = optimizer.compile(program, trainset=examples)
```

## Results Interpretation

### Output Files

After running optimization, check:

```
config/optimized/
├── optimization_results_bootstrap_v1.json    # Results summary
├── skill_program_bootstrap_v1.pkl           # Optimized program (if serialized)
└── ...
```

### Results JSON

```json
{
  "optimizer": "BootstrapFewShot",
  "trainset_size": 40,
  "testset_size": 10,
  "baseline_score": 80.0,
  "optimized_score": 85.0,
  "improvement": 5.0,
  "improvement_percent": 6.25
}
```

### Interpreting Scores

- **No improvement** (0%): Metric may be too simple or data not representative
- **Small improvement** (5-10%): Typical with BootstrapFewShot
- **Good improvement** (15-25%): Typical with MIPROv2
- **Great improvement** (>25%): Excellent results, consider production deployment

## Advanced Optimization

### Multi-Stage Optimization

```python
# Stage 1: Quick baseline with BootstrapFewShot
optimizer1 = dspy.BootstrapFewShot(metric=metric)
program_v1 = optimizer1.compile(program, trainset=trainset)

# Stage 2: Further optimize with MIPROv2
optimizer2 = dspy.MIPROv2(metric=metric, auto="light")
program_v2 = optimizer2.compile(program_v1, trainset=trainset)

# Stage 3: Heavy optimization if needed
optimizer3 = dspy.MIPROv2(metric=metric, auto="heavy")
program_v3 = optimizer3.compile(program_v2, trainset=trainset)
```

### Ensemble Optimization Results

```python
# Combine multiple optimized versions
ensemble = dspy.Module()
ensemble.programs = [program_v1, program_v2, program_v3]

def ensemble_forward(input):
    results = [p(input) for p in ensemble.programs]
    # Custom selection logic
    return select_best(results)
```

### Validation with Separate Test Set

```python
# Split data properly
train_examples = trainset[:80]
test_examples = trainset[80:]

# Optimize on train
optimizer = dspy.MIPROv2(metric=metric, auto="medium")
optimized = optimizer.compile(program, trainset=train_examples)

# Evaluate on separate test
from dspy.evaluate import Evaluate

evaluator = Evaluate(devset=test_examples, metric=metric)
test_score = evaluator(optimized)

print(f"Train performance: {train_score:.2%}")
print(f"Test performance: {test_score:.2%}")
```

## Troubleshooting

### Issue: "No improvement detected"

**Possible causes**:
1. Metric is too simple or permissive
2. Training data not representative
3. Program already near-optimal
4. Insufficient training data

**Solutions**:
- Review metric design for stricter evaluation
- Expand training data with diverse examples
- Check if baseline is already high (>90%)
- Try MIPROv2 instead of BootstrapFewShot

### Issue: "Optimization runs very slowly"

**Possible causes**:
1. Using MIPROv2 with `auto="heavy"`
2. Very large training set
3. Complex program with many modules

**Solutions**:
- Use MIPROv2 `auto="light"` instead
- Reduce trainset to 50-100 examples
- Optimize individual modules separately
- Try GEPA for faster reflection-based optimization

### Issue: "OutOfMemory during optimization"

**Possible causes**:
1. Training set too large
2. LM context window exceeded
3. Caching too many traces

**Solutions**:
- Reduce training set size to 50-100 examples
- Reduce `max_bootstrapped_demos` to 1-2
- Use lighter optimizer (BootstrapFewShot or GEPA)
- Clear DSPy cache: `rm -rf .dspy_cache`

## Best Practices

### 1. Always Use Separate Train/Test Sets

```python
# Good
trainset = examples[:80]
testset = examples[80:]
optimized = optimizer.compile(program, trainset=trainset)
final_score = evaluate(optimized, testset)

# Bad - overfitting
optimized = optimizer.compile(program, trainset=examples)
final_score = evaluate(optimized, examples)  # Same data!
```

### 2. Define Clear Success Metrics

```python
# Good - clear criteria
def metric(example, pred, trace=None):
    criteria = {
        "has_output": hasattr(pred, "output") and pred.output,
        "correct_format": validate_format(pred.output),
        "semantically_correct": check_semantic(example, pred),
    }
    return sum(criteria.values()) / len(criteria)

# Bad - vague metric
def metric(example, pred, trace=None):
    return 0.5  # Arbitrary
```

### 3. Document Your Optimization Strategy

```python
# Include comments like:
# Optimization Strategy:
# 1. BootstrapFewShot baseline (~5 min, expected +5-10%)
# 2. MIPROv2 medium for production (~20 min, expected +15-25%)
# 3. Validated on separate 50-example test set
# 4. Results saved to config/optimized/
```

### 4. Monitor Optimization Progress

```python
# Collect results over time
results_log = []

for optimizer_type in ["bootstrap", "mipro", "gepa"]:
    result = run_optimization(optimizer_type)
    results_log.append({
        "optimizer": optimizer_type,
        "score": result["optimized_score"],
        "improvement": result["improvement_percent"],
        "time": result["duration"]
    })

# Analyze progress
import json
with open("optimization_history.json", "w") as f:
    json.dump(results_log, f, indent=2)
```

## References

- **DSPy Docs**: https://dspy.ai
- **BootstrapFewShot**: https://dspy.ai/api/optimizers/BootstrapFewShot/overview/
- **MIPROv2**: https://dspy.ai/api/optimizers/MIPROv2/overview/
- **GEPA**: https://dspy.ai/api/optimizers/GEPA/overview/
- **Training Data**: `config/training/trainset_v4.json`
- **Optimization Script**: `scripts/run_optimization.py`
- **Results**: `config/optimized/`

## Questions?

For issues or questions:
1. Check the troubleshooting section above
2. Review existing optimization results in `config/optimized/`
3. Check DSPy official documentation
4. Review test suite: `tests/unit/test_dspy_*.py`
