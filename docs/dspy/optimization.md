# DSPy Optimization

**Last Updated**: 2026-01-15

## Overview

DSPy provides built-in optimizers for improving prompt quality and reducing costs through intelligent caching. This guide covers how skills-fleet leverages DSPy optimization features.

Skills Fleet uses an **API-first approach** for optimization, with endpoints available at `/api/v2/optimization`. For quality assessment, see [Evaluation Documentation](evaluation.md).

`★ Insight ─────────────────────────────────────`
DSPy optimizers work by "learning" from examples. They analyze a training set of input/output pairs and automatically adjust prompts to maximize performance. This replaces manual prompt engineering with data-driven optimization.
`─────────────────────────────────────────────────`

## Optimization Techniques

| Technique   | Purpose                               | Cost      | Quality Gain |
|-------------|---------------------------------------|-----------|--------------|
| **MIPROv2** | Multi-step instruction optimization   | High      | Significant  |
| **GEPA**    | Guided evolution with prompt assembly | Medium    | Moderate     |
| **Caching** | Response caching to reduce LLM calls  | None      | Neutral      |
| **BestOfN** | Generate N candidates, pick best      | High (N×) | Moderate     |

---

## MIPROv2 Optimizer

**Multi-step Instruction Propagation with Optimizer v2**

MIPROv2 is DSPy's most powerful optimizer. It:

1. **Profiling**: Runs your program on training examples to collect traces
2. **Instruction Optimization**: Generates optimal instructions for each step
3. **Few-Shot Selection**: Selects the best examples for each module
4. **Iterative Refinement**: Improves over multiple rounds

### When to Use MIPROv2

- **Complex workflows** with multiple steps
- **High-value skills** where quality matters
- **Consistent failure patterns** in current prompts
- **Available training data** (10-100 examples)

### Usage

```python
import dspy
from skill_fleet.core.programs.skill_creator import SkillCreationProgram

# Load training data
trainset = [
    {
        "task_description": "Create a Python async skill",
        "expected_output": "...",
    },
    # ... more examples
]

# Configure MIPROv2
def metric_fn(gold, pred, trace=None):
    """Custom metric for optimization."""
    # Compare gold standard with prediction
    return similarity_score(gold, pred)

# Create optimizer
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=metric_fn,
    num_threads=4,
    num_trials=10,
    max_labeled_demos=4,
    max_rounds=2,
)

# Optimize the program
program = SkillCreationProgram()
optimized_program = optimizer.compile(
    program,
    trainset=trainset,
    valset=valset  # Optional validation set
)

# Save optimized program
optimized_program.save("optimized_program.json")
```

### Configuration Parameters

| Parameter                | Default  | Description                              |
|--------------------------|----------|------------------------------------------|
| `metric`                 | Required | Evaluation function (gold, pred) → score |
| `num_threads`            | `1`      | Parallel optimization threads            |
| `num_trials`             | `10`     | Optimization trials per round            |
| `max_labeled_demos`      | `4`      | Max few-shot examples per module         |
| `max_rounds`             | `2`      | Optimization rounds                      |
| `max_bootstrapped_demos` | `8`      | Max generated examples                   |
| `teacher_settings`       | `None`   | LM settings for generating traces        |

### Training Set Format

```python
trainset = [
    dspy.Example(
        task_description="Create a Python decorators skill",
        user_context='{"user_id": "user_1"}',
        taxonomy_structure='{"technical_skills": {"programming": {"python": {}}}}',
        existing_skills='["technical_skills/programming/python"]',
    ).with_inputs(
        "expected_skill_metadata",
        "expected_content_outline",
    ),
    # ... more examples
]
```

---

## GEPA Optimizer

**Guided Evolution with Prompt Assembly**

GEPA is a simpler optimizer that evolves prompts through guided assembly. It's faster than MIPROv2 but provides smaller quality gains.

### When to Use GEPA

- **Quick optimization** with limited time
- **Smaller training sets** (5-20 examples)
- **Moderate quality improvements** sufficient
- **Cost-sensitive** applications

### Usage

```python
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from dspy.evaluate import Evaluate

# Create optimizer (GEPA-style)
optimizer = BootstrapFewShotWithRandomSearch(
    max_bootstrapped_demos=4,
    max_labeled_demos=4,
    num_trials=10,
    metric=metric_fn,
    teacher_settings=dict(lm=teacher_lm),
)

# Optimize
optimized_program = optimizer.compile(
    program,
    trainset=trainset,
)

# Evaluate
evaluate = Evaluate(
    devset=valset,
    num_threads=4,
    metric=metric_fn,
    display_progress=True,
)

score = evaluate(optimized_program)
print(f"Optimized score: {score}")
```

---

## Caching Strategy

DSPy includes built-in caching to avoid redundant LLM calls. Skills Fleet uses this for cost optimization.

### Cache Configuration

```python
from skill_fleet.llm.dspy_config import configure_dspy
import os

# Set cache directory
os.environ["DSPY_CACHEDIR"] = "/var/cache/dspy"

# Configure DSPy (enables caching)
lm = configure_dspy()
```

### Cache Behavior

| Scenario              | Cache Behavior                      |
|-----------------------|-------------------------------------|
| **Exact input match** | Return cached response immediately  |
| **Similar input**     | No cache hit (exact match required) |
| **Cache miss**        | Call LLM and store response         |

### Cache Invalidation

```python
# Clear cache manually
import dspy
dspy.settings.configure(cache_dir=None)

# Or remove cache directory
import shutil
shutil.rmtree(os.environ.get("DSPY_CACHEDIR", ".dspy_cache"))
```

`★ Insight ─────────────────────────────────────`
Caching is most effective during development and testing. The same skill descriptions are often tested repeatedly during iteration. In production, the cache hit rate will be lower but still valuable for recurring tasks.
`─────────────────────────────────────────────────`

---

## BestOfN Pattern

Generate multiple candidates and select the best one using a reward function.

### When to Use BestOfN

- **Critical quality requirements**
- **Sufficient budget** for N generations
- **Reliable reward function** available
- **Single-output modules** (not orchestrators)

### Usage

```python
import dspy

def reward_fn(prediction, trace):
    """Reward function for selecting best candidate."""
    # Score the prediction
    score = score_quality(prediction)
    return score

# Create BestOfN module
from dspy.primitives.example import Example

module = dspy.BestOfN(
    dspy.ChainOfThought(GenerateSkillContent),
    n=3,  # Generate 3 candidates
    reward_fn=reward_fn,
)

# Use like normal module
result = module(
    skill_metadata=metadata,
    content_plan=plan,
    generation_instructions=instructions,
)
```

### Reward Function Design

```python
def reward_fn(prediction, trace=None):
    """Score a prediction (higher is better)."""
    score = 0.0

    # Check for required sections
    if "## Overview" in prediction.skill_content:
        score += 0.2
    if "## Examples" in prediction.skill_content:
        score += 0.2

    # Check YAML frontmatter
    if prediction.skill_content.startswith("---"):
        score += 0.2

    # Check content length
    if 500 < len(prediction.skill_content) < 5000:
        score += 0.2

    # Check code examples
    code_blocks = prediction.skill_content.count("```")
    if code_blocks >= 3:
        score += 0.2

    return score
```

---

## Workflow Optimization

Skills Fleet's workflow system (distributed in `src/skill_fleet/core/dspy/`) provides additional optimization capabilities.

### Optimization Command

```bash
uv run skill-fleet optimize \
    --training-data config/training/trainset.json \
    --output config/optimized/ \
    --optimizer miprov2 \
    --rounds 2
```

### Training Set Format

```json
[
    {
        "task_description": "Create a Python async/await skill",
        "user_context": {"user_id": "user_1"},
        "taxonomy_structure": {...},
        "existing_skills": [...],
        "expected": {
            "taxonomy_path": "technical_skills/programming/python/async",
            "name": "python-async-await",
            "sections": ["Overview", "Syntax", "Examples"]
        }
    }
]
```

---

## Performance Tuning

### Model Selection

Different models for different optimization phases:

| Phase            | Recommended Model   | Rationale                     |
|------------------|---------------------|-------------------------------|
| **Profiling**    | Fast model (Flash)  | Quick data collection         |
| **Optimization** | Capable model (Pro) | Better instruction generation |
| **Evaluation**   | Target model        | Real-world performance        |

### Parallel Optimization

```python
# Use multiple threads for faster optimization
optimizer = MIPROv2(
    metric=metric_fn,
    num_threads=8,  # Parallel optimization
    num_trials=20,
)
```

### Cost Estimation

```python
# Approximate cost formula
cost = (
    num_examples *
    (num_trials * avg_tokens_per_trial) *
    (model_cost_per_1k_tokens / 1000)
)

# Example: 50 examples, 10 trials, 2000 tokens/trial, $0.001/1k tokens
# cost = 50 * 10 * 2 * 0.001 = $1.00
```

---

## Monitoring Optimization

### Metrics to Track

| Metric            | Description                 | Target            |
|-------------------|-----------------------------|-------------------|
| **Accuracy**      | Correct predictions / total | > 0.9             |
| **Latency**       | Time per optimization round | < 5 min           |
| **Cost**          | LLM API costs               | Budget permitting |
| **Quality Score** | Custom quality metric       | Improving         |

### Logging

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dspy")

# During optimization
logger.info(f"Round {round_num}: score={score:.3f}")
logger.info(f"Best instructions: {best_instructions}")
```

---

## Best Practices

1. **Start Simple**: Use caching first, then try GEPA before MIPROv2
2. **Data Quality**: Ensure training examples are high-quality and diverse
3. **Metric Design**: Invest time in a good reward/evaluation metric
4. **Incremental**: Optimize individual modules before the full program
5. **Validation**: Always hold out a validation set to prevent overfitting

---

## CLI Integration

```bash
# Run optimization
uv run skill-fleet optimize \
    --program SkillCreationProgram \
    --data config/training/trainset.json \
    --optimizer miprov2 \
    --rounds 2 \
    --trials 10 \
    --output config/optimized/

# Use optimized program
uv run skill-fleet create-skill \
    --task "Create a skill" \
    --program config/optimized/skill_creator.json
```

---

## API Endpoints

Skills Fleet provides REST API endpoints for optimization:

### POST /api/v2/optimization/start

Start an optimization job (runs in background).

```json
{
    "optimizer": "miprov2",
    "training_paths": [
        "technical_skills/programming/web_frameworks/python/fastapi"
    ],
    "auto": "medium",
    "max_bootstrapped_demos": 4,
    "max_labeled_demos": 4,
    "save_path": "skill_creator_optimized.json"
}
```

### GET /api/v2/optimization/status/{job_id}

Check optimization job status and progress.

```json
{
    "job_id": "abc-123",
    "status": "running",
    "progress": 0.5,
    "message": "Running miprov2 optimization..."
}
```

### GET /api/v2/optimization/optimizers

List available optimizers and their parameters.

### GET /api/v2/optimization/config

Get current optimization configuration from `config.yaml`.

### DELETE /api/v2/optimization/jobs/{job_id}

Cancel or remove an optimization job.

---

## See Also

- **[DSPy Overview](index.md)** - Architecture and concepts
- **[Evaluation Documentation](evaluation.md)** - Quality metrics and assessment
- **[Modules Documentation](modules.md)** - Module implementations
- **[Programs Documentation](programs.md)** - Program orchestration
- **[API Endpoints](../api/endpoints.md)** - Full API reference
- **[LLM Configuration](../llm/dspy-config.md)** - Model setup for optimization
