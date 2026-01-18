# skill-fleet – Agent Working Guide

This guide is for AI agents working on the **skill-fleet** codebase. It covers project structure, key concepts, development workflows, and important gotchas.

---

## 🎯 Project Purpose

The **Agentic Skills System** is a hierarchical, dynamic capability framework that enables AI agents to load skills on-demand. It addresses context bloat by organizing knowledge into a taxonomy where agents mount only the specific skills they need for a given task.

---

## ✅ Current State (2026-01-16)

**Latest**: Taxonomy v0.2 migration completed - simplified 2-level taxonomy with canonical path resolution and alias support.

- **API-first execution**: FastAPI is the canonical surface for running DSPy workflows; the CLI (`skill-fleet create/chat/...`) is a thin API client.
- **Draft-first persistence**: jobs write drafts under `skills/_drafts/<job_id>/...`; promotion into the taxonomy is explicit via:
  - `uv run skill-fleet promote <job_id>`, or
  - `POST /api/v2/drafts/{job_id}/promote`
- **Job persistence caveat**: by default, job state is stored in-memory; a server restart may cause `GET /api/v2/hitl/{job_id}/prompt` to return 404.
- **Known runtime warnings (observed locally)**:
  - Pydantic serializer warnings for streaming/chat payloads (shape mismatches can indicate version drift between producer/consumer models).
- **CLI UX footguns (observed locally)**:
  - Rich `MarkupError` can occur if an exception message includes markup-like tags (e.g. `[/Input Credentials/]`); workaround: `--force-plain-text` or `SKILL_FLEET_FORCE_PLAIN_TEXT=1`.
  - “Action/choice” prompts are only available when the API returns structured `options`; otherwise questions fall back to free-text.
- **Skill quality**: validation can pass “with warnings” (e.g., insufficient examples, plan mismatches). Always review drafts before promotion.
- **Calibrated Evaluation**: Automated quality assessment is now integrated into the workflow, using metrics calibrated against golden skills from Obra/superpowers (scores > 0.8 are target).
- **Where to look**: `docs/api/endpoints.md`, `docs/cli/interactive-chat.md`, `docs/dspy/evaluation.md`, `plans/2026-01-15-skill-creation-hardening.md`.

---

## 🏗️ Architecture Overview

### Core Components

1. **Skills Taxonomy** (`skills/`)
   - Simplified 2-level taxonomy (category/skill) organizing agent capabilities
   - 9 categories: `python`, `devops`, `testing`, `web`, `architecture`, `api`, `practices`, `domain`, `memory`
   - Canonical path resolution with backward-compatible alias support
   - `taxonomy_index.json` defines canonical paths and legacy aliases
   - Each skill is a directory containing a `SKILL.md` file with YAML frontmatter

2. **Unified Core Architecture** (`src/skill_fleet/core/`)
   - **DSPy Integration** (`dspy/`): Complete DSPy framework integration
     - `modules/`: Phase 1 (Understanding), Phase 2 (Generation), Phase 3 (Validation)
     - `signatures/`: DSPy signatures for each phase
     - `programs/`: SkillCreationProgram, SkillRevisionProgram, QuickSkillProgram
     - `evaluation.py`: Integration with DSPy Evaluate and quality metrics
     - `skill_creator.py`: Main 3-phase orchestrator
   - **Evaluation & Metrics** (`dspy/metrics/`): Multi-dimensional quality assessment
     - `skill_quality.py`: Calibrated metrics (Obra/superpowers standards)
     - Penalty multipliers for missing critical elements (core principles, Iron Laws)
   - **Optimization** (`optimization/`): DSPy workflow optimization
     - MIPROv2 optimizer for prompt tuning
     - GEPA optimizer for reflective prompt evolution
   - **Tracing** (`tracing/`): MLflow integration and configuration
   - **Tools** (`tools/`): Research capabilities (filesystem, web search)
   - **HITL** (`hitl/`): Human-in-the-loop feedback handlers
   - `models.py`: Unified Pydantic models (consolidated from workflow and core)
   - `creator.py`: Main entry point for skill creation

3. **Conversational Agent** (`src/skill_fleet/agent/`)
   - Natural language interface for skill creation
   - Multi-phase conversation orchestration (phase1/, phase2/)
   - TDD checklist enforcement
   - Streaming modules with real-time thinking display

4. **CLI** (`src/skill_fleet/cli/`)
   - Primary interface for skill creation, validation, and migration
   - Built with Typer for a clean, typed command-line interface
   - **Commands** (`commands/`): Modular command files (create, chat, evaluate, promote, etc.)
   - **Interactive CLI** (`interactive_cli.py`): Rich-based chat interface
   - **PromptUI** (`ui/prompts.py`): Abstraction for interactive prompts

5. **API Layer** (`src/skill_fleet/api/`)
   - FastAPI REST API with async background jobs
   - **Routes** (`routes/`): skills, taxonomy, validation, evaluation, drafts, optimization
   - Auto-discovery system for DSPy modules (`discovery.py`)
   - Jobs system for long-running operations (`jobs.py`)
   - Quality-assured program versions with Refine/BestOfN

6. **Frontend UI** (`src/skill_fleet/ui/`)
   - React/TypeScript application
   - Components: chat, artifacts (CatalogTree, SkillDetail, WorkflowDashboard)
   - Hooks and services for CLI bridge integration
   - Theme system and keybinding support

7. **Validators** (`src/skill_fleet/validators/`)
   - Ensures skills meet quality and compliance standards
   - Validates YAML frontmatter, content structure, and agentskills.io compliance

8. **Taxonomy** (`src/skill_fleet/taxonomy/`)
   - **Taxonomy Index** (`taxonomy_index.json`): Canonical paths and alias mappings
   - **Models** (`models.py`): Pydantic models for CategoryNode, SkillEntry, TaxonomyIndex
   - **Manager** (`manager.py`): Path resolution with alias support, validation, and automatic linting

9. **Analytics** (`src/skill_fleet/analytics/`)
   - Usage tracking in JSONL format
   - Analytics engine for pattern analysis

---

## 📋 agentskills.io Compliance

### What It Means

**agentskills.io** is a specification for standardizing agent skills to enable:
- **Discoverability**: Agents can enumerate available skills via XML
- **Interoperability**: Skills can be shared across different agent frameworks
- **Metadata**: Standardized frontmatter enables automated indexing and searching

### Required Format

Every `SKILL.md` file MUST include YAML frontmatter:

```yaml
---
name: skill-name-in-kebab-case
description: A concise description of what this skill provides (1-2 sentences)
---
```

### Key Requirements

1. **`name`**: Must be in kebab-case (lowercase with hyphens)
2. **`description`**: Brief, clear explanation of the skill's purpose
3. **Frontmatter**: Must be at the very top of the file (no content before `---`)

### Example

```markdown
---
name: python-async-programming
description: Comprehensive guide to Python's asyncio framework, including coroutines, event loops, and concurrent programming patterns.
---

# Python Async Programming

[Skill content follows...]
```

---

## 📏 Calibrated Evaluation

### Quality Standards
The system uses multi-dimensional metrics calibrated against **Obra/superpowers** and **Anthropics** standards.

1. **Structure Completeness**: Frontmatter, Overview, "When to Use", Quick Reference.
2. **Pattern Quality**: Mandatory inclusion of Anti-patterns (❌) and Production patterns (✅).
3. **Practical Value**: Common Mistakes, Red Flags, and Real-world Impact sections.
4. **Obra Indicators**: 
   - **Core Principle**: A strong, imperative statement of the skill's essence.
   - **Iron Law**: Mandatory rules (e.g., "NO X WITHOUT Y").
   - **Contrast**: Explicit Good/Bad or ❌/✅ paired examples.

### Scoring & Penalties
- **Target Score**: > 0.8 is considered high quality.
- **Penalty Multipliers**: Scores are penalized (e.g., 0.7x multiplier) if critical elements like "Core Principle" or "Good/Bad Contrast" are missing.
- **Calibration**: Metrics are regularly tuned against "golden skills" in `config/training/gold_skills.json`.

---

## 🛠️ Development Workflow

### Setting Up

```bash
# From repo root

# Install Python dependencies (including dev tools)
uv sync --group dev

# Install TUI dependencies (optional)
bun install

# Configure environment
cp .env.example .env
# then edit .env (at minimum: GOOGLE_API_KEY)
```

### Creating a New Skill

```bash
# Start the API server (required for API-backed commands like create/chat/list)
uv run skill-fleet serve
# Dev mode with auto-reload
uv run skill-fleet serve --reload

# Conversational mode (RECOMMENDED - natural language interface)
uv run skill-fleet chat

# Create a skill with direct task (HITL by default)
uv run skill-fleet create "Create a skill for Docker best practices"

# Auto-approve mode (skips interactive prompts)
uv run skill-fleet create "Create a skill for Docker best practices" --auto-approve

# Interactive chat mode with streaming
uv run skill-fleet chat "Create a skill for Docker best practices"
uv run skill-fleet chat --auto-approve
```

**Three-Phase Skill Creation Workflow:**

The skill creation process uses a DSPy-powered 3-phase workflow:

**Phase 1: Understanding & Planning**
1. **Deep Understanding**: Ask WHY questions to understand user's problem and goals
2. **Research**: Perform web and filesystem research when needed
3. **Intent Analysis**: Parse task description and identify skill type
4. **Taxonomy Path**: Find optimal placement in skills hierarchy
5. **Dependency Analysis**: Identify related skills and prerequisites

**Phase 2: Content Generation**
6. **Initialize**: Create skill skeleton and directory structure
7. **Gather Examples**: Collect usage examples from user (optional)
8. **Edit**: Generate skill content (SKILL.md, metadata, supporting files)
9. **Preview**: Present draft for review

**Phase 3: Validation & Refinement**
10. **Validate**: Run compliance checks and quality validation
11. **TDD Checklist**: MANDATORY 3-phase verification:
    - **RED**: Baseline tests without skill (identify rationalizations)
    - **GREEN**: Tests with skill (verify compliance)
    - **REFACTOR**: Close loopholes with explicit counters
12. **Iterate**: Refine based on feedback (if needed)
13. **Save**: Persist to taxonomy

**Conversational Agent Flow:**
The `chat` command uses a natural language interface that:
- Asks clarifying questions one at a time
- Performs research when context is needed
- Presents structured confirmation before creation
- Enforces TDD checklist before saving
- Handles multi-skill requests (creates one at a time)

### Creating a Revised Skill

```bash
# Create a revised version with specific feedback
# (Implemented via the API-backed workflow; use chat to iterate with HITL)
uv run skill-fleet chat
```

Use chat/HITL prompts to provide specific guidance for improving an existing skill.

### DSPy Configuration

The system uses centralized DSPy configuration for consistent LLM settings across all operations:

```python
from skill_fleet.llm.dspy_config import configure_dspy, get_task_lm

# Configure once at startup (the API server does this automatically)
lm = configure_dspy(default_task="skill_understand")

# Get task-specific LM when needed
edit_lm = get_task_lm("skill_edit")
```

**Environment Variables:**
- `DSPY_CACHEDIR`: Override DSPy cache directory (default: `.dspy_cache`)
- `DSPY_TEMPERATURE`: Global temperature override for all tasks

**Task-Specific LMs:**
Different workflow phases use different LM configurations:
- `skill_understand`: Task analysis (high temperature for creativity)
- `skill_plan`: Structure planning (medium temperature)
- `skill_initialize`: Directory initialization (minimal temperature)
- `skill_edit`: Content generation (medium temperature)
- `skill_package`: Validation and packaging (low temperature)
- `skill_validate`: Compliance checking (minimal temperature)
- `skill_evaluate`: Quality assessment (minimal temperature)
- `conversational_agent`: Conversational interface (uses skill_understand as default)

### Workflow Optimization

DSPy programs can be optimized for better quality and consistency:

**MIPROv2 Optimization:**
- Automatically tunes prompts using training data
- Adjusts few-shot examples for each module
- Best for: Improving average quality across many examples

**GEPA Optimization:**
- Reflective prompt evolution with critique cycle
- Uses stronger reasoning model for reflection
- Best for: Complex tasks requiring deep reasoning

**Optimization CLI:**
```bash
# Optimize workflow with MIPROv2
uv run skill-fleet optimize --optimizer miprov2 --model gemini-3-flash-preview

# Optimize with GEPA (uses reflection model)
uv run skill-fleet optimize --optimizer gepa --model gemini-3-flash-preview

# Evaluate only (no optimization)
uv run skill-fleet optimize --evaluate-only --n-examples 10

# Enable MLflow tracking
uv run skill-fleet optimize --optimizer miprov2 --track
```

**Quality Assurance:**
Programs can run in "quality-assured" mode:
- Uses Refine wrapper for iterative improvement
- Uses BestOfN for generating multiple candidates
- Slower but higher quality outputs

```python
from skill_fleet.core.dspy import SkillCreationProgram

# Standard program
program = SkillCreationProgram()

# Quality-assured program
program_qa = SkillCreationProgram(quality_assured=True)
```

**MLflow Tracing:**
Optional MLflow integration for tracking experiments:
```python
from skill_fleet.core.tracing import configure_tracing

# Enable tracing (requires mlflow>=2.21.1)
configure_tracing(
    tracking_uri="mlflow-server",
    experiment_name="skill-creation"
)
```

### Validating Skills

```bash
# Validate a specific skill directory
uv run skill-fleet validate skills/general/testing

# Migrate all skills to agentskills.io format
uv run skill-fleet migrate

# Preview migration without writing changes
uv run skill-fleet migrate --dry-run
```

### Generating XML for Agents

```bash
# Print XML to console
uv run skill-fleet generate-xml

# Save to file for agent prompt injection
uv run skill-fleet generate-xml -o available_skills.xml
```

The generated XML follows the agentskills.io format:
```xml
<available_skills>
  <skill>
    <name>python-async-programming</name>
    <description>Comprehensive guide to Python's asyncio framework...</description>
  </skill>
  <!-- More skills... -->
</available_skills>
```

### Testing

```bash
# Run full test suite
uv run pytest

# Run specific test file
uv run pytest tests/test_validators.py

# Run with coverage
uv run pytest --cov=src/skill_fleet

# Linting and formatting
uv run ruff check .
uv run ruff format .

# Skills are automatically linted during creation
# You can also manually lint individual skills:
uv run ruff check skills/python/async
```

### Analytics

The system includes usage tracking and analytics for understanding skill usage patterns:

```bash
# View usage analytics
uv run skill-fleet analytics

# View analytics for specific user
uv run skill-fleet analytics --user-id user@example.com
```

**Analytics Features:**
- **Usage Tracking**: JSONL log of all skill usage events
- **Success Rates**: Track skill success/failure patterns
- **Skill Combinations**: Identify commonly co-used skills
- **Cold Skills**: Detect unused or rarely-used skills
- **Most Used Skills**: Rank skills by usage frequency

**Analytics Data Location:**
- Log file: `analytics/usage_log.jsonl`
- Analytics root: Configurable via environment variable

---

## 📂 Key Files & Directories

### Python Source

```
src/skill_fleet/
├── agent/
│   ├── agent.py                 # Conversational agent (1850+ lines)
│   ├── modules.py               # Agent conversation modules
│   ├── phase1/                  # Phase 1: Understanding & Planning
│   │   ├── signatures.py
│   │   └── understand.py
│   ├── phase2/                  # Phase 2: Scoping
│   │   ├── signatures.py
│   │   └── scope.py
│   └── signatures.py            # Agent-level signatures
├── analytics/
│   └── engine.py                # Usage tracking and analytics engine
├── api/
│   ├── app.py                   # FastAPI application
│   ├── discovery.py             # Auto-discovery of DSPy modules as endpoints
│   ├── jobs.py                  # Background job handling
│   ├── routes/                  # API route handlers
│   │   ├── hitl.py              # HITL feedback endpoints
│   │   ├── skills.py            # Skill creation endpoints
│   │   ├── taxonomy.py          # Taxonomy management endpoints
│   │   ├── validation.py        # Validation endpoints
│   │   ├── evaluation.py        # Quality evaluation endpoints
│   │   ├── drafts.py            # Draft promotion and lifecycle
│   │   ├── optimization.py      # Workflow optimization endpoints
│   │   └── jobs.py              # Job management endpoints
│   └── schemas/                 # Pydantic request/response models
├── cli/
│   ├── app.py                   # Main Typer application
│   ├── interactive_cli.py       # Rich-based conversational interface
│   ├── onboarding_cli.py        # Onboarding workflow CLI
│   ├── client.py                # API client for CLI commands
│   ├── commands/                # Modular command files (12 files, 13 commands)
│   │   ├── analytics.py         # Usage analytics command
│   │   ├── chat.py              # Conversational agent command
│   │   ├── create.py            # Skill creation command
│   │   ├── evaluate.py          # Skill evaluation (single and batch)
│   │   ├── generate_xml.py      # XML generation command
│   │   ├── list_skills.py       # Skills listing command
│   │   ├── migrate.py           # Format migration command
│   │   ├── onboard.py           # User onboarding command
│   │   ├── optimize.py          # DSPy optimization command
│   │   ├── promote.py           # Draft promotion command
│   │   ├── serve.py             # API server command
│   │   └── validate.py          # Skill validation command
│   ├── hitl/
│   │   └── runner.py            # Centralized HITL runner for CLI
│   ├── ui/
│   │   └── prompts.py           # PromptUI abstraction (PromptToolkitUI + RichFallbackUI)
│   └── utils/
│       ├── constants.py         # CLI constants
│       └── security.py          # Security utilities
├── common/
│   ├── streaming.py             # Streaming module utilities
│   └── utils.py                 # Shared utility functions
├── core/
│   ├── __init__.py              # Unified core exports (consolidated workflow+core)
│   ├── models.py                # Unified Pydantic models
│   ├── creator.py               # Main skill creation entry point
│   ├── dspy/                    # DSPy integration
│   │   ├── modules/             # DSPy modules by phase
│   │   │   ├── phase1_understanding.py
│   │   │   ├── phase2_generation.py
│   │   │   ├── phase3_validation.py
│   │   │   ├── base.py          # Base modules
│   │   │   └── hitl.py          # HITL modules
│   │   ├── signatures/          # DSPy signatures by phase
│   │   │   ├── phase1_understanding.py
│   │   │   ├── phase2_generation.py
│   │   │   ├── phase3_validation.py
│   │   │   ├── base.py
│   │   │   ├── chat.py          # Chat signatures
│   │   │   └── hitl.py          # HITL signatures
│   │   ├── metrics/             # Quality metrics
│   │   │   └── skill_quality.py # Calibrated assessment logic
│   │   ├── training/            # Training data and gold standards
│   │   │   └── gold_standards.py
│   │   ├── programs.py          # SkillCreationProgram, SkillRevisionProgram
│   │   ├── evaluation.py        # SkillEvaluator (DSPy Evaluate wrapper)
│   │   ├── conversational.py    # Conversational DSPy modules
│   │   └── skill_creator.py     # 3-phase orchestrator
│   ├── optimization/            # DSPy optimization
│   │   ├── optimizer.py         # MIPROv2 and GEPA optimizers
│   │   ├── cache.py             # Optimization cache
│   │   ├── evaluation.py        # Evaluation metrics
│   │   └── rewards/             # Reward functions
│   │       ├── phase1_rewards.py
│   │       ├── phase2_rewards.py
│   │       └── step_rewards.py
│   ├── tracing/                 # MLflow tracing
│   │   ├── tracer.py            # Tracing utilities
│   │   ├── mlflow.py            # MLflow integration
│   │   └── config.py            # Tracing configuration
│   ├── tools/                   # Research tools
│   │   └── research.py          # Filesystem and web search
│   └── hitl/                    # Human-in-the-loop
│       └── handlers.py          # Feedback handlers (auto, cli, webhook)
├── llm/
│   ├── dspy_config.py           # Centralized DSPy configuration
│   └── fleet_config.py          # LLM provider configuration
├── onboarding/
│   └── bootstrap.py             # User onboarding bootstrap logic
├── taxonomy/
│   └── manager.py               # Taxonomy management
├── ui/                          # React/TypeScript frontend
│   ├── main.tsx                 # Application entry point
│   ├── src/
│   │   ├── components/
│   │   │   ├── artifacts/       # Artifact display components
│   │   │   ├── chat/            # Chat interface components
│   │   │   └── layout/          # Layout components
│   │   ├── hooks/               # React hooks
│   │   ├── services/            # API and CLI bridge services
│   │   ├── tools/               # UI tools (permissions, prompts)
│   │   └── types.ts             # TypeScript type definitions
│   ├── tsconfig.json            # TypeScript configuration
│   └── package.json             # NPM dependencies
├── validators/
│   └── skill_validator.py       # Core validation logic
└── workflow/                    # DEPRECATED: Consolidated into core/
    ├── creator.py               # Legacy workflow orchestrator
    ├── modules.py               # Legacy DSPy modules
    ├── programs.py              # Legacy DSPy programs
    └── signatures.py            # Legacy DSPy signatures
```

### Documentation

```
docs/
├── overview.md                     # System architecture
├── skill-creator-guide.md          # Detailed skill creation guide
├── agentskills-compliance.md       # agentskills.io specification guide
├── cli-reference.md                # Complete CLI reference
├── api-reference.md                # Python API documentation
├── development/
│   ├── CONTRIBUTING.md             # Contributing guidelines
│   └── ARCHITECTURE_DECISIONS.md   # Architecture decision records
└── architecture/
    └── skill-creation-workflow.md
```

### Configuration

- **`pyproject.toml`**: Python package metadata, dependencies, entry points
- **`.env`**: Environment variables (API keys, configuration)
- **`config/config.yaml`**: LLM configuration (model selection, parameters)
- **`src/skill_fleet/config/`**: Packaged defaults for wheels (kept in sync with `config/`)
  - Sync helper: `uv run python scripts/sync_packaged_resources.py`

### Frontend UI

The system includes a React/TypeScript frontend application for visual skill management:

```bash
# Navigate to UI directory
cd src/skill_fleet/ui

# Install UI dependencies
bun install

# Start development server
bun run dev

# Build for production
bun run build
```

**UI Features:**
- **Chat Interface**: Real-time conversational skill creation with message list and input area
- **Artifact Display**: View skill catalog, skill details, and workflow dashboard
- **CLI Bridge**: Direct integration with backend CLI for command execution
- **Theme System**: Dark, light, and Dracula themes
- **Keybindings**: Customizable keyboard shortcuts
- **Tools Integration**: File system access and command execution permissions

**UI Components:**
- `Chat`: MessageList, InputArea, SuggestionList
- `Artifacts`: CatalogTree, SkillDetail, WorkflowDashboard
- `Layout`: AppShell with resizable panes
- `Hooks`: useUI for state management
- `Services`: API bridge and filesystem services

---

## ⚠️ Common Footguns & Best Practices

### 1. YAML Frontmatter

**PROBLEM**: Frontmatter not at the top of the file
```markdown
# My Skill

---
name: my-skill
---

[Content...]
```

**SOLUTION**: Frontmatter MUST be the first thing in the file
```markdown
---
name: my-skill
description: Description here
---

# My Skill

[Content...]
```

### 2. Skill Name Format

**PROBLEM**: Incorrect name format
```yaml
name: My Skill        # ❌ Contains spaces
name: my_skill        # ❌ Uses underscores
name: MySkill         # ❌ CamelCase
```

**SOLUTION**: Use kebab-case
```yaml
name: my-skill        # ✅ Correct format
```

### 3. Missing Description

**PROBLEM**: No description in frontmatter
```yaml
---
name: my-skill
---
```

**SOLUTION**: Always include a description
```yaml
---
name: my-skill
description: This skill teaches developers how to use Docker effectively.
---
```

### 4. Migration Workflow

**ALWAYS** run with `--dry-run` first to preview changes:
```bash
# Step 1: Preview
uv run skill-fleet migrate --dry-run

# Step 2: Review output carefully

# Step 3: Apply changes
uv run skill-fleet migrate
```

### 5. Validation Before Committing

**ALWAYS** validate skills before creating a commit:
```bash
# Validate a specific skill
uv run skill-fleet validate path/to/skill

# Generate XML to ensure all skills are discoverable
uv run skill-fleet generate-xml
```

If validation fails, fix issues before committing.

### 6. Testing After Changes

**ALWAYS** run tests after modifying core code:
```bash
uv run pytest

# If tests fail, fix them before committing
```

---

## 🔧 Toolchain

### Required

- **Python**: 3.12+ (managed via `uv`)
- **uv**: Fast Python package manager
- **zsh**: Default shell

### Optional

- **bun**: For TUI development
- **zig**: Required for building OpenTUI components

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_key_here

# Optional (CLI)
SKILL_FLEET_API_URL=http://localhost:8000
SKILL_FLEET_USER_ID=default

# Optional (API)
SKILL_FLEET_SKILLS_ROOT=skills
SKILL_FLEET_CORS_ORIGINS=http://localhost:3000

# Optional (providers/observability)
DEEPINFRA_API_KEY=your_key_here
LITELLM_API_KEY=your_key_here
LANGFUSE_SECRET_KEY=your_key_here
REDIS_HOST=localhost
DSPY_CACHEDIR=/path/to/cache
DSPY_TEMPERATURE=0.7
```

---

## 📊 Common Development Tasks

### Adding a New CLI Command

1. Create command file in `src/skill_fleet/cli/`
2. Define command using Typer
3. Register in `src/skill_fleet/cli/app.py`
4. Add tests in `tests/cli/`
5. Update CLI documentation

### Modifying the Skill Creation Workflow

1. API-backed flow (create/chat): update `src/skill_fleet/core/` modules/signatures/programs
2. Template guidance: update `config/templates/SKILL_md_template.md` and/or `config/templates/metadata_template.json`
3. Run the API server, then test with `uv run skill-fleet create "Test task"`
4. Validate output format and quality (and run unit tests)

### Adding a New Evaluation Metric

1. Define metric logic in `src/skill_fleet/core/dspy/metrics/skill_quality.py`
2. Update `SkillQualityScores` dataclass if adding new scoring dimensions
3. Update `compute_overall_score` with appropriate weights and penalty multipliers
4. Add tests in `tests/unit/test_evaluation_metrics.py`
5. (Optional) Update `config/training/quality_criteria.yaml` if externalized

### Adding a New Validator

1. Create validator in `validators/`
2. Register in `skill_validator.py`
3. Add tests in `tests/validators/`
4. Update documentation

### Extending the Taxonomy

1. Add new category in `skills/`
2. Create `README.md` for the category
3. Add example skills
4. Update taxonomy schema if needed

---

## 🚀 Quick Reference

### Essential Commands

```bash
# CLI help
uv run skill-fleet --help

# Start API server (required for API-backed create/chat/list)
uv run skill-fleet serve

# Conversational mode (RECOMMENDED - natural language interface)
uv run skill-fleet chat

# Create a skill (HITL by default)
uv run skill-fleet create "Your task description"

# Evaluate skill quality
uv run skill-fleet evaluate skills/general/testing
uv run skill-fleet evaluate-batch skills/technical_skills/programming/python/*

# Promote a draft to taxonomy
uv run skill-fleet promote <job_id>

# Optimize workflow (DSPy MIPROv2 or GEPA)
uv run skill-fleet optimize --optimizer miprov2
uv run skill-fleet optimize --optimizer gepa --track

# View analytics
uv run skill-fleet analytics

# List skills
uv run skill-fleet list

# Onboard new user
uv run skill-fleet onboard

# Validate skill
uv run skill-fleet validate skills/general/testing

# Migrate to agentskills.io format
uv run skill-fleet migrate --dry-run
uv run skill-fleet migrate

# Generate XML
uv run skill-fleet generate-xml -o skills.xml

# Run tests
uv run pytest

# Lint/format
uv run ruff check .
uv run ruff check --fix .
uv run ruff format .
```

### Useful Paths

- Skills: `skills/`
- CLI: `src/skill_fleet/cli/`
- Core DSPy: `src/skill_fleet/core/dspy/`
- API: `src/skill_fleet/api/`
- UI: `src/skill_fleet/ui/`
- Tests: `tests/`
- Docs: `docs/`
- Config: `config/config.yaml`

---

## 📚 Further Reading

### User Documentation
- [Getting Started](docs/getting-started/index.md) - Quick installation, CLI usage, validation, and templates
- [agentskills.io Compliance Guide](docs/agentskills-compliance.md) - Complete specification
- [Skill Creator Guide](docs/skill-creator-guide.md) - Detailed creation workflow
- [Architecture Overview](docs/overview.md) - System design and concepts
- [CLI Reference](docs/cli-reference.md) - Full command documentation
- [API Reference](docs/api-reference.md) - Python API documentation

### Developer Documentation
- [Contributing Guide](docs/development/CONTRIBUTING.md) - Development setup and workflows
- [Architecture Decisions](docs/development/ARCHITECTURE_DECISIONS.md) - Key architectural decisions and their rationale

---

## 💡 Tips for AI Agents

1. **Always read `SKILL.md` files** to understand skill format before creating new ones
2. **Use migration tools** when updating skill format - don't manually edit all files
3. **Validate early and often** - catch compliance issues before they spread
4. **Follow existing patterns** - check similar skills for structure and style
5. **Test your changes** - run `uv run pytest` and `uv run skill-fleet validate` before considering work complete
6. **Document assumptions** - if you make decisions, explain them in commit messages
7. **Use dry-run mode** - preview changes before applying them to avoid mistakes
8. **Use common utilities** - import from `skill_fleet.common.utils` for safe JSON/float conversion
9. **Understand DSPy configuration** - the API server calls `configure_dspy()`; local workflows should call it (or pass task-specific LMs) before running DSPy programs
10. **Follow templates** - keep new skills aligned with `config/templates/SKILL_md_template.md` and `config/templates/metadata_template.json`

---

## 🐛 Troubleshooting

### "YAML frontmatter not found"
- Ensure frontmatter is at the very top of the file
- Check that you have both opening and closing `---` delimiters

### "Invalid skill name format"
- Use kebab-case only (lowercase with hyphens)
- No spaces, underscores, or capital letters

### "DSPy cache issues"
- Clear cache: `rm -rf ~/.cache/dspy/`
- Or set custom cache dir: `export DSPY_CACHEDIR=/path/to/cache`

### "DSPy not configured"
- CLI automatically configures DSPy on startup
- For library use: call `configure_dspy()` before any DSPy operations
- Check `config/config.yaml` for LM settings
- Verify `GOOGLE_API_KEY` is set

### "Tests failing after changes"
- Run `uv run pytest -v` for verbose output
- Check if validators need updating
- Verify skill format compliance

---

**Last Updated**: 2026-01-16
**Maintainer**: skill-fleet team
