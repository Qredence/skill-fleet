# GEPA Quick Reference Card

**Quick Copy-Paste Commands & Configurations**

---

## Run Commands

### Default (Light, Gemini, ~$1, ~2min)
```bash
uv run python scripts/run_gepa_optimization.py
```

### Medium (Balanced, ~$3, ~10min)
```bash
GEPA_AUTO_LEVEL=medium uv run python scripts/run_gepa_optimization.py
```

### Heavy (Maximum, ~$5, ~20min)
```bash
GEPA_AUTO_LEVEL=heavy uv run python scripts/run_gepa_optimization.py
```

### With GPT-4o Reflection (Better quality)
```bash
GEPA_REFLECTION_MODEL=gpt-4o \
GEPA_AUTO_LEVEL=medium \
  uv run python scripts/run_gepa_optimization.py
```

### With All Customizations
```bash
export GEPA_AUTO_LEVEL=medium
export GEPA_REFLECTION_MODEL=gpt-4o
export GEPA_NUM_ITERATIONS=4
export GEPA_METRIC_TYPE=composite
uv run python scripts/run_gepa_optimization.py
```

---

## Configuration Matrix

### By Budget
```
Budget: <$1  → GEPA light
Budget: $1-3 → GEPA medium (recommended)
Budget: $3-5 → GEPA heavy
Budget: $5+  → MIPROv2 light
```

### By Speed
```
Fast (<5min):    GEPA light + Gemini
Medium (5-15min): GEPA medium + gpt-4o
Slow (>15min):   GEPA heavy or MIPROv2
```

### By Quality Target
```
Improvement 5-8%:  GEPA light + Gemini
Improvement 10-15%: GEPA medium + gpt-4o
Improvement 15-25%: MIPROv2 medium
```

---

## Environment Variables

```bash
# Effort level: light (2-3 iter), medium (4-5 iter), heavy (6+ iter)
GEPA_AUTO_LEVEL=medium

# LM for reflection: must be capable
GEPA_REFLECTION_MODEL=gpt-4o  # or gemini-3-flash-preview

# Reflection iterations
GEPA_NUM_ITERATIONS=4

# Metric: quality (simple) or composite (detailed)
GEPA_METRIC_TYPE=composite
```

---

## Key Files

```
scripts/run_gepa_optimization.py          # Main GEPA script
src/skill_fleet/core/dspy/metrics/gepa_reflection.py  # GEPA metrics
docs/dspy/GEPA_SETUP_GUIDE.md            # Full documentation
docs/dspy/GEPA_QUICK_REFERENCE.md        # This file

Results after running:
config/optimized/optimization_results_gepa_v1.json  # Results
config/optimized/skill_program_gepa_v1.pkl          # Optimized program
```

---

## Results Interpretation

```json
{
  "baseline_score": 0.75,
  "optimized_score": 0.82,
  "improvement": 0.07,
  "improvement_percent": 9.33
}
```

| Metric | Meaning |
|--------|---------|
| baseline_score | Score before optimization |
| optimized_score | Score after GEPA |
| improvement | Absolute change |
| improvement_percent | Relative % change |

**Expected ranges**:
- Poor baseline (40%): +15-25% improvement
- Average baseline (65%): +10-15% improvement
- Good baseline (80%): +5-10% improvement
- Excellent baseline (90%): +2-4% improvement

---

## Troubleshooting Checklist

- [ ] API server running? `uv run skill-fleet serve`
- [ ] Config file exists? `config/training/trainset_v4.json`
- [ ] API keys set? `echo $OPENAI_API_KEY` or `echo $GOOGLE_API_KEY`
- [ ] Enough examples? Need 50+ in trainset
- [ ] Metric works? Run test:
  ```bash
  uv run python -c "
  from skill_fleet.core.dspy.metrics.gepa_reflection import gepa_composite_metric
  import dspy
  example = dspy.Example(task_description='test')
  pred = dspy.Prediction(domain='test', category='test')
  result = gepa_composite_metric(example, pred)
  print(result['score'])
  "
  ```

---

## Compare Optimizers

```bash
# 1. Baseline (no optimization)
uv run python -c "from skill_fleet.core.dspy.metrics.skill_quality import skill_quality_metric; print('Ready to benchmark')"

# 2. BootstrapFewShot (free, ~1 min)
uv run python scripts/run_optimization.py

# 3. GEPA (cheap, ~2 min)
uv run python scripts/run_gepa_optimization.py

# 4. MIPROv2 (pricier, ~15 min)
# (use scripts/run_mipro_optimization.py when ready)

# Compare results
python -c "
import json
bootstrap = json.load(open('config/optimized/optimization_results_bootstrap_v1.json'))
gepa = json.load(open('config/optimized/optimization_results_gepa_v1.json'))
print(f'BootstrapFewShot: {bootstrap[\"optimized_score\"]:.1%}')
print(f'GEPA: {gepa[\"optimized_score\"]:.1%}')
"
```

---

## One-Liner Scripts

### Run GEPA + show results
```bash
uv run python scripts/run_gepa_optimization.py && \
jq '.optimized_score, .improvement_percent' config/optimized/optimization_results_gepa_v1.json
```

### Run GEPA with gpt-4o + time it
```bash
time GEPA_REFLECTION_MODEL=gpt-4o GEPA_AUTO_LEVEL=medium \
  uv run python scripts/run_gepa_optimization.py
```

### Compare with previous run
```bash
python -c "
import json
old = json.load(open('config/optimized/optimization_results_gepa_v1.json'))
new = json.load(open('config/optimized/optimization_results_gepa_v2.json'))
print(f'Previous: {old[\"optimized_score\"]:.1%} vs New: {new[\"optimized_score\"]:.1%}')
print(f'Change: {new[\"optimized_score\"] - old[\"optimized_score\"]:+.1%}')
"
```

---

## Integration with FastAPI

Add to `src/skill_fleet/api/routes/optimization.py`:

```python
from skill_fleet.core.dspy.metrics.gepa_reflection import gepa_composite_metric

@router.post("/optimize/gepa")
async def optimize_with_gepa(
    auto_level: str = "medium",
    reflection_model: str = "gpt-4o",
):
    """Run GEPA optimization."""
    # Implementation...
    metric = gepa_composite_metric
    optimizer = dspy.GEPA(
        metric=metric,
        reflection_lm=get_lm(reflection_model, temperature=1.0),
        auto=auto_level,
    )
    # ...
```

---

## Next Steps

1. **Quick Test**: `uv run python scripts/run_gepa_optimization.py`
2. **Check Results**: `cat config/optimized/optimization_results_gepa_v1.json`
3. **Compare**: Run with different reflection models
4. **Integrate**: Add to CI/CD pipeline
5. **Production**: Use ensemble of GEPA + MIPROv2

---

**See Also**: [Full GEPA Setup Guide](./GEPA_SETUP_GUIDE.md) | [DSPy Optimization Guide](./OPTIMIZATION_GUIDE.md)
