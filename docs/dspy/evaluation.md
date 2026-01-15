# DSPy Evaluation

**Last Updated**: 2026-01-15

## Overview

Skills Fleet includes a comprehensive evaluation system for assessing skill quality. The evaluation metrics are calibrated against golden skills from [Obra/superpowers](https://github.com/obra/superpowers/tree/main/skills) to ensure stricter, more realistic scoring.

`★ Insight ─────────────────────────────────────`
The evaluation system uses multidimensional scoring with penalty multipliers for missing critical elements. This ensures that skills meet high-quality standards before deployment, following the "TDD for documentation" approach from Obra's writing-skills methodology.
`─────────────────────────────────────────────────`

## API-First Approach

Evaluation is available via REST API endpoints at `/api/v2/evaluation`:

| Endpoint            | Method | Description                         |
|---------------------|--------|-------------------------------------|
| `/evaluate`         | POST   | Evaluate a skill at a path          |
| `/evaluate-content` | POST   | Evaluate raw SKILL.md content       |
| `/evaluate-batch`   | POST   | Batch evaluate multiple skills      |
| `/metrics-info`     | GET    | Get metrics information and weights |

See [API Endpoints](../api/endpoints.md#evaluation-endpoints) for full documentation.

---

## Quality Metrics

### Structure Metrics

| Metric                     | Weight | Description                                            |
|----------------------------|--------|--------------------------------------------------------|
| `frontmatter_completeness` | 0.10   | YAML frontmatter quality (name, description, metadata) |
| `has_overview`             | -      | Has Overview/Introduction section                      |
| `has_when_to_use`          | -      | Has "When to Use" section                              |
| `has_quick_reference`      | 0.06   | Has Quick Reference table                              |

### Pattern Metrics

| Metric              | Weight | Description                                 |
|---------------------|--------|---------------------------------------------|
| `pattern_count`     | 0.10   | Number of patterns (target: 5+)             |
| `has_anti_patterns` | 0.08   | Has ❌ anti-pattern examples                 |
| `has_key_insights`  | 0.08   | Has "Key insight:" summaries after patterns |

### Practical Value Metrics

| Metric                  | Weight | Description                        |
|-------------------------|--------|------------------------------------|
| `has_common_mistakes`   | 0.06   | Has Common Mistakes section/table  |
| `has_red_flags`         | 0.04   | Has Red Flags section              |
| `has_real_world_impact` | 0.08   | Has quantified real-world benefits |

### Code Quality Metrics

| Metric                  | Weight | Description                                                 |
|-------------------------|--------|-------------------------------------------------------------|
| `code_examples_count`   | -      | Number of code blocks                                       |
| `code_examples_quality` | 0.10   | Quality score (language spec, no placeholders, substantial) |

---

## Obra/Superpowers Quality Indicators

These stricter criteria are based on golden skills from [Obra/superpowers](https://github.com/obra/superpowers):

| Metric                  | Weight | Description                                                      |
|-------------------------|--------|------------------------------------------------------------------|
| `has_core_principle`    | 0.10   | Has "**Core principle:**" statement                              |
| `has_strong_guidance`   | 0.08   | Has Iron Law / imperative rules (NO X WITHOUT Y, MUST, NEVER)    |
| `has_good_bad_contrast` | 0.07   | Has paired Good/Bad or ❌/✅ examples                              |
| `description_quality`   | 0.05   | Description follows "Use when..." pattern with specific triggers |

### Critical Elements

Three metrics are considered **critical elements**:
1. `has_core_principle`
2. `has_strong_guidance`
3. `has_good_bad_contrast`

A **penalty multiplier** is applied based on how many critical elements are present:

| Critical Elements | Multiplier | Effect      |
|-------------------|------------|-------------|
| 0                 | 0.70       | 30% penalty |
| 1                 | 0.85       | 15% penalty |
| 2                 | 0.95       | 5% penalty  |
| 3                 | 1.00       | No penalty  |

---

## Usage

### Python API

```python
from skill_fleet.core.dspy.metrics import assess_skill_quality, SkillQualityScores

# Evaluate skill content
content = open("skills/path/to/SKILL.md").read()
scores: SkillQualityScores = assess_skill_quality(content)

print(f"Overall Score: {scores.overall_score:.3f}")
print(f"Pattern Count: {scores.pattern_count}")
print(f"Issues: {scores.issues}")
print(f"Strengths: {scores.strengths}")
```

### DSPy Metric Function

For use with DSPy optimizers:

```python
from skill_fleet.core.dspy.metrics import skill_quality_metric

# Use as metric in MIPROv2
from dspy.teleprompt import MIPROv2

optimizer = MIPROv2(
    metric=skill_quality_metric,
    auto="medium",
)
```

### REST API

```bash
# Evaluate a skill
curl -X POST http://localhost:8000/api/v2/evaluation/evaluate \
    -H "Content-Type: application/json" \
    -d '{"path": "technical_skills/programming/web_frameworks/python/fastapi"}'

# Evaluate raw content
curl -X POST http://localhost:8000/api/v2/evaluation/evaluate-content \
    -H "Content-Type: application/json" \
    -d '{"content": "---\nname: test\n---\n# Test"}'

# Get metrics info
curl http://localhost:8000/api/v2/evaluation/metrics-info
```

### CLI Tool

```bash
# Evaluate a single skill file
uv run python scripts/run_dspy_tools.py evaluate-file "skills/path/to/SKILL.md"

# Example output:
# Overall Score: 0.855
# Strengths (16):
#   - Has skill name
#   - Description follows 'Use when...' pattern
#   - Excellent pattern coverage (9 patterns)
#   ...
# Issues (1):
#   - Missing strong guidance (add imperative rules like 'NO X WITHOUT Y')
```

---

## Score Interpretation

| Score Range | Quality Level | Description |
|-------------|---------------|-------------|
| 0.90 - 1.00 | Excellent | Production-ready, meets all quality criteria |
| 0.80 - 0.89 | Good | Minor improvements needed |
| 0.60 - 0.79 | Mediocre | Significant gaps, needs revision |
| 0.00 - 0.59 | Poor | Major issues, requires substantial rework |

### Quality Thresholds (from config.yaml)

```yaml
evaluation:
  thresholds:
    minimum_quality: 0.6   # Minimum acceptable score
    target_quality: 0.8    # Target for production skills
    excellent_quality: 0.9 # Excellent skill threshold
```

---

## Example Evaluation Results

### Excellent Skill (FastAPI)

```
Overall Score: 0.855
Pattern Count: 9
Code Examples: 15

Strengths (16):
  ✓ Has skill name
  ✓ Description follows 'Use when...' pattern
  ✓ Complete metadata section
  ✓ Has overview section
  ✓ Has when to use section
  ✓ Has quick reference section
  ✓ Has core patterns section
  ✓ Has common mistakes section
  ✓ Has red flags section
  ✓ Includes real-world impact/benefits
  ✓ Excellent pattern coverage (9 patterns)
  ✓ Shows both anti-patterns (❌) and production patterns (✅)
  ✓ Includes key insights after patterns
  ✓ Rich code examples (15 blocks)
  ✓ All code blocks have language specification
  ✓ Has clear core principle statement

Issues (1):
  ✗ Missing strong guidance (add imperative rules like 'NO X WITHOUT Y')
```

### Mediocre Skill (shadcn-registry)

```
Overall Score: 0.720
Pattern Count: 2

Strengths (15):
  ✓ Has skill name
  ✓ Good pattern coverage (2 patterns)
  ...

Issues (4):
  ✗ Description should start with 'Use when...'
  ✗ Limited patterns (2), target is 5+
  ✗ Missing strong guidance
  ✗ Description lacks specific triggering conditions
```

---

## Custom Weights

You can provide custom weights to adjust scoring:

```python
custom_weights = {
    "pattern_count": 0.20,        # Increase pattern importance
    "has_core_principle": 0.15,   # Increase core principle importance
    "code_examples_quality": 0.05, # Decrease code quality importance
}

scores = assess_skill_quality(content, weights=custom_weights)
```

Or via API:

```json
{
    "path": "skills/path/to/skill",
    "weights": {
        "pattern_count": 0.20,
        "has_core_principle": 0.15
    }
}
```

---

## Integration with Optimization

The evaluation metrics integrate with DSPy optimizers:

1. **Training**: Use `skill_quality_metric` as the optimization metric
2. **Validation**: Evaluate generated skills against quality thresholds
3. **Feedback Loop**: Low scores trigger refinement iterations

```python
from skill_fleet.core.dspy.metrics import skill_quality_metric
from skill_fleet.core.dspy.optimization import SkillOptimizer

# Optimize using quality metric
optimizer = SkillOptimizer()
optimized_program = optimizer.optimize_with_miprov2(
    training_examples=gold_skills,
    metric=skill_quality_metric,
)
```

---

## See Also

- **[DSPy Overview](index.md)** - Architecture and concepts
- **[Optimization Documentation](optimization.md)** - MIPROv2, BootstrapFewShot
- **[API Endpoints](../api/endpoints.md)** - Full API reference
- **[Quality Criteria](../../config/training/quality_criteria.yaml)** - Scoring rubric configuration
