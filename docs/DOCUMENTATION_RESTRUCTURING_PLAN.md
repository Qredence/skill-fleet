# Documentation Restructuring Plan

**Date**: 2026-01-27
**Status**: Proposed
**Objective**: Simplify and reorganize the documentation for better navigation, reduced redundancy, and improved clarity.

---

## Current Problems Identified

### 1. API Documentation Confusion

- **Conflicting version info**: `api/index.md` shows only v1 as current, but `api/MIGRATION_V1_TO_V2.md` says v2 is production and v1 is experimental
- **Overlapping files**: `api-reference.md`, `V2_ENDPOINTS.md`, `V2_SCHEMAS.md`, `endpoints.md`, `schemas.md` likely contain duplicate information
- **Unclear versioning**: Users may not know which API version to use

### 2. Excessive Top-Level Categories (10 current)

- 🚀 Getting Started
- 🏗️ Architecture
- 📡 API
- 💻 CLI
- ⚙️ LLM Configuration
- 🤝 HITL
- 📚 Concept Guides
- 🛠️ Development
- 📋 Migration & Notes
- (Plus workflows/, intro/, archive/)

### 3. Redundant or Overlapping Content

- **Workflow docs**: 7 files in `workflows/` (content-generation, conversational, hitl, quality-assurance, signature-tuning, task-analysis) that may overlap with other sections
- **Historical notes**: 29 notes in `archive/historical-notes/` that clutter the docs
- **CLI docs**: Multiple CLI files that may duplicate information

### 4. Complex Main Index

- Long "Quick Links" section
- Extensive "What's New" with detailed architecture changes
- Too many sub-lists making navigation difficult

---

## Proposed Simplified Structure (5 Main Sections)

```
docs/
├── index.md (Main hub - simplified)
│
├── getting-started/ (User-focused quick start)
│   ├── index.md (Installation, quick start, templates)
│   └── user-guide.md (User workflows: creating, managing, promoting skills)
│
├── guides/ (Task-based guides - merged & simplified)
│   ├── api.md (Unified API guide - v2 production, v1 experimental clearly labeled)
│   ├── cli.md (Unified CLI guide)
│   ├── workflows.md (Unified workflow guide - merges all workflow/)
│   ├── hitl.md (HITL system guide)
│   └── dspy.md (DSPy framework guide)
│
├── architecture/ (System architecture for developers)
│   ├── overview.md (High-level architecture)
│   ├── domain-layer.md (DDD patterns, entities)
│   ├── service-layer.md (Service architecture, DI)
│   ├── caching-layer.md (Cache architecture)
│   └── api-architecture.md (API design, versioning)
│
├── development/ (For contributors)
│   ├── setup.md (Development setup)
│   ├── contributing.md (Contribution guidelines)
│   └── extending.md (How to extend the system)
│
└── reference/ (Deep technical reference)
    ├── schemas.md (Data models and schemas)
    ├── agentskills-compliance.md (agentskills.io spec)
    └── migration.md (Format migration guide)
```

---

## Simplification Actions

### Phase 1: API Documentation Unification

**Goal**: Resolve API version confusion and eliminate overlap

**Actions**:

1. Create single `guides/api.md` that:
   - Clearly states v2 is the production API
   - Documents v1 as experimental chat API
   - Merges content from: `api/endpoints.md`, `api/V2_ENDPOINTS.md`
   - Includes schema information inline (no separate file)
   - Provides clear "Quick Start" section for each version

2. Remove/Archive these files:
   - `api/MIGRATION_V1_TO_V2.md` → Move to `reference/` as historical context
   - `api/V2_ENDPOINTS.md` → Consolidate into `guides/api.md`
   - `api/V2_SCHEMAS.md` → Merge schemas into `guides/api.md`
   - `api/api-reference.md` → Consolidate if different content
   - `api/schemas.md` → Merge into reference/schemas.md

3. Keep:
   - `api/index.md` → Simplified landing page that points to `guides/api.md`
   - `api/jobs.md` → Keep if distinct content
   - `api/middleware.md` → Merge into architecture/api-architecture.md

---

### Phase 2: Workflow Documentation Consolidation

**Goal**: Merge 7 workflow files into 1 cohesive guide

**Actions**:

1. Create `guides/workflows.md` that consolidates:
   - Phase 1: Task Analysis
   - Phase 2: Content Generation
   - Phase 3: Quality Assurance
   - HITL Workflow
   - Conversational Workflows
   - Signature Tuning (if needed for users)

2. Archive technical details:
   - Move orchestrator implementation details to `reference/workflows-reference.md`
   - Or create `development/workflows-implementation.md` for contributors

3. Remove:
   - `workflows/content-generation.md`
   - `workflows/conversational.md`
   - `workflows/hitl.md`
   - `workflows/quality-assurance.md`
   - `workflows/signature-tuning.md`
   - `workflows/task-analysis.md`

4. Keep:
   - `workflows/index.md` → Rename to `guides/workflows.md`

---

### Phase 3: CLI Documentation Simplification

**Goal**: Reduce CLI files from 7 to 2

**Actions**:

1. Create `guides/cli.md` that includes:
   - Quick start commands
   - Common workflows
   - Command reference (condensed)

2. Move technical details:
   - `cli/architecture.md` → `development/cli-architecture.md`
   - `cli/architecture.md` already exists - check if needed
   - `cli/tui-architecture.md` → Keep if TUI is active, else archive
   - `cli/dev-command.md` → Merge into `guides/cli.md` or `development/setup.md`
   - `cli/CLI_SYNC_COMMANDS.md` → Merge into `guides/cli.md`
   - `cli/cli-reference.md` → Merge into `guides/cli.md`
   - `cli/commands.md` → Merge into `guides/cli.md`
   - `cli/interactive-chat.md` → Merge into `guides/workflows.md` or `guides/cli.md`

3. Keep:
   - `cli/index.md` → Simplified landing page

---

### Phase 4: Main Index Simplification

**Goal**: Create a clean, user-friendly hub

**Actions**:

1. Simplify `docs/index.md`:
   - Remove extensive "Quick Links" section
   - Consolidate "What's New" into a brief section
   - Use 2-column layout or tabs for different user types
   - Focus on "What do you want to do?" navigation

2. New structure for `index.md`:

```markdown
# Skills Fleet Documentation

**Version**: Post-FastAPI-Centric Restructure | **Last Updated**: 2026-01-27

## Quick Start

[🚀 Getting Started](getting-started/) | [📡 API Guide](guides/api.md) | [💻 CLI Guide](guides/cli.md)

## Navigate by Role

### For Users

Creating and managing skills? Start here:

- [Getting Started Guide](getting-started/)
- [User Guide - Creating Skills](getting-started/user-guide.md)
- [API Guide](guides/api.md)
- [CLI Guide](guides/cli.md)

### For Developers

Building integrations or contributing to the code?

- [Development Setup](development/)
- [Architecture Overview](architecture/)
- [API Guide](guides/api.md)
- [Contributing Guide](development/contributing.md)

### For AI Agents

Working with the system programmatically?

- [AGENTS.md](../AGENTS.md) - Complete working guide
- [Architecture Overview](architecture/)
- [Workflows Guide](guides/workflows.md)

## Topic Index

- [Workflows & HITL](guides/workflows.md) - Skill creation workflow
- [HITL System](guides/hitl.md) - Human-in-the-loop
- [DSPy Framework](guides/dspy.md) - DSPy 3.1.2+ integration
- [LLM Configuration](reference/llm-config.md) - LLM setup (MOVED from docs/llm/)
- [Data Schemas](reference/schemas.md) - Request/response models
- [agentskills.io Compliance](reference/agentskills-compliance.md)

---

## What's New

**FastAPI-Centric Restructure Complete** (January 2026):

- ✅ Domain layer with DDD patterns
- ✅ Service layer with dependency injection
- ✅ Caching layer architecture in place
- ✅ Conversational interface (v1 chat API - experimental)
- ✅ API v2 is now the production API for skill operations

[See full changelog](../CHANGELOG.md)
```

---

### Phase 5: Archive Cleanup

**Goal**: Reduce clutter from historical notes

**Actions**:

1. Keep only the most relevant historical notes in main docs:
   - `archive/historical-notes/DOCUMENTATION_RESTRUCTURING.md` - Document this restructure!
   - Keep summary files like `JOB_PERSISTENCE_IMPLEMENTATION_SUMMARY.md`

2. Consider moving `archive/` entirely outside `docs/`:
   - Suggested: Move to `REFACTORING_NOTES/` at repo root
   - Or keep but add a README explaining it's historical

3. Simplify `docs/archive/README.md` to explain it's historical only

---

### Phase 6: Remove Low-Value Categories

**Actions**:

1. Eliminate or merge these sections:
   - `concepts/` (2 files) - Merge content into reference/ or relevant guides
   - `llm/` (4 files) - Merge into `reference/llm-config.md`
   - `notes/` (4 files) - Evaluate if needed, likely archive
   - `intro/` (1 file) - Merge into getting-started/

2. Result: 5 main sections instead of 10

---

## File-by-File Consolidation Plan

### API Documentation

| Keep/Archive/Merge | File                                                       | Action                   |
| ------------------ | ---------------------------------------------------------- | ------------------------ |
| Keep               | `api/index.md`                                             | Simplify to landing page |
| Merge              | `api/MIGRATION_V1_TO_V2.md` → `reference/api-migration.md` | Historical reference     |
| Merge              | `api/V2_ENDPOINTS.md` → `guides/api.md`                    | Consolidate              |
| Merge              | `api/V2_SCHEMAS.md` → `guides/api.md`                      | Merge schemas inline     |
| Merge              | `api/endpoints.md` → `guides/api.md`                       | Consolidate              |
| Merge              | `api/schemas.md` → `reference/schemas.md`                  | Move to reference        |
| Merge              | `api/middleware.md` → `architecture/api-architecture.md`   | Merge                    |
| Keep               | `api/jobs.md`                                              | Keep if distinct         |

### Workflow Documentation

| Keep/Archive/Merge | File                                         | Action      |
| ------------------ | -------------------------------------------- | ----------- |
| Keep               | `workflows/index.md` → `guides/workflows.md` | Main guide  |
| Remove             | `workflows/content-generation.md`            | Consolidate |
| Remove             | `workflows/conversational.md`                | Consolidate |
| Remove             | `workflows/hitl.md`                          | Consolidate |
| Remove             | `workflows/quality-assurance.md`             | Consolidate |
| Remove             | `workflows/signature-tuning.md`              | Consolidate |
| Remove             | `workflows/task-analysis.md`                 | Consolidate |

### CLI Documentation

| Keep/Archive/Merge | File                                                                 | Action                   |
| ------------------ | -------------------------------------------------------------------- | ------------------------ |
| Keep               | `cli/index.md`                                                       | Simplify to landing page |
| Merge              | `cli/cli-reference.md` → `guides/cli.md`                             | Consolidate              |
| Merge              | `cli/commands.md` → `guides/cli.md`                                  | Consolidate              |
| Merge              | `cli/interactive-chat.md` → `guides/cli.md`                          | Consolidate              |
| Merge              | `cli/CLI_SYNC_COMMANDS.md` → `guides/cli.md`                         | Consolidate              |
| Merge              | `cli/dev-command.md` → `guides/cli.md` or `development/setup.md`     | Consolidate              |
| Archive            | `cli/architecture.md` → `development/cli-architecture.md` or archive | Move to dev              |
| Evaluate           | `cli/tui-architecture.md`                                            | Keep if TUI active       |

### Concepts

| Keep/Archive/Merge | File                                                  | Action      |
| ------------------ | ----------------------------------------------------- | ----------- |
| Merge              | `concepts/concept-guide.md` → `reference/` or archive | Evaluate    |
| Merge              | `concepts/concept-guide.md`                           | Evaluate    |
| Keep               | `concepts/agentskills-compliance.md` → `reference/`   | Important   |
| Merge              | `concepts/developer-reference.md` → `development/`    | Move to dev |

### LLM Configuration

| Keep/Archive/Merge | File                                                                 | Action                  |
| ------------------ | -------------------------------------------------------------------- | ----------------------- |
| Merge              | `llm/index.md` → `reference/llm-config.md`                           | Create single LLM guide |
| Merge              | `llm/providers.md` → `reference/llm-config.md`                       | Merge                   |
| Merge              | `llm/dspy-config.md` → `reference/llm-config.md`                     | Merge                   |
| Merge              | `llm/task-models.md` → `guides/dspy.md` or `reference/llm-config.md` | Merge                   |

### Notes

| Keep/Archive/Merge | File                            | Action                            |
| ------------------ | ------------------------------- | --------------------------------- |
| Evaluate           | `notes/TESTING_REPORT.md`       | Archive if outdated               |
| Evaluate           | `notes/OPTIMIZATION_GUIDE.md`   | Move to `guides/dspy.md`          |
| Evaluate           | `notes/DEPLOYMENT_CHECKLIST.md` | Move to `development/` or archive |
| Merge              | `notes/README.md`               | Archive                           |

### Intro

| Keep/Archive/Merge | File                                                 | Action |
| ------------------ | ---------------------------------------------------- | ------ |
| Merge              | `intro/introduction.md` → `getting-started/index.md` | Merge  |

### Migration

| Keep/Archive/Merge | File                                                              | Action          |
| ------------------ | ----------------------------------------------------------------- | --------------- |
| Merge              | `migration/skill-format-v2-updated.md` → `reference/migration.md` | Keep important  |
| Archive            | `migration/archive/skill-format-v2-draft.md`                      | Historical only |

---

## Implementation Order

1. **Create backup** of current `docs/` directory
2. **Phase 1**: API documentation unification (highest priority)
3. **Phase 2**: Workflow consolidation
4. **Phase 3**: CLI simplification
5. **Phase 4**: Main index rewrite
6. **Phase 5**: Archive cleanup
7. **Phase 6**: Remove low-value categories
8. **Update**: AGENTS.md references
9. **Test**: Navigation and link correctness
10. **Commit**: With descriptive commit message

---

## Success Criteria

✅ Reduced top-level categories from 10 to 5
✅ API version confusion resolved (v2 production, v1 experimental clear)
✅ Workflow files reduced from 7 to 1
✅ Archive cleared of historical notes from main view
✅ Main index is <100 lines (currently ~150)
✅ No broken internal links
✅ Clear navigation by user role (User/Developer/AI Agent)
✅ Documentation file count reduced by ~40%

---

## Notes

- This restructuring should be documented in `archive/historical-notes/` for future reference
- Update any external links or READMEs that reference old paths
- Consider using a static site generator later (MkDocs, Docusaurus) for better navigation
- Get approval from maintainers before implementing
