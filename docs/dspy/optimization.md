# Optimizer Auto-Selection Guide

The Optimizer Auto-Selection Engine intelligently recommends the best DSPy optimizer based on your task characteristics, budget, and quality goals.

## Quick Start

### CLI Usage

```bash
# Auto-select optimizer based on trainset and budget
uv run skill-fleet optimize --auto-select --budget 10.0 --quality-target 0.85

# With time constraint
uv run skill-fleet optimize --auto-select --time-limit 5 --budget 20.0

# Specify trainset
uv run skill-fleet optimize --auto-select \
  --trainset config/training/trainset_v4.json \
  --budget 15.0
```

### API Usage

```bash
curl -X POST http://localhost:8000/api/v1/optimization/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "trainset_size": 50,
    "budget_dollars": 10.0,
    "quality_target": 0.85,
    "domain": "testing"
  }'
```

### Python Usage

```python
from skill_fleet.core.dspy.optimization.selector import (
    OptimizerContext,
    OptimizerSelector,
)

# Create context
context = OptimizerContext(
    trainset_size=50,
    budget_dollars=10.0,
    quality_target=0.85,
    domain="testing",
)

# Get recommendation
selector = OptimizerSelector()
result = selector.recommend(context)

print(f"Recommended: {result.recommended.value}")
print(f"Config: auto={result.config.auto}")
print(f"Cost: ${result.estimated_cost:.2f}")
print(f"Time: {result.estimated_time_minutes} min")
print(f"Confidence: {result.confidence:.0%}")
print(f"Reasoning: {result.reasoning}")
```

## Decision Rules

| Condition | Recommended Optimizer | Why |
|-----------|----------------------|-----|
| time < 2 min | Reflection Metrics | Fastest (<1 sec) |
| budget < $1 | Reflection Metrics | Cheapest ($0.01-0.05) |
| trainset < 100 AND budget < $5 | GEPA | Fast + cheap for small data |
| trainset < 500 AND budget < $20 | MIPROv2 (light) | Good balance |
| trainset >= 500 AND budget >= $20 | MIPROv2 (medium) | Best quality |
| budget >= $100 | MIPROv2 (heavy) | Maximum quality |
| budget >= $100 AND quality >= 0.95 | BootstrapFinetune | Weight tuning |
| Fallback | BootstrapFewShot | Always works |

## Cost Estimates

| Optimizer | Cost per 100 examples | Time per 100 examples |
|-----------|----------------------|----------------------|
| Reflection Metrics | $0.05 | < 1 min |
| BootstrapFewShot | $0.10 | 1 min |
| GEPA | $0.50 | 5 min |
| MIPROv2 (light) | $1.25 | 7 min |
| MIPROv2 (medium) | $2.50 | 15 min |
| MIPROv2 (heavy) | $6.25 | 40 min |
| BootstrapFinetune | $20.00 | 60 min |

## Metrics Tracking

Results are automatically recorded to `config/selector_metrics.jsonl` for future learning. The system uses historical data to improve confidence in recommendations.

## API Response Example

```json
{
  "recommended": "miprov2",
  "config": {
    "auto": "light",
    "max_bootstrapped_demos": 2,
    "max_labeled_demos": 4,
    "num_threads": 8
  },
  "estimated_cost": 1.25,
  "estimated_time_minutes": 7,
  "confidence": 0.82,
  "reasoning": "Medium trainset (50) + moderate budget ($10.00). MIPROv2 'light' provides good quality/cost balance.",
  "alternatives": [
    {
      "optimizer": "reflection_metrics",
      "cost": "$0.03",
      "time": "< 1 min",
      "quality_risk": 0.15,
      "note": "Fastest option, may sacrifice some quality"
    },
    {
      "optimizer": "bootstrap_fewshot",
      "cost": "$0.05",
      "time": "1 min",
      "quality_risk": 0.10,
      "note": "Safe fallback, always works"
    }
  ]
}
```

## CLI Output Example

```
============================================================
🤖 Optimizer Auto-Selection
============================================================
Trainset size: 50
Budget: $10.00
Quality target: 0.85

✅ Recommended: miprov2
   Config: auto=light
   Estimated cost: $1.25
   Estimated time: 7 minutes
   Confidence: 75%

📝 Reasoning: Medium trainset (50) + moderate budget ($10.00). 
   MIPROv2 'light' provides good quality/cost balance.

🔄 Alternatives:
   - reflection_metrics: $0.03 | < 1 min | Risk: +15%
   - bootstrap_fewshot: $0.05 | 1 min | Risk: +10%
============================================================

Proceed with recommended optimizer? [Y/n]:
```

## Advanced Usage

### Recording Results for Learning

The selector can learn from past optimization results:

```python
# After optimization completes
selector.record_result(
    context=context,
    optimizer=OptimizerType.MIPROV2,
    actual_cost=1.50,
    actual_time_minutes=8,
    quality_score=0.87,
)
```

### Custom Metrics Path

```python
selector = OptimizerSelector(
    metrics_path="path/to/custom_metrics.jsonl"
)
```

### Context Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trainset_size` | int | required | Number of training examples |
| `budget_dollars` | float | 10.0 | Maximum budget in USD |
| `quality_target` | float | 0.85 | Target quality (0.0-1.0) |
| `complexity_score` | float | 0.5 | Task complexity (0.0-1.0) |
| `domain` | str | "general" | Skill domain/category |
| `time_constraint_minutes` | int | None | Max time allowed |
| `previous_optimizer` | str | None | Last optimizer used |
| `historical_quality` | float | None | Previous quality score |

## Troubleshooting

### "Recommendation confidence is low"

This happens when:
- Trainset is very small (< 20 examples)
- No historical data matches your domain
- Edge case parameters

**Solution**: Consider collecting more training data or using the recommended optimizer as a baseline.

### "Estimated cost too high"

**Solutions**:
1. Use `--time-limit` to force faster/cheaper options
2. Reduce `--budget` to get cheaper recommendations
3. Use `--optimizer reflection_metrics` for instant, cheap optimization

### "Wrong optimizer was selected"

The selector learns from results. After optimization:
1. Record the result with `record_result()`
2. Future recommendations will factor in your domain's history
