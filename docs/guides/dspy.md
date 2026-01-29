# DSPy Guide

Last updated: 2026-01-27

This guide orients readers to the DSPy integration used by Skills Fleet. For full module-level details see `docs/dspy/`.

## What is DSPy here?

DSPy is the internal program orchestration framework used to build the three-phase skill creation programs. It provides signatures, modules, and program composition primitives used by the TaskAnalysis, ContentGeneration, and QualityAssurance orchestrators.

## Where to configure LMs

Centralized DSPy/LM configuration lives in `src/skill_fleet/llm/dspy_config.py`. Default model settings and task-specific mappings are defined in `config/config.yaml`.

## Optimization

Skill Fleet supports optimization workflows (MIPROv2, GEPA) to tune prompts and few-shot examples. Use the API or CLI `optimization` endpoints/commands to start optimization jobs.

## See also

- `docs/dspy/index.md` — detailed DSPy architecture and modules
- `docs/dspy/optimization.md` — optimizer guides
- `src/skill_fleet/core/dspy/` — code-level implementations
