# Signature Tuning Orchestrator

The **SignatureTuningOrchestrator** manages signature tuning and optimization workflow to improve skill quality scores.

`★ Insight ─────────────────────────────────────`
Signature tuning uses **iterative refinement** - it analyzes failures, proposes improvements, and evaluates whether the improvement meets the threshold. This prevents endless tuning loops while ensuring genuine quality improvements.
`─────────────────────────────────────────────────`

## Overview

The orchestrator manages:
- **Failure Analysis** - Understand why a signature produced low-quality output
- **Signature Improvement** - Propose better signature structures
- **Iterative Tuning** - Repeatedly tune until target score is reached
- **Version Tracking** - Maintain history of signature versions

## Quick Start

```python
from skill_fleet.workflows import SignatureTuningOrchestrator

orchestrator = SignatureTuningOrchestrator(
    improvement_threshold=0.05,  # Require 5% improvement
    max_iterations=3,            # Maximum tuning iterations
    quality_threshold=0.75,      # Tune if score below 0.75
)

# Single tuning pass
result = await orchestrator.tune_signature(
    skill_content=generated_skill,
    current_signature=current_signature,
    metric_score=0.65,           # Current quality score
    target_score=0.80,           # Desired quality score
    skill_type="comprehensive",
)

# Check if tuning was needed
if result["tuning_needed"]:
    print(f"Proposed signature: {result['proposed_signature']}")
    print(f"Reason: {result['failure_analysis']['reason']}")

# Iterative tuning (automatic retries)
result = await orchestrator.tune_iteratively(
    skill_content=generated_skill,
    current_signature=current_signature,
    metric_score=0.65,
    target_score=0.80,
)

print(f"Iterations used: {result['iterations_used']}")
print(f"Target reached: {result['target_reached']}")
```

## API Reference

### `__init__(task_lms=None, improvement_threshold=0.05, max_iterations=3, quality_threshold=0.75)`

Initialize the orchestrator.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `task_lms` | dict[str, dspy.LM], optional | Task-specific LMs |
| `improvement_threshold` | float | Minimum improvement to accept (default: 0.05 = 5%) |
| `max_iterations` | int | Maximum tuning iterations per session (default: 3) |
| `quality_threshold` | float | Score below which tuning is triggered (default: 0.75) |

### Single Tuning

#### `tune_signature(skill_content, current_signature, metric_score, target_score=0.80, skill_type="comprehensive", signature_id=None, enable_mlflow=True)`

Tune a signature to improve quality scores.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_content` | str | The generated skill content |
| `current_signature` | str | The signature that generated this content |
| `metric_score` | float | Current quality score (0.0-1.0) |
| `target_score` | float | Target quality score (default: 0.80) |
| `skill_type` | str | Type of skill: `"navigation_hub"`, `"comprehensive"`, `"minimal"` |
| `signature_id` | str, optional | ID for version tracking |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "tuning_needed": bool,
    "proposed_signature": str,      # Improved signature (if needed)
    "failure_analysis": {
        "reason": str,
        "issues": [str],
        "suggested_changes": [str],
    },
    "version_history": {
        "signature_id": str,
        "version": int,
        "score": float,
        "timestamp": str,
    },
}
```

### Iterative Tuning

#### `tune_iteratively(skill_content, current_signature, metric_score, target_score=0.80, skill_type="comprehensive", re_evaluate_fn=None, enable_mlflow=True)`

Iteratively tune signature until target score is reached or max iterations.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `skill_content` | str | The generated skill content |
| `current_signature` | str | The signature that generated this content |
| `metric_score` | float | Current quality score (0.0-1.0) |
| `target_score` | float | Target quality score (default: 0.80) |
| `skill_type` | str | Type of skill for context |
| `re_evaluate_fn` | callable, optional | Function to re-evaluate after tuning |
| `enable_mlflow` | bool | Whether to track with MLflow |

**Returns:**
```python
{
    "tuning_needed": bool,
    "final_signature": str,
    "final_score": float,
    "iterations_used": int,
    "target_reached": bool,
    "total_improvement": float,
    "version_history": [...],
}
```

### Version Tracking

#### `get_version_history(signature_id)`

Get version history for a signature.

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `signature_id` | str | ID of the signature |

**Returns:** Version history dictionary or `None` if not found

## Synchronous Usage

```python
orchestrator = SignatureTuningOrchestrator()

# Synchronous usage
result = orchestrator.tune_signature_sync(
    skill_content=generated_skill,
    current_signature=current_sig,
    metric_score=0.65,
)
```

## Examples

### Basic Tuning

```python
from skill_fleet.workflows import SignatureTuningOrchestrator

orchestrator = SignatureTuningOrchestrator()

# After generating content with low quality score
quality_score = evaluate_quality(generated_skill)  # Returns 0.65

if quality_score < 0.75:
    result = await orchestrator.tune_signature(
        skill_content=generated_skill,
        current_signature=used_signature,
        metric_score=quality_score,
        target_score=0.80,
        skill_type="comprehensive",
    )

    if result["tuning_needed"]:
        print("Tuning recommended:")
        print(f"  Reason: {result['failure_analysis']['reason']}")
        print(f"  Proposed: {result['proposed_signature']}")

        # Use the improved signature
        improved_signature = result["proposed_signature"]
```

### Iterative Tuning

```python
# Let the orchestrator iteratively tune until target is reached
result = await orchestrator.tune_iteratively(
    skill_content=generated_skill,
    current_signature=used_signature,
    metric_score=0.65,
    target_score=0.80,
    skill_type="comprehensive",
    re_evaluate_fn=evaluate_quality,  # Function to re-evaluate
)

if result["target_reached"]:
    print(f"Success! Reached target in {result['iterations_used']} iterations")
    print(f"Total improvement: {result['total_improvement']:.2%}")
else:
    print(f"Used max iterations. Final score: {result['final_score']:.2%}")
```

### Custom Configuration

```python
# Strict tuning - require significant improvements
strict_orchestrator = SignatureTuningOrchestrator(
    improvement_threshold=0.10,  # Require 10% improvement
    max_iterations=5,            # More iterations allowed
    quality_threshold=0.85,      # Higher threshold
)

# Lenient tuning - accept small improvements
lenient_orchestrator = SignatureTuningOrchestrator(
    improvement_threshold=0.02,  # Accept 2% improvement
    max_iterations=2,            # Fewer iterations
    quality_threshold=0.70,      # Lower threshold
)
```

### Version History

```python
# Track signature versions
signature_id = "python_decorators_v1"

result = await orchestrator.tune_signature(
    skill_content=skill,
    current_signature=sig,
    metric_score=0.70,
    signature_id=signature_id,
)

# Later, retrieve version history
history = orchestrator.get_version_history(signature_id)
print(f"Version: {history['version']}")
print(f"Score: {history['score']}")
print(f"Timestamp: {history['timestamp']}")
```

## Configuration Parameters

### `improvement_threshold`

Minimum improvement required to accept a tuning suggestion.

- **Default:** `0.05` (5% improvement)
- **Higher values** = More selective, fewer tuning iterations
- **Lower values** = More accepting, more iterations

```python
# Strict: require 10% improvement
orchestrator = SignatureTuningOrchestrator(improvement_threshold=0.10)

# Lenient: accept 2% improvement
orchestrator = SignatureTuningOrchestrator(improvement_threshold=0.02)
```

### `max_iterations`

Maximum number of tuning iterations per session.

- **Default:** `3`
- **Higher values** = More thorough, but slower
- **Lower values** = Faster, but may not reach target

```python
# Thorough: up to 5 iterations
orchestrator = SignatureTuningOrchestrator(max_iterations=5)

# Quick: max 2 iterations
orchestrator = SignatureTuningOrchestrator(max_iterations=2)
```

### `quality_threshold`

Score below which tuning is automatically triggered.

- **Default:** `0.75`
- **Higher values** = More aggressive tuning
- **Lower values** = Only tune very poor results

```python
# Aggressive: tune if below 0.85
orchestrator = SignatureTuningOrchestrator(quality_threshold=0.85)

# Relaxed: only tune if below 0.70
orchestrator = SignatureTuningOrchestrator(quality_threshold=0.70)
```

## MLflow Tracking

When `enable_mlflow=True`, the orchestrator logs:

**Parameters:**
- `skill_type`
- `current_score`
- `target_score`
- `max_iterations` (for iterative tuning)

**Metrics:**
- `tuning_needed` (bool)
- `accept_improvement` (bool)
- `iterations_used` (int)
- `target_reached` (bool)
- `total_improvement` (float)

**Experiments:**
- `signature-tuning` - Single tuning pass
- `signature-tuning-iterative` - Iterative tuning

## Integration with Workflow

```python
from skill_fleet.workflows import (
    ContentGenerationOrchestrator,
    SignatureTuningOrchestrator,
)

content_orchestrator = ContentGenerationOrchestrator()
tuning_orchestrator = SignatureTuningOrchestrator()

# Generate content
content_result = await content_orchestrator.generate(
    understanding=understanding,
    plan=plan,
    skill_style="comprehensive",
)

# Evaluate quality
quality_score = evaluate(content_result["skill_content"])

# Auto-tune if quality is low
if quality_score < 0.75:
    tune_result = await tuning_orchestrator.tune_iteratively(
        skill_content=content_result["skill_content"],
        current_signature=used_signature,
        metric_score=quality_score,
        target_score=0.80,
        re_evaluate_fn=evaluate,
    )

    if tune_result["target_reached"]:
        # Regenerate with improved signature
        improved_result = await content_orchestrator.generate(
            understanding=understanding,
            plan=plan,
            skill_style="comprehensive",
        )
```

## Related Documentation

- [Content Generation Orchestrator](content-generation.md) - Phase 2 content generation
- [DSPy Optimization](../dspy/optimization.md) - MIPROv2, GEPA optimizers
- [DSPy Signatures](../dspy/signatures.md) - Signature organization
