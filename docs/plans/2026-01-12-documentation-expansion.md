# Skills Fleet Documentation Expansion Design

**Date**: 2026-01-12
**Status**: Approved
**Audience**: Both end users/operators and contributors/developers

## Overview

This document outlines the comprehensive expansion of the skills-fleet documentation to provide extensive conceptual and technical coverage of the entire system. The documentation targets both users (operators) and developers, using a hierarchical structure with overview pages linking to detailed content.

## Goals

1. Provide comprehensive documentation for DSPy usage (signatures, modules, programs, optimization)
2. Document the FastAPI REST API (endpoints, schemas, middleware, jobs)
3. Document the CLI including interactive chat mode
4. Document LLM configuration (providers, task-specific models)
5. Document the HITL (Human-in-the-Loop) system
6. Ensure all relevant aspects of `src/skill_fleet/` are covered

## Documentation Structure

```
docs/
├── intro/
│   ├── introduction.md          (expand existing)
│   └── quick-start.md           (new)
│
├── getting-started/
│   ├── index.md                 (expand existing)
│   ├── installation.md          (new)
│   └── first-skill.md           (new)
│
├── concepts/
│   ├── concept-guide.md         (expand existing)
│   ├── taxonomy-system.md       (new)
│   └── agentskills-io.md        (new)
│
├── dspy/
│   ├── index.md                 (new - DSPy overview & architecture)
│   ├── signatures.md            (new - all signatures)
│   ├── modules.md               (new - all modules)
│   ├── programs.md              (new - all programs)
│   └── optimization.md          (new - MIPROv2, GEPA, caching)
│
├── api/
│   ├── index.md                 (new - API overview)
│   ├── endpoints.md             (new - all REST endpoints)
│   ├── schemas.md               (new - all Pydantic schemas)
│   ├── middleware.md            (new - CORS, error handling)
│   └── jobs.md                  (new - background jobs)
│
├── cli/
│   ├── index.md                 (new - CLI overview)
│   ├── commands.md              (new - all commands)
│   ├── interactive-chat.md      (new - chat mode)
│   └── architecture.md          (new - CLI app structure)
│
├── llm/
│   ├── index.md                 (new - LLM config overview)
│   ├── providers.md             (new - all providers)
│   ├── dspy-config.md           (new - centralized config)
│   └── task-models.md           (new - task-specific models)
│
├── hitl/
│   ├── index.md                 (new - HITL overview)
│   ├── callbacks.md             (new - callback interface)
│   ├── interactions.md          (new - interaction types)
│   └── runner.md                (new - HITL runner)
│
├── development/
│   ├── CONTRIBUTING.md          (existing)
│   ├── ARCHITECTURE_DECISIONS.md (existing)
│   ├── testing.md               (new)
│   └── extending.md             (new)
│
├── reference/
│   ├── api-reference.md         (expand existing)
│   ├── cli-reference.md         (expand existing)
│   └── python-api.md            (new)
│
└── architecture/
    ├── skill-creation-workflow.md (existing)
    ├── system-architecture.md   (new)
    └── data-flow.md             (new)
```

## Content Specifications

### DSPy Documentation (`docs/dspy/`)

#### index.md - DSPy Overview
- What is DSPy and its role in skills-fleet
- 3-phase workflow architecture
- Integration with HITL
- File locations: `src/skill_fleet/core/`

#### signatures.md - All Signatures
- **Phase 1 Signatures** (`phase1_understanding.py`):
  - `RequirementGatheringSignature`
  - `IntentAnalysisSignature`
  - `TaxonomyPathFindingSignature`
  - `DependencyAnalysisSignature`
  - `PlanSynthesisSignature`
- **Phase 2 Signatures** (`phase2_generation.py`):
  - `ContentGenerationSignature`
  - `CapabilityDocumentationSignature`
  - `UsageExamplesSignature`
- **Phase 3 Signatures** (`phase3_validation.py`):
  - `ValidationSignature`
  - `RefinementSignature`
- **Chat Signatures** (`chat.py`):
  - `ChatRequestSignature`
  - `ChatResponseSignature`
- **HITL Signatures** (`hitl.py`):
  - `ConfirmationSignature`
  - `PreviewSignature`
  - `FeedbackAnalysisSignature`

Each signature documented with:
- Input/output fields
- When used in workflow
- Code examples

#### modules.md - All Modules
- **Phase 1 Orchestrator**: Parallel analysis architecture
- **Phase 2 Generator**: Content generation flow
- **Phase 3 Validator**: Validation and refinement
- **HITL Utilities**: Confirmation, preview, feedback analysis

#### programs.md - All Programs
- `SkillCreationProgram` - Main 3-phase orchestrator
- `ConversationalProgram` - Chat-based skill creation
- Program composition patterns
- HITL integration

#### optimization.md - Workflow Optimization
- MIPROv2 optimizer usage
- GEPA reflection
- Caching strategy
- Performance tuning

### API Documentation (`docs/api/`)

#### index.md - API Overview
- FastAPI application structure
- Auto-discovery system for DSPy modules
- CORS middleware
- Route organization
- API vs CLI decision guide

#### endpoints.md - REST Endpoints
**Skills routes** (`/api/v1/skills/*`):
- `POST /skills` - Create skill (async)
- `GET /skills` - List with filtering
- `GET /skills/{skill_id}` - Get details
- `PUT /skills/{skill_id}` - Update
- `DELETE /skills/{skill_id}` - Delete

**HITL routes** (`/api/v1/hitl/*`):
- `POST /hitl/confirm` - Handle confirmation
- `POST /hitl/preview` - Handle preview
- `POST /hitl/feedback` - Submit feedback

**Taxonomy routes** (`/api/v1/taxonomy/*`):
- `GET /taxonomy` - Get structure
- `GET /taxonomy/xml` - Generate XML

**Validation routes** (`/api/v1/validation/*`):
- `POST /validation/skill` - Validate skill
- `POST /validation/frontmatter` - Validate YAML

#### schemas.md - Pydantic Schemas
- Request models
- Response models
- Workflow models
- Model conversions

#### middleware.md - Middleware & Error Handling
- CORS configuration
- Exception handlers
- Error response format

#### jobs.md - Background Jobs
- Async skill creation
- Job status polling
- Webhook callbacks
- Job queue management

### CLI Documentation (`docs/cli/`)

#### index.md - CLI Overview
- Typer-based architecture
- Command groups
- Global options
- Environment variables

#### commands.md - All Commands
- **create**: Skill creation with all options
- **chat**: Interactive chat mode
- **validate**: Validation command
- **serve**: API server
- **list**: List skills with filtering
- **migrate**: agentskills.io migration
- **optimize**: Workflow optimization
- **analytics**: Usage statistics

#### interactive-chat.md - Chat Mode
- Starting chat sessions
- Chat commands
- Context management
- Streaming responses
- Chat-specific HITL

#### architecture.md - CLI Structure
- `app.py` - Main Typer app
- Command registration
- `client.py` - HTTP client
- HITL runner
- Adding new commands

### LLM Documentation (`docs/llm/`)

#### index.md - LLM Configuration
- Configuration hierarchy
- Provider architecture
- DSPy integration

#### providers.md - All Providers
- **DeepInfra**: API setup, models, config
- **Gemini**: API setup, Gemini 3 models, config
- **ZAI**: API setup, config
- **Vertex AI**: Service account, config
- Provider comparison

#### dspy-config.md - DSPy Configuration
- `configure_dspy()` function
- `get_task_lm()` function
- `DSPY_CACHEDIR` variable
- `DSPY_TEMPERATURE` variable
- Config file format

#### task-models.md - Task-Specific Models
| Task | Purpose | Model | Temperature |
|------|---------|-------|-------------|
| skill_understand | Analysis | High reasoning | 0.7 |
| skill_plan | Planning | Medium reasoning | 0.5 |
| skill_initialize | Setup | Fast model | 0.1 |
| skill_edit | Generation | Creative model | 0.6 |
| skill_package | Validation | Precise model | 0.1 |
| skill_validate | Compliance | Precise model | 0.0 |

### HITL Documentation (`docs/hitl/`)

#### index.md - HITL System
- Why HITL matters
- Interaction types
- Callback design
- Integration points

#### callbacks.md - Callback Interface
- Callback signature
- Custom callbacks
- Async/sync support
- Frontend integration

#### interactions.md - Interaction Types
- **ClarifyingQuestion**: Multi-choice and free-text
- **Confirmation**: Yes/no with details
- **Preview**: Show content for approval
- **Feedback**: Structured feedback
- Interaction flow

#### runner.md - HITL Runner
- `src/skill_fleet/cli/hitl/runner.py`
- Session management
- Response parsing
- Error handling

### Development Documentation (`docs/development/`)

#### testing.md - Testing Guide
- Unit tests with pytest
- Integration tests
- Testing DSPy modules
- Mocking LLM responses
- Coverage requirements

#### extending.md - Extending the System
- Adding new signatures
- Creating custom modules
- Adding workflow phases
- Contributing guidelines

### Reference Documentation (`docs/reference/`)

#### python-api.md - Programmatic Python API
- `TaxonomyManager` deep dive
- `SkillValidator` API
- Workflow orchestrators
- Direct DSPy program usage

## Documentation Standards

Each document must include:

1. **Frontmatter**: Title, description, last updated date
2. **Table of Contents**: Auto-generated for docs > 3 sections
3. **Code blocks**: Language-specific syntax highlighting
4. **Diagrams**: Mermaid for flows, architecture diagrams
5. **Examples**: Real, runnable code snippets
6. **Cross-references**: Links to related documentation
7. **File paths**: Always include full `src/skill_fleet/...` paths
8. **Type hints**: Show function signatures with complete type information

## Implementation Phases

### Phase 1: File Structure
Create all new documentation files with placeholder structure

### Phase 2: Core Documentation (Priority)
- `docs/dspy/` - All files
- `docs/api/` - All files
- `docs/cli/` - All files
- `docs/llm/` - All files

### Phase 3: Supporting Documentation
- `docs/hitl/` - All files
- `docs/development/` - New files
- `docs/reference/` - python-api.md

### Phase 4: Updates & Polish
- Expand existing docs
- Add cross-references
- Generate diagrams
- Final review

## Success Criteria

- [ ] All DSPy signatures, modules, programs documented
- [ ] All API endpoints documented with examples
- [ ] All CLI commands documented with examples
- [ ] All LLM providers documented
- [ ] HITL system fully documented
- [ ] Cross-references between related docs
- [ ] Code examples for all major operations
- [ ] Diagrams for complex flows
- [ ] All file paths reference `src/skill_fleet/` locations

## Related Files

- `src/skill_fleet/core/` - DSPy implementation
- `src/skill_fleet/api/` - FastAPI implementation
- `src/skill_fleet/cli/` - CLI implementation
- `src/skill_fleet/llm/` - LLM configuration
- `src/skill_fleet/workflow/` - Workflow orchestrators
