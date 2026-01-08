# Skill Creation Workflow (Agentic Skills System)

This document describes the Phase 1 skill creation workflow and how it integrates with the on-disk taxonomy.

## Implementation Locations

- Taxonomy manager: `src/agentic_fleet/agentic_skills_system/taxonomy/manager.py`
- DSPy signatures: `src/agentic_fleet/agentic_skills_system/workflow/signatures.py`
- DSPy modules: `src/agentic_fleet/agentic_skills_system/workflow/modules.py`
- DSPy programs: `src/agentic_fleet/agentic_skills_system/workflow/programs.py`
- Orchestrator: `src/agentic_fleet/agentic_skills_system/workflow/skill_creator.py`
- CLI runner: `src/agentic_fleet/agentic_skills_system/cli.py`
- OpenTUI entrypoint: `src/agentic_fleet/tui/main.tsx`

## Taxonomy Data

The default taxonomy root (for development) lives under:

- `src/agentic_fleet/agentic_skills_system/skills/`

All `skill_id` values are **path-style** (e.g. `technical_skills/programming/languages/python`).

## Model Selection

The skill workflow uses the fleet model config:

- `src/agentic_fleet/config.yaml`

This repo is configured to use Gemini 3 as the primary model:

- `gemini/gemini-3-flash-preview` (requires `GOOGLE_API_KEY`)

Each workflow step is executed under a task-specific LM context with optimized `thinking_level`:

- `skill_understand`, `skill_plan`, `skill_initialize`, `skill_edit`, `skill_package`, `skill_validate`

## Workflow Steps (6-Step Pattern)

1. **UNDERSTAND** – Map a task to a taxonomy path
2. **PLAN** – Define metadata, dependencies, and capabilities
3. **INITIALIZE** – Produce a skeleton structure for the skill
4. **EDIT** – Generate `SKILL.md` content + capability docs
5. **PACKAGE** – Validate and create a packaging manifest
6. **ITERATE** – Human-in-the-loop approval + evolution metadata

## Notes

- Phase 1 provides the workflow wiring and core taxonomy manager.
- Unit tests avoid LLM calls; end-to-end workflow execution requires a configured DSPy LM.

## Running

```bash
# from repo root
uv run skill-fleet create-skill --task "Create a Python async programming skill"
```
