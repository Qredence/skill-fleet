# Skill Creation Workflow (Agentic Skills System)

This document describes the Phase 1 skill creation workflow, its DSPy implementation, and how it integrates with the on-disk taxonomy.

## Architecture Overview

The system uses a **6-step pipeline** orchestrated by DSPy to transform a high-level task description into a fully validated, standards-compliant agent skill.

### Implementation Locations

- **Orchestrator**: `src/skill_fleet/workflow/creator.py`
- **Programs**: `src/skill_fleet/workflow/programs.py`
- **Modules**: `src/skill_fleet/workflow/modules.py`
- **Signatures**: `src/skill_fleet/workflow/signatures.py`
- **Models**: `src/skill_fleet/workflow/models.py`
- **Taxonomy Manager**: `src/skill_fleet/taxonomy/manager.py`

## Workflow Programs

The system provides different DSPy Programs for various use cases:

1.  **`SkillCreationProgram` (Standard)**: The default end-to-end pipeline (Steps 1-5).
2.  **`SkillCreationProgramQA` (Quality Assured)**: A high-fidelity version that uses `dspy.Refine` and `dspy.BestOfN` for critical steps (Understanding, Planning, Editing) to maximize quality at the cost of latency.
3.  **`QuickSkillProgram`**: A "fast path" for rapid prototyping that skips Initialization and Packaging (Steps 1, 2, 4 only).
4.  **`SkillRevisionProgram`**: Used during the Iterate phase to regenerate content based on feedback (Steps 4-5).

## Detailed Workflow Steps

Each step is encapsulated in a DSPy Module that returns strict Pydantic models.

### 1. UNDERSTAND
**Goal**: Map a user task to a specific taxonomy path.
- **Input**: User task description.
- **Module**: `UnderstandModule` / `UnderstandModuleQA` (uses `dspy.Refine`)
- **Output**: `UnderstandingResult`
    - `task_intent`: Distilled requirements.
    - `taxonomy_path`: Proposed path (e.g., `technical_skills/programming/python/async`).
    - `dependency_analysis`: Missing vs. optional skill dependencies.

### 2. PLAN
**Goal**: Define the skill's structure and capabilities.
- **Input**: Taxonomy path, parent skills context.
- **Module**: `PlanModule` / `PlanModuleQA` (uses `dspy.Refine`)
- **Output**: `PlanResult`
    - `skill_metadata`: Full `agentskills.io` metadata (see below).
    - `capabilities`: List of discrete `Capability` objects.
    - `dependencies`: `DependencyRef` objects with justification.
    - `composition_strategy`: How this skill fits with others.

### 3. INITIALIZE
**Goal**: Create the file skeleton on disk.
- **Input**: Skill metadata.
- **Module**: `InitializeModule`
- **Output**: `InitializeResult`
    - `skill_skeleton`: Directory tree (`capabilities/`, `tests/`, etc.) and file paths.

### 4. EDIT
**Goal**: Generate the actual content.
- **Input**: Skeleton, parent context.
- **Module**: `EditModule` / `EditModuleQA` (uses `dspy.BestOfN` to pick the best of 3 drafts)
- **Output**: `EditResult`
    - `skill_content`: The Markdown body for `SKILL.md`.
    - `capability_implementations`: Detailed docs for each capability.
    - `usage_examples`: Runnable code snippets.

### 5. PACKAGE
**Goal**: Validate and manifest.
- **Input**: Generated content.
- **Module**: `PackageModule` / `PackageModuleQA`
- **Output**: `PackageResult`
    - `validation_report`: Errors, warnings, and compliance checks.
    - `packaging_manifest`: Checksums and file lists.

### 6. ITERATE (HITL)
**Goal**: Human-in-the-Loop refinement.
- **Input**: Validation report, user feedback.
- **Module**: `IterateModule`
- **Output**: `IterateResult`
    - `approval_status`: `approved`, `needs_revision`, or `rejected`.
    - `revision_plan`: Specific instructions for the `SkillRevisionProgram`.

## Data Structures

### Scalable Discovery Metadata
To support large-scale taxonomies (500+ skills), the `SkillMetadata` model includes specialized fields:

-   **`category`**: Hierarchical path for grouping (e.g., `tools/web`).
-   **`keywords`**: List of search terms (e.g., `["playwright", "e2e"]`).
-   **`scope`**: Explicit definition of what the skill *does* and *does not* cover.
-   **`see_also`**: Cross-references to related skills.

### Human-in-the-Loop (HITL) Models
The workflow supports structured interaction via:
-   `ClarifyingQuestion`: Multi-choice or free-text questions.
-   `HITLSession`: Tracks rounds of feedback (min 1, max 4).

## Model Configuration

This repo is configured to use **Gemini 3** models via `config/config.yaml`:

-   **`gemini-3-flash-preview`**: Primary model for all steps.
-   **`gemini-3-pro-preview`**: Used for GEPA reflection and high-reasoning tasks.

## Optimization

The workflow supports automatic optimization using DSPy's `MIPROv2` and `GEPA` optimizers.
Run `skills-fleet optimize` to tune the prompts against the `config/training/trainset.json`.

---

## Further Reading

### Detailed Documentation

| Topic | Description |
|-------|-------------|
| **[DSPy Programs](../dspy/programs.md)** | Complete DSPy program reference |
| **[DSPy Signatures](../dspy/signatures.md)** | All DSPy signature definitions |
| **[DSPy Modules](../dspy/modules.md)** | DSPy module implementations |
| **[DSPy Optimization](../dspy/optimization.md)** | MIPROv2, GEPA, and tuning |
| **[HITL System](../hitl/)** | Human-in-the-Loop interactions |
| **[LLM Configuration](../llm/)** | Task-specific model configuration |

### Related Documentation

- **[System Overview](../overview.md)** - High-level system architecture
- **[Developer Reference](../concepts/developer-reference.md)** - Development workflows
- **[Getting Started](../getting-started/)** - Installation and quick start