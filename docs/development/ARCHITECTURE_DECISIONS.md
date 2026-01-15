# Architecture Decision Records

This document records significant architectural decisions made during the development of Skills Fleet. Each ADR captures the context, decision, rationale, and consequences.

## ADR-001: Use DSPy for LLM Orchestration

**Date:** 2024
**Status:** Accepted

### Context

We need a framework for building LLM-powered applications with:
- Optimized prompts that can be improved over time
- Consistent patterns for multi-step reasoning
- Quality assurance mechanisms
- Good TypeScript/Python ecosystem support

### Decision

Use [DSPy](https://github.com/stanfordnlp/dspy) as the primary framework for:
- Skill creation workflow orchestration
- Prompt optimization (MIPROv2, GEPA)
- Multi-step reasoning chains
- Quality assurance (Refine, BestOfN)

### Rationale

**Pros:**
- **Declarative approach**: Separates logic from prompts, making both easier to modify
- **Built-in optimization**: MIPROv2 and GEPA for automated prompt improvement
- **Growing community**: Active development and good documentation
- **Python-native**: First-class Python support with type hints
- **Composability**: Easy to combine multiple modules into programs
- **Quality primitives**: Built-in Refine and BestOfN for quality assurance

**Cons:**
- **Learning curve**: Requires understanding of DSPy's abstraction model
- **Training data requirement**: Optimization requires training datasets
- **Young ecosystem**: Fewer examples and patterns compared to more established frameworks

### Consequences

- All LLM interactions go through DSPy modules (`dspy.Module`, `dspy.Signature`)
- Prompt optimization requires training data in `config/training/` directory
- Developers need to learn DSPy's programming model
- Quality assurance uses DSPy's Refine and BestOfN patterns
- Workflow is defined in `SkillCreationProgram` which chains 6 DSPy modules

### Alternatives Considered

1. **LangChain**: More mature but heavier and more complex
2. **Direct API calls**: Simpler but no optimization or quality assurance
3. **Custom framework**: More control but higher development cost

---

## ADR-002: agentskills.io Compliance

**Date:** 2024
**Status:** Accepted

### Context

Skills need a standard format for:
- Metadata and structure
- Dependency management
- Cross-platform compatibility
- Agent system integration

### Decision

Adopt [agentskills.io](https://agentskills.io/) specification for all skills.

### Rationale

**Pros:**
- **Industry standard**: Emerging standard for AI skill packaging
- **Cross-platform**: Skills work across different agent systems
- **Clear structure**: Well-defined metadata and content format
- **Dependency management**: Built-in support for skill dependencies
- **Validation**: Clear rules for compliance checking

**Cons:**
- **Additional complexity**: Requires frontmatter and validation
- **Migration effort**: Existing skills need updates
- **External dependency**: Must track spec changes

### Consequences

- All skills must include `metadata.json` with required fields
- YAML frontmatter required in `SKILL.md`
- Validation enforces compliance before skill registration
- Taxonomy structure follows agentskills.io conventions
- Migration tools provided for updating existing skills

### Implementation

- `SkillValidator` checks compliance
- `TaxonomySkillCreator` generates compliant skills
- Migration tools update legacy skills
- XML generation follows agentskills.io format

---

## ADR-003: Taxonomy-Based Skill Organization

**Date:** 2024
**Status:** Accepted

### Context

Skills need to be organized in a way that:
- Supports semantic discovery
- Enables dependency resolution
- Facilitates skill composition
- Scales to thousands of skills
- Maps to user mental models

### Decision

Use hierarchical taxonomy with 8-type classification matrix.

### Rationale

**Pros:**
- **Semantic discovery**: Users can find skills by domain
- **Dependency resolution**: Clear paths enable dependency management
- **Composition**: Skills can reference each other by taxonomy path
- **Scalability**: Hierarchical structure scales to large numbers
- **Flexibility**: Type classification affects loading strategy

**Cons:**
- **Maintenance overhead**: Taxonomy requires curation
- **Rigid structure**: Skills must fit into predetermined categories
- **Potential for inconsistency**: Requires guidelines to maintain

### Consequences

- Taxonomy paths determine skill location (e.g., `technical_skills/programming/languages/python`)
- Type classification affects loading strategy
- 8 skill types: `cognitive`, `technical`, `domain`, `tool`, `mcp`, `specialization`, `task_focus`, `memory`
- `TaxonomyManager` handles traversal and validation
- Skills reference dependencies via taxonomy paths

### Type System

| Type | Description | Loading Strategy |
|------|-------------|-------------------|
| `cognitive` | Reasoning and decision-making | Always loaded |
| `technical` | Programming and development | Task-specific |
| `domain` | Subject-matter expertise | On-demand |
| `tool` | External tool integration | On-demand |
| `mcp` | MCP server integration | On-demand |
| `specialization` | Specialized capabilities | On-demand |
| `task_focus` | Task-specific operations | Dormant |
| `memory` | Memory management | Always loaded |

---

## ADR-004: Centralized DSPy Configuration

**Date:** 2026-01-10
**Status:** Accepted

### Context

Multiple parts of the codebase need DSPy LM configuration:
- CLI commands
- Workflow programs
- Conversational agent
- Testing utilities

Previously, each component configured DSPy independently, leading to:
- Inconsistent configuration
- Code duplication
- Difficult testing

### Decision

Create centralized `skill_fleet.llm.dspy_config` module with:
- `configure_dspy()` for one-time initialization
- `get_task_lm()` for task-specific LM instances

### Rationale

**Pros:**
- **Single source of truth**: One place for DSPy configuration
- **Consistency**: All components use same configuration
- **Testability**: Easy to mock configuration for tests
- **Environment variables**: Centralized support for overrides

**Cons:**
- **Additional abstraction**: One more layer to understand
- **Initialization order**: Must call `configure_dspy()` before use

### Consequences

- CLI calls `configure_dspy()` at startup
- Library users can call `configure_dspy()` themselves
- Environment variables `DSPY_CACHEDIR` and `DSPY_TEMPERATURE` respected
- Task-specific LMs accessed via `get_task_lm()`
- Configuration priority: environment → config.yaml → defaults

---

## ADR-005: 6-Step Skill Creation Workflow

**Date:** 2024
**Status:** Accepted

### Context

Skill creation is a complex process requiring:
- Task understanding
- Structure planning
- Directory initialization
- Content generation
- Validation
- Iteration based on feedback

### Decision

Implement a 6-step DSPy-powered workflow with quality assurance options:
1. **Understand**: Analyze task requirements
2. **Plan**: Design skill structure
3. **Initialize**: Create directories and metadata
4. **Edit**: Generate content
5. **Package**: Validate and package
6. **Iterate**: Improve based on feedback

### Rationale

**Pros:**
- **Clear separation**: Each step has single responsibility
- **Quality options**: Standard and quality-assured variants
- **Composability**: Steps can be combined or skipped
- **Traceability**: Each step produces artifacts for debugging

**Cons:**
- **Complexity**: More moving parts than simple generation
- **LM costs**: Multiple LM calls per skill
- **Latency**: Sequential steps take time

### Consequences

- `SkillCreationProgram` chains 6 modules
- Each module has standard and QA variants
- QA variants use DSPy's Refine and BestOfN
- Artifacts stored in `cache_dir/` for debugging
- Reward functions ensure quality metrics

### Module Variants

| Step | Standard Module | QA Module | Quality Mechanism |
|------|----------------|-----------|-------------------|
| Understand | `UnderstandModule` | `UnderstandModuleQA` | Reward-based filtering |
| Plan | `PlanModule` | `PlanModuleQA` | Refine with reward |
| Initialize | `InitializeModule` | N/A | Simple file operations |
| Edit | `EditModule` | `EditModuleQA` | Refine with reward |
| Package | `PackageModule` | `PackageModuleQA` | BestOfN selection |
| Iterate | `IterateModule` | N/A | Human-in-the-loop |

---

## ADR-006: Common Utilities Module

**Date:** 2026-01-10
**Status:** Accepted

### Context

Safe type conversion utilities were duplicated across:
- `workflow/modules.py`
- `agent/modules.py`

This led to:
- Code duplication
- Inconsistent behavior
- Maintenance burden

### Decision

Create centralized `skill_fleet.common.utils` module with:
- `safe_json_loads()` for robust JSON parsing
- `safe_float()` for safe float conversion

### Rationale

**Pros:**
- **DRY principle**: Single implementation
- **Consistency**: Same behavior everywhere
- **Testing**: Test utilities once
- **Documentation**: Single source of truth

**Cons:**
- **Import overhead**: Additional import statement
- **Breaking change**: Requires updating import locations

### Consequences

- All modules import from `skill_fleet.common.utils`
- Utilities handle LLM output variations gracefully
- Well-documented with examples
- Comprehensive test coverage

---

## ADR-007: Conversational Agent Design

**Date:** 2024
**Status:** Accepted

### Context

Users need an interactive way to create skills that:
- Guides them through the process
- Validates understanding before generation
- Enforces TDD checklist before saving
- Handles multiple skill creation

### Decision

Implement a conversational agent using state machine pattern with:
- One-question-at-a-time approach (brainstorming principles)
- Mandatory confirmation before creation
- TDD checklist enforcement before save
- Multi-skill queue support

### Rationale

**Pros:**
- **User-friendly**: Guided experience vs command-line
- **Quality gates**: Mandatory checkpoints prevent bad skills
- **Transparent**: Shows "thinking" content for trust
- **Scalable**: Can handle queue of skills

**Cons:**
- **State management**: Complex conversation state
- **Latency**: Multiple round trips vs batch generation
- **LM dependency**: Quality of agent affects results

### Consequences

- `ConversationalAgent` manages state machine
- States: `READY`, `CLARIFYING`, `DEEP_UNDERSTANDING`, `CONFIRMING`, `CREATING`, `TDD_REFINE_PHASE`, `COMPLETE`
- Each state uses specific DSPy modules
- TDD checklist mandatory before skill save
- Supports skill revision workflow

---

## Change Process

To propose a new ADR or modify an existing one:

1. Create a draft ADR following this format
2. Discuss with the team (GitHub Discussions or PR)
3. Update status to `Accepted`, `Rejected`, or `Superseded`
4. Update related documentation and code

## References

- [ADR template](https://adr.github.io/)
- [DSPy documentation](https://dspy-docs.vercel.app/)
- [agentskills.io specification](https://agentskills.io/)
