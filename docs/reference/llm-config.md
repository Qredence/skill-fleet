# LLM & DSPy Configuration (reference)

Last updated: 2026-01-27

This reference collects the canonical places to configure language models and DSPy for Skills Fleet.

Key locations:

- Code: `src/skill_fleet/llm/dspy_config.py` (use `configure_dspy()` and `get_task_lm()`)
- Default config: `src/skill_fleet/config/config.yaml`
- Provider-specific settings: `docs/llm/providers.md`
- Task-model mappings: `docs/llm/task-models.md`

Core guidance:

- Call `configure_dspy()` once at application startup. For temporary overrides, use `get_task_lm()` or `dspy.context()`.
- Use `DSPY_CACHEDIR` and `DSPY_TEMPERATURE` environment variables for deployment overrides.
- Prefer task-specific LMs for different phases (analysis/generation/validation) to improve cost/quality tradeoffs.

Example (startup):

```python
from skill_fleet.llm.dspy_config import configure_dspy

# Configure global DSPy LM
configure_dspy()
```

See `docs/llm/dspy-config.md` for the full reference and usage examples.
