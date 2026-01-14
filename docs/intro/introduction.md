# Skill Fleet — Introduction

## What You’re Looking At

Skill Fleet is an **agentic capability platform** that keeps AI knowledge modular, discoverable, and compliant with agentskills.io. Instead of monolithic prompts, it dynamically mounts only the skills needed for the current task, then spins up DSPy-powered workflows to reason, draft, validate, and persist new capabilities via a FastAPI job + HITL loop.

## Why It Matters

1. **Efficiency** – The taxonomy keeps agents light by loading skill directories on demand.
2. **Compliance** – Every skill comes with YAML frontmatter + `metadata.json` so other systems can consume it.
3. **Automation** – The FastAPI backend orchestrates DSPy modules with human-in-the-loop checkpoints.
4. **Observability** – CLI + documentation link logging, analytics, and templates to keep quality high.

## How to Explore the System

- **Getting started** → `docs/getting-started/index.md` covers install, CLI usage, templates, and validation/migration flows.
- **Architectural overview** → `docs/overview.md` and the existing `docs/architecture/` tree explain how DSPy programs, modules, and taxonomy combine.
- **Concept deep dives** → `docs/concepts/developer-reference.md` and future concept docs (Planning, HITL, Templates) go into workflow specifics.
- **Living guide** → `AGENTS.md` is the working instructions for agents/developers.

## Map of the Docs Tree

```
docs/
├── intro/
│   └── introduction.md         # This page
├── getting-started/
│   └── index.md                # Installation, CLI/API, templates, validation
├── dspy/                       # DSPy architecture & usage
│   ├── index.md                 # DSPy overview
│   ├── signatures.md            # All DSPy signatures
│   ├── modules.md               # All DSPy modules
│   ├── programs.md              # DSPy programs
│   └── optimization.md          # MIPROv2, GEPA, caching
├── api/                        # FastAPI REST API
│   ├── index.md                 # API overview
│   ├── endpoints.md             # REST endpoint reference
│   ├── schemas.md               # Request/response models
│   ├── middleware.md            # CORS, error handling
│   └── jobs.md                  # Background jobs
├── cli/                        # CLI documentation
│   ├── index.md                 # CLI overview
│   ├── commands.md              # Command reference
│   ├── interactive-chat.md      # Chat mode guide
│   └── architecture.md          # CLI internals
├── llm/                        # LLM configuration
│   ├── index.md                 # Configuration overview
│   ├── providers.md             # Provider setup
│   ├── dspy-config.md           # Centralized config
│   └── task-models.md           # Task-specific models
├── hitl/                       # HITL system
│   ├── index.md                 # HITL overview
│   ├── callbacks.md             # Callback interface
│   ├── interactions.md          # Interaction types
│   └── runner.md                # HITL runner
├── concepts/
│   ├── concept-guide.md         # Concepts overview
│   └── developer-reference.md   # DSPy workflows, HITL, taxonomy concepts
├── agentskills-compliance.md   # Schema/validation
├── api-reference.md            # FastAPI + programmatic surface
├── cli-reference.md            # Command reference
├── overview.md                 # High-level architecture and taxonomy
├── architecture/
│   └── skill-creation-workflow.md # 3-phase workflow
└── development/
    ├── CONTRIBUTING.md         # Contribution guide
    └── ARCHITECTURE_DECISIONS.md # Design decisions
```

## Next Steps

1. **Getting Started**: Read [`docs/getting-started/index.md`](../getting-started/) for installation and basic usage
2. **DSPy Deep Dive**: Explore [`docs/dspy/`](../dspy/) to understand the 3-phase workflow architecture
3. **API Usage**: Check [`docs/api/`](../api/) for REST API integration
4. **CLI Reference**: See [`docs/cli/`](../cli/) for command details
5. **Advanced Topics**: Visit [`docs/llm/`](../llm/), [`docs/hitl/`](../hitl/) for configuration details

**New Documentation** 📚:
- [`docs/dspy/`](../dspy/) - Comprehensive DSPy guide (signatures, modules, programs, optimization)
- [`docs/api/`](../api/) - Complete REST API documentation (endpoints, schemas, jobs)
- [`docs/cli/`](../cli/) - CLI reference with interactive chat mode
- [`docs/llm/`](../llm/) - LLM configuration and task-specific models
- [`docs/hitl/`](../hitl/) - Human-in-the-Loop system documentation
