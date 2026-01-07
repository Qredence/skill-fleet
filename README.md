# Agentic Skills System (skills-fleet)

A hierarchical, dynamic capability framework for AI agents. This system enables agents to load and generate skills on-demand, optimizing performance and reducing context bloat through a "just-in-time" capability model.

## 🚀 Overview

The **Agentic Skills System (ASS)** addresses capability bloat in AI agents by organizing knowledge into a hierarchical taxonomy. Instead of massive system prompts, agents mount only the specific skills they need for a given task.

### Key Features
- **Hierarchical Taxonomy**: 8-level structure for organizing agent capabilities.
- **Dynamic Mounting**: Load skills on-demand, reducing context usage by up to 90%.
- **Just-In-Time Generation**: Automatically create new skills using DSPy-based workflows.
- **Stateful Memory**: Maintain context and learn from past interactions.
- **Hybrid Interface**: Powerful CLI for automation and an interactive TUI for management.
- **agentskills.io Compliant**: Full compliance with agentskills.io specification:
  - **YAML Frontmatter**: All skills include standardized metadata (`name`, `description`)
  - **XML Discoverability**: Generate agent-ready `<available_skills>` XML for context injection
  - **Migration Tools**: Convert existing skills to compliant format with automated validation
  - **Interoperability**: Share skills across different agent frameworks

---

## 🛠 Tech Stack

- **Language**: Python 3.12+ & TypeScript/React
- **Python Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Node Package Manager**: [bun](https://bun.sh/)
- **LLM Frameworks**: [DSPy](https://github.com/stanfordnlp/dspy), [LiteLLM](https://github.com/BerriAI/litellm)
- **TUI Framework**: [OpenTUI](https://github.com/opentui/opentui)
- **Quality Assurance**: Pytest (Testing), Ruff (Linting)

---

## 📋 Requirements

- **Python**: 3.12 or higher
- **Node.js/Bun**: For the TUI components
- **Zig**: Required for building `@opentui` core components
- **API Keys**: Google API Key (primary), DeepInfra (optional), LiteLLM (optional), Langfuse (optional)

---

## ⚙️ Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd skills-fleet
```

### 2. Install Python Dependencies
```bash
# Recommended: use uv
uv sync --group dev
```

### 3. Install TUI Dependencies
```bash
bun install
```

### 4. Configure Environment
Create a `.env` file in the root:
```bash
GOOGLE_API_KEY="your_key_here"
# Optional overrides
DEEPINFRA_API_KEY="your_key_here"
LITELLM_API_KEY="your_key_here"
LANGFUSE_SECRET_KEY="your_key_here"
```

---

## 🏃 Commands & Scripts

### CLI (Python)
The CLI is the primary way to interact with the skills system.

```bash
# General help
uv run skills-fleet --help

# Create a new skill (Full 6-step workflow with HITL)
uv run skills-fleet create-skill --task "Create a Python async programming skill"

# Create a skill with auto-approval (skips interactive review)
uv run skills-fleet create-skill --task "Create a Python async programming skill" --auto-approve

# Validate a skill directory
uv run skills-fleet validate-skill src/agentic_fleet/agentic_skills_system/skills/general/testing

# agentskills.io compliance tools
uv run skills-fleet migrate                    # Migrate existing skills to agentskills.io format
uv run skills-fleet migrate --dry-run          # Preview migration changes without writing
uv run skills-fleet generate-xml               # Generate <available_skills> XML for agent prompts
uv run skills-fleet generate-xml -o skills.xml # Save XML to file for context injection

# User onboarding
uv run skills-fleet onboard --user-id my_user_123

# View analytics
uv run skills-fleet analytics --user-id my_user_123
```

### TUI (TypeScript)
Launch the interactive terminal UI for skill management.

```bash
bun run tui
```

### Development & Testing
```bash
# Run tests
uv run pytest

# Linting
uv run ruff check .
```

---

## 📖 Documentation

*   [Quick Start](docs/quick-start.md) - Get up and running in minutes.
*   [Overview](docs/overview.md) - System architecture and core concepts.
*   [Skill Creator Guide](docs/skill-creator-guide.md) - Detailed instructions for generating new skills.
*   [CLI Reference](docs/cli-reference.md) - Complete command-line interface reference.
*   [API Reference](docs/api-reference.md) - Python API documentation for programmatic use.
*   [agentskills.io Compliance](docs/agentskills-compliance.md) - Guide to agentskills.io standard, YAML frontmatter, migration, and XML generation.
*   [Workflow Internals](docs/architecture/skill-creation-workflow.md) - Technical breakdown of the 6-step generation process.

---

## 📂 Project Structure

```text
.
├── src/agentic_fleet/
│   ├── agentic_skills_system/  # Core Python logic
│   │   ├── cli/                # CLI implementation
│   │   ├── skills/             # Skills storage & taxonomy
│   │   ├── taxonomy/           # Taxonomy management
│   │   ├── workflow/           # DSPy skill generation workflows
│   │   └── validators/         # Skill validation logic
│   ├── llm/                    # LLM configuration and clients
│   └── tui/                    # TypeScript/React TUI
├── tests/                      # Pytest suite
├── plans/                      # Architecture and roadmap docs
├── pyproject.toml              # Python metadata & entry points
└── package.json                # Node.js metadata & scripts
```

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | API key for Gemini 3 models (primary) | Yes |
| `DEEPINFRA_API_KEY` | API key for DeepInfra (optional) | No |
| `LITELLM_API_KEY`   | API key for LiteLLM proxy | No |
| `LANGFUSE_SECRET_KEY`| Telemetry via Langfuse | No |
| `REDIS_HOST`        | Redis host for state management | No |
| `DSPY_CACHEDIR`     | Custom directory for DSPy disk cache | No |
| `DSPY_TEMPERATURE`  | Global temperature override for all tasks | No |

*Note: See `.env` for a comprehensive list of supported integrations.*

---

## 📝 TODOs
- [ ] Add LICENSE file.
- [ ] Complete documentation for `MCP_CAPABILITIES` level.
- [ ] Add CI/CD configuration.

## 📄 License

TODO: Add license information.
