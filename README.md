# Skills Fleet

A modular AI capability platform that keeps agent skills organized, discoverable, and standards-compliant.

**Skills Fleet** lets you create, manage, and deploy AI agent skills as modular, reusable components. Instead of bloated monolithic prompts, skills are organized in a hierarchical taxonomy that agents can load on-demand.

> **Perfect for**: AI development teams building agent systems, platform engineers managing AI capability libraries, and organizations standardizing AI knowledge management.

## Why Skills Fleet?

### For Technical Teams

- **DSPy-Powered Optimization**: Built on DSPy (a framework for optimizing LLM workflows) with MIPROv2 and GEPA optimizers for reliable, consistent skill generation
- **agentskills.io Compliant**: Standard YAML frontmatter ensures skills work across different agent frameworks
- **Production-Ready**: FastAPI v2 server with async background jobs and comprehensive testing

### For Decision Makers

- **Modular & Maintainable**: Skills are versioned, tracked, and independently testable
- **Standards-Based**: Open specification compliance prevents vendor lock-in
- **Scalable**: 100+ skills in the library with hierarchical taxonomy for organized growth

### For Everyone

- **Easy to Use**: Simple chat interface for creating skills without coding
- **Validated**: Automated compliance checking ensures quality
- **Observable**: Built-in analytics and usage tracking

## Quick Start

Create your first skill in under 2 minutes:

```bash
# 1. Install dependencies
uv sync --group dev

# 2. Configure your API key
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 3. Start the API server
uv run skill-fleet serve

# 4. Create a skill (in a new terminal)
uv run skill-fleet chat "Create a Python decorators skill"
```

**What happens next:**

The conversational agent guides you through a 3-phase workflow:

1. **Understanding**: "I'll help you create a Python decorators skill. Should this focus on basic decorators, class-based decorators, or both?"
2. **Generation**: Creates the skill with YAML frontmatter, capabilities, examples, and tests
3. **Validation**: Runs compliance checks and saves to `skills/technical_skills/programming/languages/python/decorators/`

**Result**: A production-ready skill with agentskills.io-compliant metadata, ready to be deployed.

```bash
# 5. Verify your skill
uv run skill-fleet list

# 6. Generate XML for agent integration
uv run skill-fleet generate-xml -o available_skills.xml
```

**That's it!** You now have a validated, standards-compliant skill that can be discovered and used by any agent system.

## How Skills Fleet Works

Skills Fleet combines three innovative technologies:

### 1. DSPy-Powered 3-Phase Workflow

Every skill goes through a rigorous creation process:

- **Phase 1: Understanding & Planning** — Analyzes requirements, researches context, maps to taxonomy
- **Phase 2: Content Generation** — Generates SKILL.md, capabilities, examples, and tests
- **Phase 3: Validation & Refinement** — Runs compliance checks, enforces TDD checklist, iterates

### 2. MIPROv2 & GEPA Optimization

- **MIPROv2**: Automatically tunes prompts using training data for consistent quality
- **GEPA**: Reflective prompt evolution with critique cycle for complex reasoning tasks
- **Quality-Assured Mode**: Uses Refine and BestOfN wrappers for higher-quality outputs

### 3. agentskills.io Compliance

Every skill includes standardized YAML frontmatter:

```yaml
---
name: python-decorators
description: Ability to design, implement, and apply higher-order functions to extend or modify the behavior of functions and classes in Python.
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.0.0
  type: technical
  weight: medium
  load_priority: task_specific
  dependencies: []
  capabilities:
    - basic-function-decorators
    - parameterized-decorators
    - class-based-decorators
    - memoization
---
```

This ensures skills are discoverable, interoperable, and machine-readable.

### Architecture Overview

```
User Request → Conversational Agent → DSPy 3-Phase Workflow → Taxonomy Storage
                    ↓                           ↓                      ↓
              HITL Feedback              MIPROv2/GEPA           Validation

FastAPI Server ← Background Jobs ← Optimization Cache
```

## Core Commands

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `uv run skill-fleet serve` | Start FastAPI server | Required for create/chat/list |
| `uv run skill-fleet chat` | **Recommended**: Conversational skill creation | Most skill creation workflows |
| `uv run skill-fleet create "task"` | Direct skill creation | CI/CD pipelines, scripting |
| `uv run skill-fleet optimize --optimizer miprov2` | Optimize DSPy workflows | Improving skill quality |
| `uv run skill-fleet validate <path>` | Validate skill compliance | Quality checks before commit |
| `uv run skill-fleet generate-xml` | Generate agentskills.io XML | Agent integration |
| `uv run skill-fleet analytics` | View usage statistics | Understanding skill patterns |
| `uv run skill-fleet list` | List all skills | Discovery and inventory |

**Full command reference**: See [CLI Documentation](docs/cli/commands.md)

## What Makes Skills Fleet Different?

| Feature | Skills Fleet | Traditional Prompt Management | Other Skill Systems |
|---------|--------------|-------------------------------|---------------------|
| **Skill Format** | agentskills.io compliant YAML frontmatter | Free-form prompts | Proprietary formats |
| **Creation Process** | DSPy-powered 3-phase workflow with HITL | Manual drafting | Simple templates |
| **Optimization** | MIPROv2 & GEPA prompt tuning | None | Manual iteration |
| **Validation** | Automated compliance checking | Manual review | Basic checks |
| **Discovery** | Hierarchical taxonomy + XML generation | Search by keyword | Flat lists |
| **Interoperability** | Standard specification compliant | Platform-specific | Limited |
| **Quality Assurance** | TDD checklist enforcement | None | Optional |
| **Analytics** | Built-in usage tracking | None | Rare |

**Bottom Line**: Skills Fleet is the only platform that combines DSPy's programmatic optimization, agentskills.io's open standards, and production-ready infrastructure in one integrated system.

## Project Structure

```
skills-fleet/
├── skills/                    # Hierarchical skills taxonomy (100+ skills)
│   ├── technical_skills/      # Programming, frameworks, tools
│   ├── domain_knowledge/      # Industry-specific knowledge
│   ├── task_focus_areas/      # Cross-cutting capabilities
│   └── _core/                 # Always-loaded foundational skills
├── src/skill_fleet/
│   ├── core/dspy/             # DSPy integration (modules, signatures, programs)
│   ├── api/                   # FastAPI v2 REST API
│   ├── cli/                   # Typer CLI with chat interface
│   ├── ui/                    # React/TypeScript TUI
│   └── validators/            # Compliance validation
├── docs/                      # Comprehensive documentation
│   ├── dspy/                  # DSPy architecture guide
│   ├── api/                   # API reference
│   ├── cli/                   # CLI documentation
│   └── getting-started/       # Installation & tutorials
├── tests/                     # Unit & integration tests
└── config/                    # LLM & workflow configuration
```

**Key directories to explore**:
- `docs/getting-started/` — Start here for hands-on tutorials
- `docs/dspy/` — Deep dive into DSPy optimization
- `docs/cli/` — Complete command reference
- `AGENTS.md` — Working guide for AI agents and developers

## Documentation & Resources

### Getting Started
- [Installation Guide](docs/getting-started/index.md) — Detailed setup instructions
- [Configuration](docs/llm/index.md) — LLM provider setup and DSPy configuration

### Core Concepts
- [DSPy Architecture](docs/dspy/index.md) — 3-phase workflow, signatures, modules, programs
- [agentskills.io Compliance](docs/agentskills-compliance.md) — Schema and validation rules
- [Concept Guide](docs/concepts/concept-guide.md) — Taxonomy and skill organization

### API & CLI Reference
- [CLI Commands](docs/cli/commands.md) — Complete command reference
- [REST API](docs/api/endpoints.md) — FastAPI endpoint documentation
- [Python API](docs/api-reference.md) — Programmatic usage

### Advanced Topics
- [Optimization Guide](docs/dspy/optimization.md) — MIPROv2 and GEPA tuning
- [HITL System](docs/hitl/index.md) — Human-in-the-loop workflows

### Development
- [Contributing Guide](docs/development/CONTRIBUTING.md) — Contribution workflow
- [Architecture Decisions](docs/development/ARCHITECTURE_DECISIONS.md) — Design rationale
- [AGENTS.md](AGENTS.md) — Working guide for agents/developers

### External Resources
- [agentskills.io Specification](https://agentskills.io) — Open standard for agent skills
- [DSPy Documentation](https://dspy.ai) — DSPy framework documentation

## Testing & Quality

Skills Fleet maintains high quality standards:

```bash
# Run linting
uv run ruff check src/skill_fleet

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/skill_fleet
```

**Quality metrics**:
- Comprehensive unit and integration tests
- Ruff linting for code consistency
- agentskills.io compliance validation
- DSPy workflow optimization with MLflow tracking

## Branch Protection & CI/CD

The repository uses branch protection rules to maintain code quality and security. See [Branch Protection Guide](.github/BRANCH_PROTECTION.md) for recommended protection settings, CI/CD workflow configuration, and setup instructions.

Quick setup:
```bash
./scripts/setup_branch_protection.sh
```

## License

[License information from your project]

## Contributing

We welcome contributions! Please see [Contributing Guide](docs/development/CONTRIBUTING.md) for details.

## Acknowledgments

Built with:
- [DSPy](https://dspy.ai) — Programmatic optimization for LLM workflows
- [FastAPI](https://fastapi.tiangolo.com) — Modern Python web framework
- [agentskills.io](https://agentskills.io) — Open specification for agent skills
