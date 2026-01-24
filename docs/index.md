# Skills Fleet Documentation

Welcome to the Skills Fleet documentation hub. This index provides quick access to all documentation for the agentic capability platform.

## Quick Links

- **[Project README](../README.md)** - High-level overview and quick start
- **[AGENTS.md](../AGENTS.md)** - Comprehensive working guide for AI agents

## Documentation by Category

### 🚀 Getting Started
For new users setting up and using Skills Fleet

- **[Getting Started Guide](getting-started/index.md)** - Installation, quick start, templates
- **[MLflow Setup Guide](getting-started/MLFLOW_SETUP.md)** - DSPy autologging with MLflow
- **[Streaming Quickstart](getting-started/STREAMING_QUICKSTART.md)** - Real-time skill creation

### 🏗️ Architecture
Understanding how Skills Fleet works

- **[Workflow Layer](workflows/)** - New orchestrators for DSPy workflows
- **[Skill Creation Workflow](architecture/skill-creation-workflow.md)** - 3-phase workflow details
- **[Background Jobs](architecture/BACKGROUND_JOBS.md)** - Async job processing
- **[Database Sync](architecture/DATABASE_SYNC.md)** - Data synchronization
- **[Job Persistence](architecture/JOB_PERSISTENCE.md)** - Job state management
- **[Streaming Architecture](architecture/STREAMING_ARCHITECTURE.md)** - Real-time updates

### 🔧 DSPy Framework
Skills Fleet's core workflow engine

- **[DSPy Overview](dspy/index.md)** - DSPy 3.1.2+ integration
- **[DSPy Signatures](dspy/signatures.md)** - Task-based signature organization
- **[DSPy Modules](dspy/modules.md)** - Execution strategies
- **[DSPy Programs](dspy/programs.md)** - High-level orchestrators
- **[DSPy Optimization](dspy/optimization.md)** - MIPROv2, GEPA, auto-selection
- **[Adaptive Metric Weighting](dspy/ADAPTIVE_METRIC_WEIGHTING.md)** - Dynamic metrics

### 📡 API
Programmatic access to Skills Fleet

- **[API Overview](api/index.md)** - REST API introduction
- **[API Endpoints](api/endpoints.md)** - Complete endpoint reference
- **[API Schemas](api/schemas.md)** - Request/response models
- **[API Middleware](api/middleware.md)** - CORS and error handling
- **[Background Jobs](api/jobs.md)** - Job system documentation

### 💻 CLI
Command-line interface for skill creation

- **[CLI Overview](cli/index.md)** - CLI introduction
- **[Command Reference](cli/commands.md)** - All commands detailed
- **[Interactive Chat](cli/interactive-chat.md)** - Chat mode guide
- **[CLI Architecture](cli/architecture.md)** - Internal structure
- **[CLI Sync Commands](cli/CLI_SYNC_COMMANDS.md)** - Synchronous operations
- **[Dev Command](cli/dev-command.md)** - Development utilities

### ⚙️ LLM Configuration
Language model setup and DSPy configuration

- **[LLM Overview](llm/index.md)** - Configuration introduction
- **[Provider Setup](llm/providers.md)** - Setting up LLM providers
- **[DSPy Configuration](llm/dspy-config.md)** - Centralized config system
- **[Task-Specific Models](llm/task-models.md)** - Task model mapping

### 🤝 Human-in-the-Loop (HITL)
Interactive skill creation workflow

- **[HITL Overview](hitl/index.md)** - HITL system introduction
- **[HITL Callbacks](hitl/callbacks.md)** - Callback interface
- **[HITL Interactions](hitl/interactions.md)** - Interaction types
- **[HITL Runner](hitl/runner.md)** - Implementation details

### 📚 Concept Guides
Deep dives into specific concepts

- **[Concept Guide](concepts/concept-guide.md)** - Core concepts overview
- **[agentskills.io Compliance](concepts/agentskills-compliance.md)** - Schema and validation
- **[Developer Reference](concepts/developer-reference.md)** - Development patterns

### 🛠️ Development
Contributing and extending Skills Fleet

- **[Contributing Guide](development/CONTRIBUTING.md)** - Development setup and workflows
- **[Architecture Decisions](development/ARCHITECTURE_DECISIONS.md)** - Design decisions
- **[Restructuring Status](architecture/restructuring-status.md)** - Current restructure progress

### 📋 Migration & Notes
Project evolution and transition notes

- **[Migration Guide](migration/skill-format-v2-updated.md)** - Format migration
- **[Project Notes](notes/)** - Implementation notes and summaries

---

## Recommended Reading Paths

### For New Users
1. [Getting Started Guide](getting-started/index.md) - Set up your environment
2. [Workflow Layer](workflows/) - Learn the orchestrator pattern
3. [CLI Overview](cli/index.md) - Command usage
4. [Create Your First Skill](getting-started/index.md#core-user-workflows) - Hands-on practice

### For Developers
1. [Workflow Layer](workflows/) - New architecture
2. [DSPy Overview](dspy/index.md) - Core framework
3. [API Overview](api/index.md) - REST API
4. [Contributing Guide](development/CONTRIBUTING.md) - Development workflow

### For AI Agents
1. [AGENTS.md](../AGENTS.md) - Complete working guide
2. [Workflow Layer](workflows/) - Orchestrator usage
3. [DSPy Overview](dspy/index.md) - 3-phase workflow
4. [agentskills.io Compliance](concepts/agentskills-compliance.md) - Skill schema

---

## Documentation Status

| Section | Status | Last Updated |
|---------|--------|--------------|
| Getting Started | ✅ Complete | 2026-01-23 |
| Architecture | ✅ Complete | 2026-01-23 |
| DSPy Framework | ✅ Complete | 2026-01-23 |
| API Documentation | ✅ Complete | 2026-01-12 |
| CLI Documentation | ✅ Complete | 2026-01-14 |
| LLM Configuration | ✅ Complete | 2026-01-15 |
| HITL System | ✅ Complete | 2026-01-12 |
| Concept Guides | ✅ Complete | 2026-01-21 |
| Development | ✅ Complete | 2026-01-23 |

---

**Last Updated**: 2026-01-23
**Version**: Current (Post-Restructure)

**Recent Changes:**
- ✅ Phase 1 & 2 restructure complete (task-based signatures + workflows layer)
- ✅ MLflow integration fixed and verified
- ✅ Documentation reorganized for clarity
- ✅ Legacy facade and compat layers removed
