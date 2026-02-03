# 🚀 Skill Fleet

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**A local-first platform for creating, validating, and curating AI agent skills as standards-compliant artifacts.**

Skill Fleet transforms natural language descriptions into production-ready agent skills using an intelligent three-phase workflow: Understanding → Generation → Validation. Built on [DSPy](https://github.com/stanfordnlp/dspy) for reliable, optimizable LLM programs.

```bash
# Create a skill in minutes
uv run skill-fleet chat "Create a React hooks mastery skill for intermediate developers"
```

---

## ✨ Why Skill Fleet?

Traditional prompt engineering creates fragile, unversioned prompts that break when models change. Skill Fleet creates **structured, validated, reusable artifacts** that agentskills.io-compliant agents can consume.

### Key Differentiators

| Feature | Traditional Prompts | Skill Fleet |
|---------|-------------------|-------------|
| **Creation** | Manual, trial-and-error | AI-assisted, structured workflow |
| **Validation** | Ad-hoc testing | Multi-phase validation with quality gates |
| **Format** | Plain text | agentskills.io compliant SKILL.md |
| **Dependencies** | Implicit | Explicitly declared and validated |
| **Versioning** | None | Git-tracked with promotion workflow |
| **Discovery** | None | Hierarchical taxonomy with search |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **uv** package manager
- **Git**
- **API Key**: Google (Gemini) or LiteLLM proxy

### Installation

```bash
# Clone and setup
git clone https://github.com/qredence/skill-fleet.git
cd skill-fleet
uv sync --group dev

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY or LITELLM credentials
```

### First Skill Creation

```bash
# Start the API server
uv run skill-fleet serve

# In another terminal, create a skill interactively
uv run skill-fleet chat "Create a skill for Python decorators"

# Or create non-interactively with auto-approval
uv run skill-fleet create "Build a React testing skill" --auto-approve

# Validate the generated skill
uv run skill-fleet validate skills/_drafts/<job_id>

# Promote to taxonomy when ready
uv run skill-fleet promote <job_id>
```

---

## 🏗️ Architecture

Skill Fleet uses a **three-phase workflow** powered by DSPy:

```
User Request
    ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Understanding                                 │
│  - Extract requirements                                 │
│  - Analyze intent                                       │
│  - Build execution plan                                 │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: Generation                                    │
│  - Create SKILL.md with YAML frontmatter                │
│  - Generate code examples                               │
│  - Apply category-specific templates                    │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: Validation                                    │
│  - Structure validation                                 │
│  - Compliance checking                                  │
│  - Quality assessment (Best-of-N)                       │
└─────────────────────────────────────────────────────────┘
    ↓
Draft Ready for Review → Promote to Taxonomy
```

### Draft-First Workflow

1. **Draft Phase**: Skills are generated into `skills/_drafts/<job_id>/`
2. **Review Phase**: Human-in-the-loop (HITL) for feedback and refinement
3. **Promotion Phase**: Validated skills moved to stable taxonomy paths

---

## 📋 CLI Reference

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `serve` | Start FastAPI server | `uv run skill-fleet serve --reload` |
| `dev` | Start server + TUI | `uv run skill-fleet dev` |
| `chat` | Interactive skill creation | `uv run skill-fleet chat "Create..."` |
| `create` | Non-interactive creation | `uv run skill-fleet create "..." --auto-approve` |
| `validate` | Validate skill directory | `uv run skill-fleet validate ./skills/_drafts/job_123` |
| `promote` | Promote draft to taxonomy | `uv run skill-fleet promote job_123` |
| `generate-xml` | Export skills as XML | `uv run skill-fleet generate-xml` |

### Server Options

```bash
# Development mode with auto-reload
uv run skill-fleet serve --reload

# Skip database initialization
uv run skill-fleet serve --skip-db-init

# Custom port
uv run skill-fleet serve --port 8080
```

### Validation Options

```bash
# Validate with JSON output for scripting
uv run skill-fleet validate ./my-skill --json

# Strict validation (fail on warnings)
uv run skill-fleet validate ./my-skill --strict
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes* | Gemini API key (or use LiteLLM) |
| `LITELLM_API_KEY` | Yes* | LiteLLM proxy API key |
| `LITELLM_BASE_URL` | With LiteLLM | LiteLLM proxy endpoint |
| `DATABASE_URL` | Production | PostgreSQL connection string |
| `SKILL_FLEET_ENV` | No | `development` (default) or `production` |
| `SKILL_FLEET_CORS_ORIGINS` | Production | Comma-separated allowed origins |

\* Choose either Google API key OR LiteLLM credentials.

### Development vs Production

**Development Mode** (`SKILL_FLEET_ENV=development`):
- SQLite fallback (no DATABASE_URL required)
- CORS allows `*`
- Debug logging
- Auto-reload enabled

**Production Mode** (`SKILL_FLEET_ENV=production`):
- PostgreSQL required
- Explicit CORS origins required
- Structured logging
- Security headers enabled

---

## 🌐 API Reference

When the server is running, access interactive documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/skills` | POST | Create skill (returns job ID) |
| `/api/v1/skills/stream` | POST | Create skill with SSE streaming |
| `/api/v1/skills/{id}` | GET | Get skill by ID |
| `/api/v1/jobs/{id}` | GET | Get job status and results |
| `/api/v1/taxonomy` | GET | List taxonomy categories |
| `/api/v1/hitl/responses` | POST | Submit HITL response |

### Streaming API

For real-time progress updates:

```bash
curl -X POST http://localhost:8000/api/v1/skills/stream \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Create a Python asyncio skill",
    "user_id": "developer-1",
    "enable_hitl": true
  }'
```

Returns Server-Sent Events (SSE) with:
- Phase transitions (Understanding → Generation → Validation)
- Real-time reasoning and thoughts
- Progress updates
- HITL suspension points

---

## 🧪 Development

### Setup

```bash
# Install dependencies
uv sync --group dev

# Run linting and formatting
uv run ruff check --fix .
uv run ruff format .

# Run type checker
uv run ty check

# Run tests
uv run pytest

# Run specific test
uv run pytest tests/unit/test_async_utils.py -v
```

### Pre-commit Hooks

```bash
# Install hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

### Project Structure

```
src/skill_fleet/
├── api/                    # FastAPI application
│   ├── v1/                 # API endpoints (skills, jobs, HITL)
│   └── services/           # Business logic layer
├── cli/                    # Typer CLI application
├── core/                   # Core business logic
│   ├── modules/            # DSPy modules (generation, validation)
│   ├── signatures/         # DSPy signatures
│   └── workflows/          # Workflow orchestration
├── taxonomy/               # Taxonomy management
└── infrastructure/         # Database, monitoring, tracing
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/README.md`](docs/README.md) | Documentation index and navigation |
| [`docs/tutorials/getting-started.md`](docs/tutorials/getting-started.md) | Step-by-step onboarding |
| [`docs/how-to-guides/create-a-skill.md`](docs/how-to-guides/create-a-skill.md) | End-to-end creation guide |
| [`docs/how-to-guides/validate-a-skill.md`](docs/how-to-guides/validate-a-skill.md) | Validation details |
| [`docs/reference/api/endpoints.md`](docs/reference/api/endpoints.md) | Complete API reference |
| [`AGENTS.md`](AGENTS.md) | Development workflow guide |
| [`SECURITY.md`](SECURITY.md) | Security policy |

---

## 🤝 Contributing

We welcome contributions! Please see [`docs/explanation/development/contributing.md`](docs/explanation/development/contributing.md) for guidelines.

### Quick Contribution Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`uv run pre-commit run --all-files`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📄 License

Apache License 2.0. See [`LICENSE`](LICENSE) for details.

---

## 🔗 Related Projects

- **[DSPy](https://github.com/stanfordnlp/dspy)** - The framework powering our LLM programs
- **[agentskills.io](https://agentskills.io)** - The skill standard we implement
- **[LiteLLM](https://github.com/BerriAI/litellm)** - Proxy for multiple LLM providers

---

**Version**: 0.3.5
**Status**: Alpha
**Last Updated**: 2026-02-02

Built with ❤️ by the Qredence team
