# Skill Fleet Concepts

## Core Concepts

### Taxonomy & Skills
- Skills live under `skills/` with a hierarchical path (`domain/subdomain/topic`).
- Each skill includes `SKILL.md` (frontmatter + body) and `metadata.json` (version, type, load priority).
- The taxonomy manager (`src/skill_fleet/taxonomy/manager.py`) enforces naming, handles `register_skill()`, and generates XML for discoverability.

### DSPy Workflow Architecture

Skill Fleet uses a clean three-layer architecture:

1. **Signatures** (`core/signatures/`): Type definitions using `dspy.Signature`
2. **Modules** (`core/modules/`): Reusable business logic with `forward()`/`aforward()`
3. **Workflows** (`core/workflows/`): High-level orchestration with HITL support

The workflow executes three phases:
- **Understanding**: Requirements gathering, intent analysis, taxonomy path finding, dependency analysis
- **Generation**: Content generation using structured templates
- **Validation**: Compliance checking and quality assessment with auto-refinement

### HITL & Human Feedback
- The workflow supports HITL checkpoints at any phase: `clarify`, `confirm`, `preview`, `validate`
- HITL callbacks surface prompts to the CLI via the job system
- The CLI uses a shared runner to display prompts, capture feedback, and resume jobs
- Job states are managed by `JobManager` in `src/skill_fleet/api/services/`

### Templates & Compliance
- `config/templates/SKILL_md_template.md` describes required YAML frontmatter and body structure.
- `config/templates/metadata_template.json` outlines optional metadata fields (capabilities, dependencies, evolution).
- `TaxonomyManager.register_skill()` uses these templates to write consistent artifacts.

### Centralized DSPy Configuration

DSPy configuration is centralized in `skill_fleet.dspy`:

```python
from skill_fleet.dspy import configure_dspy, get_task_lm

# Configure once at startup
configure_dspy()

# Get task-specific language models
lm = get_task_lm("skill_understand")
edit_lm = get_task_lm("skill_edit")
```

### Opening a New Concept Document

When a concept requires more detail (e.g., DSPy workflows, taxonomy expansion), add a file under `docs/concepts/` and link it from here.

---

## Further Reading

### In-Depth Documentation

| Topic | Description |
|-------|-------------|
| **[Architecture Status](../architecture/restructuring-status.md)** | Current architecture overview and migration details |
| **[Import Path Guide](../development/IMPORT_PATH_GUIDE.md)** | Canonical import paths for the new architecture |
| **[API Documentation](../api/)** | REST API endpoints, schemas, jobs, middleware |
| **[CLI Documentation](../cli/)** | Command reference, interactive chat, architecture |
| **[HITL System](../hitl/)** | Callbacks, interactions, runner implementation |

### Concept Guides

- **[Developer Reference](developer-reference.md)** - Development workflows and patterns
- **[agentskills.io Compliance](agentskills-compliance.md)** - Schema and validation rules
- **[Getting Started](../getting-started/)** - Installation, quick start, templates

### Architecture Documentation

- **[Domain Layer](../architecture/DOMAIN_LAYER.md)** - DDD patterns and entities
- **[Service Layer](../architecture/SERVICE_LAYER.md)** - Service architecture
- **[Background Jobs](../architecture/BACKGROUND_JOBS.md)** - Job system design
- **[Caching Layer](../architecture/CACHING_LAYER.md)** - Caching implementation
