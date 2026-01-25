# Skills Fleet Documentation

Welcome to the Skills Fleet documentation hub. This index provides quick access to all documentation for the agentic capability platform.

**Last Updated**: 2026-01-25
**Version**: Post-FastAPI-Centric Restructure

## Quick Links

- **[Project README](../README.md)** - High-level overview and quick start
- **[AGENTS.md](../AGENTS.md)** - Comprehensive working guide for AI agents
- **[What's New](#whats-new-post-restructure)** - Latest architecture changes

## What's New (Post-Restructure)

### Latest Architecture Enhancements (January 2025)

1. **Domain Layer (DDD Patterns)** - NEW
   - Domain entities with rich business logic
   - Specification pattern for business rules
   - Repository interfaces for data access abstraction
   - See: [Domain Layer Architecture](architecture/DOMAIN_LAYER.md)

2. **Service Layer** - NEW
   - BaseService with dependency injection
   - MLflow hierarchical run tracking
   - Automatic artifact logging
   - See: [Service Layer Architecture](architecture/SERVICE_LAYER.md)

3. **Caching Layer** - NEW
   - In-memory cache with TTL configuration
   - Pattern-based invalidation
   - Redis migration path documented
   - See: [Caching Layer Architecture](architecture/CACHING_LAYER.md)

4. **Conversational Interface (v1 API)** - NEW
   - Session management with state machine
   - Multi-turn conversations
   - Server-Sent Events (SSE) streaming
   - See: [Conversational Interface](architecture/CONVERSATIONAL_INTERFACE.md)

5. **API Versioning Clarity** - UPDATED
   - v2 API: Main, stable API for skill operations
   - v1 API: Experimental chat streaming endpoints
   - See: [API Migration Guide](api/MIGRATION_V1_TO_V2.md)

## Documentation by Category

### 🚀 Getting Started
For new users setting up and using Skills Fleet

- **[Getting Started Guide](getting-started/index.md)** - Installation, quick start, templates
- **[MLflow Setup Guide](getting-started/MLFLOW_SETUP.md)** - DSPy autologging with hierarchical runs, tag organization, artifact logging
- **[Streaming Quickstart](getting-started/STREAMING_QUICKSTART.md)** - Real-time skill creation
- **[Import Path Guide](development/IMPORT_PATH_GUIDE.md)** - Canonical import paths (NEW)

### 🏗️ Architecture
Understanding how Skills Fleet works

- **[Domain Layer](architecture/DOMAIN_LAYER.md)** - DDD patterns, entities, specifications (NEW)
- **[Service Layer](architecture/SERVICE_LAYER.md)** - Service architecture, dependency injection (NEW)
- **[Caching Layer](architecture/CACHING_LAYER.md)** - Cache architecture, Redis migration (NEW)
- **[Conversational Interface](architecture/CONVERSATIONAL_INTERFACE.md)** - Chat system, session management (NEW)
- **[Workflow Layer](workflows/)** - Orchestrators for DSPy workflows
- **[Restructuring Status](architecture/restructuring-status.md)** - Current restructure progress (UPDATED)
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

- **[API Overview](api/index.md)** - REST API introduction (UPDATED)
- **[API Migration Guide](api/MIGRATION_V1_TO_V2.md)** - Versioning, v1 vs v2 (NEW)
- **[v2 Endpoints](api/V2_ENDPOINTS.md)** - Complete v2 API reference (NEW)
- **[v2 Schemas](api/V2_SCHEMAS.md)** - Request/response models (NEW)
- **[API Endpoints](api/endpoints.md)** - Detailed endpoint reference (v2)
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
- **[Import Path Guide](development/IMPORT_PATH_GUIDE.md)** - Canonical import paths (NEW)
- **[Service Extension Guide](development/SERVICE_EXTENSION_GUIDE.md)** - Extending services (NEW)
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
2. [API Migration Guide](api/MIGRATION_V1_TO_V2.md) - Understand API versioning
3. [Workflow Layer](workflows/) - Learn the orchestrator pattern
4. [CLI Overview](cli/index.md) - Command usage
5. [Create Your First Skill](getting-started/index.md#core-user-workflows) - Hands-on practice

### For Developers
1. [Domain Layer](architecture/DOMAIN_LAYER.md) - DDD patterns and entities
2. [Service Layer](architecture/SERVICE_LAYER.md) - Service architecture
3. [Import Path Guide](development/IMPORT_PATH_GUIDE.md) - Import patterns
4. [DSPy Overview](dspy/index.md) - Core framework
5. [API Overview](api/index.md) - REST API
6. [Service Extension Guide](development/SERVICE_EXTENSION_GUIDE.md) - Extending services
7. [Contributing Guide](development/CONTRIBUTING.md) - Development workflow

### For AI Agents
1. [AGENTS.md](../AGENTS.md) - Complete working guide
2. [Domain Layer](architecture/DOMAIN_LAYER.md) - Domain model understanding
3. [Workflow Layer](workflows/) - Orchestrator usage
4. [DSPy Overview](dspy/index.md) - 3-phase workflow
5. [agentskills.io Compliance](concepts/agentskills-compliance.md) - Skill schema

---

## Documentation Status

| Section | Status | Last Updated |
|---------|--------|--------------|
| Getting Started | ✅ Complete | 2026-01-25 |
| Architecture | ✅ Complete | 2026-01-25 |
| Domain Layer | ✅ Complete | 2026-01-25 |
| Service Layer | ✅ Complete | 2026-01-25 |
| DSPy Framework | ✅ Complete | 2026-01-23 |
| API Documentation (v2) | ✅ Complete | 2026-01-25 |
| API Documentation (v1) | ✅ Complete | 2026-01-25 |
| CLI Documentation | ✅ Complete | 2026-01-14 |
| LLM Configuration | ✅ Complete | 2026-01-15 |
| HITL System | ✅ Complete | 2026-01-12 |
| Concept Guides | ✅ Complete | 2026-01-21 |
| Development | ✅ Complete | 2026-01-25 |

---

**Recent Changes (January 2025):**
- ✅ FastAPI-centric restructure complete
- ✅ Domain layer with DDD patterns documented
- ✅ Service layer with dependency injection documented
- ✅ Caching layer architecture documented
- ✅ Conversational interface (v1 API) documented
- ✅ API versioning guide created (v1 vs v2)
- ✅ MLflow hierarchical runs and artifact logging documented
- ✅ Import path guide created
- ✅ Service extension guide created
