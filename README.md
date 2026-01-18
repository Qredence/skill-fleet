# Skills Fleet

A modular AI capability platform that keeps agent skills organized, discoverable, and standards-compliant.

**Skills Fleet** lets you create, manage, and deploy AI agent skills as modular, reusable components. Instead of bloated monolithic prompts, skills are organized in a hierarchical taxonomy that agents can load on-demand.

> **Perfect for**: AI development teams building agent systems, platform engineers managing AI capability libraries, and organizations standardizing AI knowledge management.

## Why Skills Fleet?

### For Technical Teams
- **DSPy-Powered Optimization**: Built on DSPy (a framework for optimizing LLM workflows) with MIPROv2 and GEPA optimizers for reliable, consistent skill generation.
- **agentskills.io Compliant**: Standard YAML frontmatter ensures skills work across different agent frameworks.
- **Production-Ready**: FastAPI v2 server with async background jobs and comprehensive testing.

### For Decision Makers
- **Modular & Maintainable**: Skills are versioned, tracked, and independently testable.
- **Standards-Based**: Open specification compliance prevents vendor lock-in.
- **Scalable**: Hierarchical taxonomy for organized growth, supporting hundreds of skills.

### For Everyone
- **Easy to Use**: Simple chat interface for creating skills without coding.
- **Validated**: Automated compliance checking ensures quality.
- **Observable**: Built-in analytics and usage tracking.

## Prerequisites

- **Python**: 3.12+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **API Keys**: `GOOGLE_API_KEY` (Gemini 3 Flash is the default model)

## Installation

```bash
# Clone the repository
git clone https://github.com/Qredence/skill-fleet.git
cd skill-fleet

# Install dependencies
uv sync

# Setup environment variables
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## Quick Start

Create your first skill in under 2 minutes:

1. **Start the API server**:
   ```bash
   uv run skill-fleet serve
   ```

2. **Create a skill via chat** (in a new terminal):
   ```bash
   uv run skill-fleet chat "Create a Python decorators skill"
   ```

3. **Review and Promote**:
   The skill is created as a draft. After reviewing it in `skills/_drafts/<job_id>`, promote it:
   ```bash
   uv run skill-fleet promote <job_id>
   ```

**Note**: Taxonomy v0.2 uses simplified paths (e.g., `python/decorators` instead of `technical_skills/programming/languages/python/decorators`). Legacy paths still resolve with deprecation warnings.

## Core Commands

| Command | Description |
|---------|-------------|
| `uv run skill-fleet serve` | Start the FastAPI v2 server (required for most operations) |
| `uv run skill-fleet chat` | Interactive conversational skill creation |
| `uv run skill-fleet list` | List all skills in the taxonomy |
| `uv run skill-fleet promote <id>` | Promote a draft skill to the permanent taxonomy |
| `uv run skill-fleet validate <path>`| Validate a skill against agentskills.io standards |
| `uv run skill-fleet generate-xml`| Generate an XML registry for agent discovery |
| `uv run skill-fleet optimize` | Run DSPy MIPROv2/GEPA optimization |
| `uv run skill-fleet analytics` | View usage and performance statistics |

## Project Structure

```text
skill-fleet/
├── src/skill_fleet/
│   ├── agent/          # Conversational agent for skill creation
│   ├── api/            # FastAPI v2 REST API & routes
│   ├── cli/            # Typer-based CLI (fleet-agent)
│   ├── core/           # Core logic (DSPy programs, tools, models)
│   ├── llm/            # LLM configuration and DSPy setup
│   ├── taxonomy/       # Skill taxonomy management & index
│   ├── validators/     # Skill validation logic
│   └── onboarding/     # User onboarding & skill bootstrapping
├── skills/             # Simplified 2-level taxonomy (category/skill)
│   ├── taxonomy_index.json  # Canonical paths & alias mappings
│   ├── python/          # Python-related skills
│   ├── devops/          # DevOps & containerization skills
│   ├── testing/         # Testing framework skills
│   ├── web/             # Web development skills
│   └── ...             # Other categories
├── tests/              # Unit and integration tests
├── config/             # Configuration files (config.yaml, templates)
├── scripts/            # Utility, migration & maintenance scripts
└── docs/               # Comprehensive documentation
```

## Configuration

The system is configured via `config/config.yaml`. This file defines:
- **Models**: Default model is `gemini/gemini-3-flash-preview`.
- **Roles**: Router, Planner, Worker, Judge.
- **Optimizers**: Settings for MIPROv2 and GEPA.

### Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini models.
- `SKILL_FLEET_ENV`: (Optional) `production` (default) or `development`.
- `SKILL_FLEET_CORS_ORIGINS`: Required in production. Comma-separated list of allowed origins. Set to `*` only in `development`.
- `SKILL_FLEET_API_URL`: (Optional) Defaults to `http://localhost:8000`.
- `DSPY_TEMPERATURE`: (Optional) Override default LLM temperature.

## Development & Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=skill_fleet
```

### Linting & Formatting
Uses [Ruff](https://docs.astral.sh/ruff/) for high-performance linting:
```bash
uv run ruff check .
uv run ruff format .
```

### Utility Scripts
- `scripts/setup_branch_protection.sh`: Configure GitHub branch protection.
- `scripts/run_dspy_tools.py`: Run DSPy optimization and evaluation tools.
- `scripts/check_docstrings.py`: Verify documentation completeness.

## Documentation

- [Getting Started](docs/getting-started/index.md)
- [DSPy Architecture](docs/dspy/index.md)
- [CLI Reference](docs/cli/commands.md)
- [API Endpoints](docs/api/endpoints.md)

## License

Apache License 2.0. See `LICENSE`.

## Contributing

Please see [CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for details on our development workflow.
