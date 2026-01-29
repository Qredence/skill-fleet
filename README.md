# Skill Fleet

A modular AI capability platform that creates, manages, and deploys agent skills as reusable, standards-compliant components.

**Skill Fleet** transforms how AI agents learn by organizing capabilities in a hierarchical taxonomy. Instead of bloated monolithic prompts, skills are modular, versioned, and discoverable—loaded on-demand when agents need them.

> **Perfect for**: AI teams building agent systems, platform engineers managing capability libraries, and organizations standardizing AI knowledge management.

---

## Why Skill Fleet?

### For Technical Teams

- **DSPy-Powered Workflows**: Built on DSPy with task-based orchestrators for reliable skill generation
- **FastAPI Architecture**: Clean API layer with background tasks, dependency injection, and async support
- **agentskills.io Compliant**: Standard YAML frontmatter ensures skills work across different agent frameworks
- **Hierarchical MLflow Tracking**: Parent runs for workflows, child runs for each phase

### For Decision Makers

- **Modular & Maintainable**: Skills are versioned, tracked, and independently testable
- **Standards-Based**: Open specification compliance prevents vendor lock-in
- **Scalable**: Hierarchical taxonomy supports hundreds of skills with organized growth

### For Everyone

- **Easy to Use**: Chat interface for creating skills without coding
- **Validated**: Automated compliance checking ensures quality
- **Observable**: Built-in analytics and usage tracking

---

## Quick Start

Create your first skill in under 2 minutes:

```bash
# 1. Install dependencies
uv sync --group dev
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 2. Start the API server
uv run skill-fleet serve

# 3. Create a skill via chat (in a new terminal)
uv run skill-fleet chat "Create a Python decorators skill"
```

The skill is created as a draft. After reviewing it in `drafts/<job_id>/`, promote it:

```bash
uv run skill-fleet promote <job_id>
```

---

## Prerequisites

- **Python**: 3.12+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **API Keys**: `GOOGLE_API_KEY` (Gemini is the default model)

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Qredence/skill-fleet.git
cd skill-fleet

# Install dependencies
uv sync

# Setup environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

---

## Interactive Workflows

### 💬 Real-Time Chat

Build skills with streaming updates and live reasoning display:

```bash
uv run skill-fleet chat "Create a Redis caching skill"
```

Features:
- Real-time progress updates (100ms polling)
- Live thinking/reasoning display
- Arrow key navigation for multi-choice questions
- HITL (Human-in-the-Loop) integration

### 📊 Validation & Quality

Validate skills against agentskills.io standards:

```bash
# Validate a skill
uv run skill-fleet validate skills/python/decorators

# Check compliance
uv run skill-fleet validate --strict skills/general/testing
```

### 🧠 DSPy Optimization

Tune prompts using MIPROv2 or GEPA optimizers:

```bash
uv run skill-fleet optimize --optimizer miprov2
```

---

## API Reference

### v1 API (Current)

The v1 API provides comprehensive skill management:

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/skills` | Create skill (starts background job) |
| `GET /api/v1/skills/{id}` | Get skill details |
| `PUT /api/v1/skills/{id}` | Update skill |
| `POST /api/v1/skills/{id}/validate` | Validate skill |
| `POST /api/v1/skills/{id}/refine` | Refine with feedback |
| `GET /api/v1/jobs/{id}` | Check job status |
| `GET /api/v1/hitl/{job_id}` | Poll for HITL prompts |
| `POST /api/v1/hitl/{job_id}` | Submit HITL response |

### CLI Commands

| Command | Description |
|---------|-------------|
| `skill-fleet serve` | Start FastAPI server |
| `skill-fleet chat` | Interactive skill creation |
| `skill-fleet list` | List all skills |
| `skill-fleet promote <id>` | Promote draft to taxonomy |
| `skill-fleet validate <path>` | Validate skill |
| `skill-fleet terminal` | Python-only CLI interface |

---

## Project Structure

```text
skill-fleet/
├── src/skill_fleet/
│   ├── api/                 # FastAPI application
│   │   ├── v1/             # API v1 routes
│   │   ├── services/       # Business logic layer
│   │   └── schemas/        # Pydantic models
│   ├── cli/                # Typer-based CLI
│   │   └── commands/
│   │       ├── chat.py     # Interactive chat
│   │       └── terminal.py # Python-only interface
│   ├── core/               # Domain logic
│   │   ├── workflows/      # Task-based orchestrators
│   │   ├── modules/        # DSPy modules
│   │   └── signatures/     # DSPy signatures
│   ├── dspy/               # Centralized DSPy config
│   ├── infrastructure/     # Technical infrastructure
│   │   ├── db/            # Database layer
│   │   └── tracing/       # MLflow integration
│   ├── taxonomy/          # Skill taxonomy management
│   └── validators/        # Skill validation
├── skills/                # Skill taxonomy
│   ├── _core/            # Always-loaded skills
│   ├── python/           # Python skills
│   ├── devops/           # DevOps skills
│   └── ...
├── tests/
│   ├── api/              # API tests
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── config/               # Configuration
└── docs/                 # Documentation
```

---

## Architecture

### FastAPI-Centric Design

The v0.3.5 restructure introduces a clean, FastAPI-centric architecture:

1. **API Layer** (`api/`): Routes, schemas, and dependency injection
2. **Service Layer** (`api/services/`): Business logic bridging API to workflows
3. **Workflow Layer** (`core/workflows/`): Task-based DSPy orchestrators
4. **Infrastructure** (`infrastructure/`): Database, tracing, monitoring

### Workflow Orchestrators

Three-phase skill creation with HITL support:

1. **Understanding Workflow**: Analyzes requirements, generates plan
2. **Generation Workflow**: Creates skill content
3. **Validation Workflow**: Checks compliance, refines content

Each phase runs in a child MLflow run under a parent workflow run.

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key |
| `SKILL_FLEET_ENV` | No | `production` or `development` |
| `SKILL_FLEET_CORS_ORIGINS` | Prod | Allowed origins (comma-separated) |
| `DSPY_CACHEDIR` | No | DSPy cache directory |
| `DSPY_TEMPERATURE` | No | Override LLM temperature |

### Config File

Edit `config/config.yaml` for:
- Model settings (default: `gemini/gemini-2-flash`)
- Optimizer configurations (MIPROv2, GEPA)
- Task-specific model assignments

---

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=skill_fleet
```

### Linting & Formatting

```bash
# Check and fix
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Project Standards

- **Python**: 3.12+ with modern type hints (`str | None`)
- **Line Length**: 100 characters
- **Quotes**: Double quotes
- **Docstrings**: Google style
- **Imports**: Absolute only, no relative imports

---

## Documentation

### Getting Started

- [Getting Started Guide](docs/getting-started/index.md) - Installation and first steps
- [Quick Start](docs/getting-started/STREAMING_QUICKSTART.md) - Streaming chat guide

### Core Concepts

- [System Overview](docs/index.md) - Architecture and concepts
- [AGENTS.md](AGENTS.md) - Comprehensive working guide
- [Developer Reference](docs/concepts/developer-reference.md)

### API & Technical

- [API v1 Documentation](docs/api/index.md) - REST API reference
- [API Migration](docs/api/MIGRATION_V1_TO_V2.md) - v1 to v2 migration guide
- [DSPy Framework](docs/dspy/index.md) - Workflow documentation
- [Import Path Guide](docs/development/IMPORT_PATH_GUIDE.md) - Import conventions
- [Service Extension](docs/development/SERVICE_EXTENSION_GUIDE.md) - Adding services

### Advanced

- [HITL System](docs/architecture/CONVERSATIONAL_INTERFACE.md) - Human-in-the-Loop
- [agentskills.io Compliance](docs/concepts/agentskills-compliance.md) - Standards
- [Background Jobs](docs/architecture/BACKGROUND_JOBS.md) - Async job processing

---

## Migration from v0.2.x

See [docs/api/MIGRATION_V1_TO_V2.md](docs/api/MIGRATION_V1_TO_V2.md) for:
- Import path changes
- API endpoint updates
- Architecture changes
- Breaking changes and deprecations

---

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for development workflow.

---

**Version**: 0.3.5  
**Status**: Production Ready  
**Last Updated**: January 2026
