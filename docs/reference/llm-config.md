# LLM & DSPy Configuration (reference)

Last updated: 2026-01-30

This reference collects the canonical places to configure language models and DSPy for Skills Fleet.

Key locations:

- Code: `src/skill_fleet/dspy/config.py` (use `dspy_context()` for scoped configuration)
- Initialization: `src/skill_fleet/api/lifespan.py` (application startup)
- Config loader: `src/skill_fleet/infrastructure/tracing/config.py` (ConfigModelLoader)
- Default config: `src/skill_fleet/config/config.yaml`
- Provider-specific settings: `docs/llm/providers.md`
- Task-model mappings: `docs/llm/task-models.md`

Core guidance:

- DSPy configuration is handled at application startup in `api/lifespan.py` using `ConfigModelLoader`.
- For scoped configuration (e.g., per-request or per-task), use `dspy_context()` context manager.
- Use `DSPY_CACHEDIR` and `DSPY_TEMPERATURE` environment variables for deployment overrides.
- Prefer task-specific LMs for different phases (analysis/generation/validation) to improve cost/quality tradeoffs.

Example (scoped configuration):

```python
from skill_fleet.dspy import dspy_context

# Use custom LM for this scope
with dspy_context(lm=custom_lm):
    result = await module.aforward(...)
```

See `docs/llm/dspy-config.md` for the full reference and usage examples.
