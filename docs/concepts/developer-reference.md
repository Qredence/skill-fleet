# Skill Fleet — Developer Guide

## 1. Purpose & Architecture

Skill Fleet combines:
- **FastAPI** for API endpoints that orchestrate DSPy workflows (`/api/v2/skills`, `/api/v2/hitl`, `/api/v2/taxonomy`, `/api/v2/validation`).
- **DSPy programs** (`src/skill_fleet/core/programs/skill_creator.py`) implementing the three-phase skill creation pipeline with HITL callbacks.
- **Typer CLI** wrapping the API (`src/skill_fleet/cli/`) and the optional interactive agent (`src/skill_fleet/agent/` + `cli/interactive_cli.py`).
- **Taxonomy manager** (`src/skill_fleet/taxonomy/manager.py`) that enforces agentskills.io compliance and writes `metadata.json` + `SKILL.md`.
- **Templates** (`config/templates/SKILL_md_template.md`, `config/templates/metadata_template.json`) guide generated output.

## 2. Repository Layout

```
skill-fleet/
├── src/skill_fleet/
│   ├── api/          # FastAPI server, discovery, routes, jobs
│   ├── cli/          # Typer commands, shared HITL runner
│   ├── core/         # DSPy modules/signatures/program
│   ├── llm/          # DSPy configuration, LM builders
│   ├── taxonomy/      # Skill registration + metadata handling
│   ├── workflow/      # Legacy workflows (optimizer, creator, tracing)
│   ├── validators/    # agentskills.io validation rules
│   ├── agent/         # Conversational agent + session handling
│   └── common/        # Utilities (paths, async helpers)
├── config/            # Templates, config YAML, profile bootstrappers
├── docs/              # Documentation (new user/developer guides + legacy references)
├── skills/            # Taxonomy content + metadata
├── tests/             # Pytest suites
├── .env.example
├── pyproject.toml
└── uv.lock
```

## 3. Core Development Workflows

### 3.1 Configure DSPy

Call `configure_dspy()` once during startup (API server does this by default). Library consumers can use `skill_fleet.llm.dspy_config.get_task_lm()` when needing task-specific LMs. Keep `DSPY_CACHEDIR` and `DSPY_TEMPERATURE` in sync with environment.

### 3.2 Build + Run

Use `uv` for all Python commands:

```bash
uv sync --group dev
uv run skill-fleet serve
uv run pytest -q tests/unit
uv run ruff check src/skill_fleet
```

### 3.3 Developer CLI Commands

- `uv run skill-fleet create "...` uses the API `POST /api/v2/skills/create`.
- `uv run skill-fleet chat` shells the job + HITL loop via `src/skill_fleet/cli/hitl/runner.py`.
- `uv run skill-fleet validate` and `migrate` operate directly on `skills/` and call `TaxonomyManager`.

## 4. DSPy Program Details

`SkillCreationProgram.aforward()` (with HITL callbacks) executes:

1. **Phase 1**: Understand & plan → `Phase1UnderstandingModule`.
2. **Phase 2**: Generate content + preview/refinement using `Phase2GenerationModule`.
3. **Phase 3**: Validation/refinement via `Phase3ValidationModule`.

HITL callbacks feed prompts back to the CLI or API via `wait_for_hitl_response`. The CLI runner understands `clarify`, `confirm`, `preview`, and `validate` types, so keep that mapping in sync.

## 5. Templates & Metadata

- `config/templates/SKILL_md_template.md` is trimmed and injected into Phase 2 instructions to steer the LLM’s SKILL.md output.
- `config/templates/metadata_template.json` defines the `metadata.json` fields (version, type, load priority, dependencies, capabilities, evolution).
- `TaxonomyManager.register_skill()` enforces kebab-case names, descriptions, and metadata lists. Update this logic if templates change.

## 6. Testing & Quality Assurance

1. **Linting**: `uv run ruff check src/skill_fleet`
2. **Unit tests**: `uv run pytest -q tests/unit`
3. **Documentation**: Keep AGENTS.md and docs/ in sync with tooling changes.
4. **Interactive behavior**: Manual smoke tests via `skill-fleet create`, `skill-fleet chat`, `skill-fleet serve`.

## 7. Contributions & Planning

- Keep `AGENTS.md` updated when workflows or tooling change; this is the canonical “agent working guide”.
- Record multi-step work in `plans/` as ExecPlans or feature plans (see `plans/README.md`).
- For major features, abide by the multi-agent workflow guidance (Codex + MCP + Agents SDK).

## 8. References

### Documentation

- **[CLI Reference](../cli/)** - Command documentation and interactive chat
- **[API Reference](../api/)** - REST API endpoints and schemas
- **[DSPy Documentation](../dspy/)** - DSPy signatures, modules, programs
- **[LLM Configuration](../llm/)** - Provider setup and task-specific models
- **[HITL System](../hitl/)** - Human-in-the-Loop interactions

### Legacy References

- `docs/cli-reference.md`, `docs/skill-creator-guide.md`, `docs/api-reference.md`
- `skills/` directory for live examples
- `docs/plans/` for ongoing experiments (CLI UX, FastAPI production patterns)
