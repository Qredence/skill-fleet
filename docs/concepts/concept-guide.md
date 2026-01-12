# Skill Fleet Concepts

## Core Concepts

### Taxonomy & Skills
- Skills live under `skills/` with a hierarchical path (`domain/subdomain/topic`).
- Each skill includes `SKILL.md` (frontmatter + body) and `metadata.json` (version, type, load priority).
- The taxonomy manager (`src/skill_fleet/taxonomy/manager.py`) enforces naming, handles `register_skill()`, and generates XML for discoverability.

### DSPy Workflow
- FastAPI triggers `SkillCreationProgram` (`src/skill_fleet/core/programs/skill_creator.py`) which runs three phases: understanding, generation, validation.
- HITL callbacks surface prompts to the CLI via `/api/v2/hitl/{job_id}`. CLI interacts with `src/skill_fleet/cli/hitl/runner.py`.
- Templates (SKILL.md + metadata) are fed into Phase 2 instructions to steer the model’s output.

### HITL & Human Feedback
- The job loop transitions through `clarify`, `confirm`, `preview`, `validate`.
- The CLI uses a shared runner to display prompts, capture feedback, and resume jobs (auto-approve option available).
- Job states are stored in `src/skill_fleet/api/jobs.py`; hitting `/api/v2/hitl/*` polls and posts the responses.

### Templates & Compliance
- `config/templates/SKILL_md_template.md` describes required YAML frontmatter and body structure.
- `config/templates/metadata_template.json` outlines optional metadata fields (capabilities, dependencies, evolution).
- `TaxonomyManager.register_skill()` uses these templates to write consistent artifacts.

### Opening a New Concept Document

When a concept requires more detail (e.g., DSPy tuning, taxonomy expansion), add a file under `docs/concepts/` and link it from here.

---

## Further Reading

### In-Depth Documentation

| Topic | Description |
|-------|-------------|
| **[DSPy Documentation](../dspy/)** | 3-phase workflow, signatures, modules, programs, optimization |
| **[API Documentation](../api/)** | REST API endpoints, schemas, jobs, middleware |
| **[CLI Documentation](../cli/)** | Command reference, interactive chat, architecture |
| **[LLM Configuration](../llm/)** | Provider setup, DSPy config, task-specific models |
| **[HITL System](../hitl/)** | Callbacks, interactions, runner implementation |

### Concept Guides

- **[Developer Reference](developer-reference.md)** - Development workflows and patterns
- **[agentskills.io Compliance](../agentskills-compliance.md)** - Schema and validation rules
- **[Getting Started](../getting-started/)** - Installation, quick start, templates
