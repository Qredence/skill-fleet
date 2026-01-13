# Skill Fleet

A hierarchical, DSPy-powered capability platform that keeps AI agent knowledge modular, discoverable, and agentskills.io compliant. Skill Fleet uses a conversational agent, FastAPI background jobs, DSPy programs with MIPROv2/GEPA optimization, and a React/TypeScript frontend so that you can create, validate, and operate skills with confidence.

## Documentation Structure

Skill Fleet documentation follows a “intro → getting started → concepts” path:

- **Introduction** (`docs/intro/introduction.md`): purpose, doc map, and navigation cues.
- **Getting Started** (`docs/getting-started/index.md`): install, CLI/API workflows, templates, and validation flows.
- **Concepts** (`docs/concepts/concept-guide.md`): taxonomy, DSPy workflow, HITL, and templates.
- **Developer Reference** (`docs/concepts/developer-reference.md`): deep architecture, DSPy programs, testing, and contribution guidance.
- **References**: `docs/cli-reference.md`, `docs/api-reference.md`, `docs/agentskills-compliance.md`, `docs/overview.md`.
- **Working guide**: `AGENTS.md` is the day-to-day instructions for agents/developers.

## Installation & Setup

```bash
git clone https://github.com/Qredence/skill-fleet.git
cd skill-fleet
uv sync --group dev
bun install  # optional, needed for the TUI
cp .env.example .env
# Edit .env to export GOOGLE_API_KEY, DSPY_CACHEDIR, DSPY_TEMPERATURE, etc.
```

## Getting Started

1. Start the API server (`uv run skill-fleet serve` or `--reload` in dev).
2. Run `uv run skill-fleet chat` (RECOMMENDED) or `uv run skill-fleet create "..."` to launch the conversational agent with 3-phase skill creation workflow.
3. Optimize workflows with `uv run skill-fleet optimize --optimizer miprov2` or `--optimizer gepa`.
4. Validate with `uv run skill-fleet validate skills/<path>` and migrate legacy skills via `uv run skill-fleet migrate --dry-run`.
5. Generate `<available_skills>` XML (`uv run skill-fleet generate-xml`) and review analytics (`uv run skill-fleet analytics`).

# Getting Started Highlights

1. Start the API server (`uv run skill-fleet serve` or `--reload` in dev).
2. Run `uv run skill-fleet chat` (RECOMMENDED) or `uv run skill-fleet create "..."` to launch the conversational agent with 3-phase skill creation workflow.
3. Optimize workflows with `uv run skill-fleet optimize --optimizer miprov2` or `--optimizer gepa`.
4. Validate with `uv run skill-fleet validate skills/<path>` and migrate legacy skills via `uv run skill-fleet migrate --dry-run`.
5. Generate `<available_skills>` XML (`uv run skill-fleet generate-xml`) and review analytics (`uv run skill-fleet analytics`).

## Core Commands

| Command | Purpose |
| --- | --- |
| `uv run skill-fleet serve` | Run the FastAPI server (job + HITL endpoints). |
| `uv run skill-fleet chat` | **RECOMMENDED**: Conversational agent with 3-phase skill creation workflow. |
| `uv run skill-fleet create "task"` | Create a skill via DSPy + HITL (direct task mode). |
| `uv run skill-fleet optimize` | Optimize DSPy workflows with MIPROv2 or GEPA. |
| `uv run skill-fleet analytics` | View usage analytics and skill patterns. |
| `uv run skill-fleet validate <skill>` | Check frontmatter/metadata compliance. |
| `uv run skill-fleet migrate` | Upgrade legacy skills to the modern schema. |
| `uv run skill-fleet generate-xml` | Produce agentskills.io `<available_skills>`. |
| `uv run skill-fleet list` | Enumerate skills stored in `skills/`. |
| `uv run skill-fleet onboard` | Run user onboarding workflow. |

# Documentation Tree

```
docs/
├── intro/              # introduction and doc map
├── getting-started/     # install, CLI/API guides, templates, validation
├── concepts/            # taxonomy/DSPy/HITL concepts + developer reference
├── cli-reference.md
├── api-reference.md
├── agentskills-compliance.md
├── overview.md
└── ...
```

## Testing & Quality

```bash
UV_CACHE_DIR=$PWD/.uv_cache uv run ruff check src/skill_fleet
UV_CACHE_DIR=$PWD/.uv_cache uv run pytest -q tests/unit
```

## Documentation & Contribution Paths

- Keep `AGENTS.md` and `plans/` in sync with any workflow changes.
- Author new UX or API features via ExecPlans (see `plans/README.md` and `plans/2026-01-12-cli-chat-ux.md`).
- Update the new User/Developer guides when CLI or API behaviors shift.
