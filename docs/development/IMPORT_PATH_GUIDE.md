# Import Path Guide

**Last Updated**: 2026-01-29
**Status**: Post-DSPy Architecture Migration

## Overview

After the DSPy workflow architecture migration, Skills Fleet uses a clean three-layer pattern: **Signatures → Modules → Workflows**. This guide provides canonical import paths for all modules.

## Current Architecture

```
src/skill_fleet/
├── dspy/                  # Centralized DSPy configuration ⭐
├── core/
│   ├── modules/          # DSPy modules
│   ├── signatures/       # DSPy signatures
│   ├── workflows/        # Workflow orchestration
│   └── models.py         # Domain models
├── api/                  # FastAPI application
├── cli/                  # CLI commands
├── common/               # Shared utilities
├── infrastructure/       # Technical infrastructure
├── taxonomy/             # Taxonomy management
└── validators/           # Skill validation
```

## Recommended Import Patterns

### 1. DSPy Configuration ⭐

**Primary Location**: `skill_fleet.dspy`

```python
# DSPy setup (NEW location - preferred)
from skill_fleet.dspy import configure_dspy, get_task_lm

# Configure DSPy globally
configure_dspy()

# Get language model for specific task
lm = get_task_lm("skill_understand")
edit_lm = get_task_lm("skill_edit")
```

**Note**: Old imports from `infrastructure/llm/` and `core/dspy/` no longer work.

### 2. Workflow Layer

**Primary Location**: `skill_fleet.core.workflows`

```python
# Skill creation workflows
from skill_fleet.core.workflows.skill_creation import (
    UnderstandingWorkflow,
    GenerationWorkflow,
    ValidationWorkflow,
)

# Use workflows
understanding = UnderstandingWorkflow()
result = await understanding.execute(
    task_description="Build a REST API",
    user_context={},
    taxonomy_structure={},
    existing_skills=[],
)
```

### 3. Module Layer (Direct Use)

**Primary Location**: `skill_fleet.core.modules`

```python
# Understanding modules
from skill_fleet.core.modules.understanding import (
    GatherRequirementsModule,
    AnalyzeIntentModule,
    FindTaxonomyPathModule,
    AnalyzeDependenciesModule,
)

# Generation modules
from skill_fleet.core.modules.generation import SkillContentGeneratorModule

# Validation modules
from skill_fleet.core.modules.validation import (
    ComplianceCheckerModule,
    QualityAssessorModule,
    SkillRefinerModule,
)

# HITL modules
from skill_fleet.core.modules.hitl import GenerateClarifyingQuestionsModule
```

### 4. Signature Layer (Type Definitions)

**Primary Location**: `skill_fleet.core.signatures`

```python
# Understanding signatures
from skill_fleet.core.signatures.understanding import (
    GatherRequirements,
    AnalyzeIntent,
    FindTaxonomyPath,
    AnalyzeDependencies,
    SynthesizePlan,
)

# Generation signatures
from skill_fleet.core.signatures.generation import (
    GenerateSkillContent,
    GenerateSkillSection,
)

# Validation signatures
from skill_fleet.core.signatures.validation import (
    ValidateCompliance,
    AssessQuality,
    RefineSkill,
)

# HITL signatures
from skill_fleet.core.signatures.hitl import GenerateClarifyingQuestions
```

### 5. API Layer

**Primary Location**: `skill_fleet.api`

```python
# FastAPI application
from skill_fleet.api.factory import create_app

# Services
from skill_fleet.api.services.skill_service import SkillService
from skill_fleet.api.services.job_manager import get_job_manager

# Schemas
from skill_fleet.api.schemas.skills import (
    CreateSkillRequest,
    CreateSkillResponse,
)

# Dependencies
from skill_fleet.api.dependencies import get_skill_service
```

### 6. Domain Models

**Primary Location**: `skill_fleet.core.models`

```python
from skill_fleet.core.models import (
    # Skill creation
    SkillCreationResult,
    SkillMetadata,
    PlanResult,
    
    # HITL
    HITLSession,
    ClarifyingQuestion,
    
    # Validation
    ValidationReport,
    QualityAssessment,
)
```

### 7. Common Utilities

**Primary Location**: `skill_fleet.common`

```python
# Security
from skill_fleet.common.security import (
    sanitize_taxonomy_path,
    resolve_path_within_root,
    is_safe_path,
)

# Utilities
from skill_fleet.common.utils import (
    safe_json_loads,
    safe_float,
)

# Paths
from skill_fleet.common.paths import (
    get_skills_root,
    get_drafts_root,
)
```

### 8. Taxonomy

**Primary Location**: `skill_fleet.taxonomy`

```python
from skill_fleet.taxonomy.manager import TaxonomyManager
```

### 9. Validation

**Primary Location**: `skill_fleet.validators`

```python
from skill_fleet.validators.skill_validator import SkillValidator
```

### 10. CLI

**Primary Location**: `skill_fleet.cli`

```python
from skill_fleet.cli.app import app as cli_app
```

## Deprecated Import Patterns ❌

These import paths **no longer work** after the migration:

```python
# ❌ Deleted directories
from skill_fleet.core.dspy import ...              # Directory deleted
from skill_fleet.infrastructure.llm import ...     # Directory deleted
from skill_fleet.onboarding import ...             # Directory deleted

# ❌ Deleted orchestrators
from skill_fleet.core.dspy.modules.workflows import TaskAnalysisOrchestrator  # Deleted
from skill_fleet.core.dspy.modules.workflows import ContentGenerationOrchestrator  # Deleted
from skill_fleet.core.dspy.modules.workflows import QualityAssuranceOrchestrator  # Deleted

# ❌ Old creator
from skill_fleet.core.creator import TaxonomySkillCreator  # Deleted
```

## Architecture Pattern: Signatures → Modules → Workflows

### Layer 1: Signatures (Type Definitions)

```python
# src/skill_fleet/core/signatures/understanding/requirements.py
import dspy

class GatherRequirements(dspy.Signature):
    """Gather and structure requirements from task description."""
    
    task_description = dspy.InputField(desc="Task description from user")
    user_context = dspy.InputField(desc="Additional user context")
    
    domain = dspy.OutputField(desc="Primary domain")
    category = dspy.OutputField(desc="Category within domain")
    target_level = dspy.OutputField(desc="Target skill level")
```

### Layer 2: Modules (Business Logic)

```python
# src/skill_fleet/core/modules/understanding/requirements.py
import dspy
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.understanding import GatherRequirements

class GatherRequirementsModule(BaseModule):
    """Module for gathering requirements from task descriptions."""
    
    def __init__(self):
        super().__init__()
        self.gather = dspy.ChainOfThought(GatherRequirements)
    
    def forward(self, task_description: str, user_context: str | None = None) -> dict:
        # Sanitize inputs
        task_description = self._sanitize_input(task_description)
        user_context = user_context or ""
        
        # Execute
        result = self.gather(
            task_description=task_description,
            user_context=user_context,
        )
        
        return self._parse_result(result)
```

### Layer 3: Workflows (Orchestration)

```python
# src/skill_fleet/core/workflows/skill_creation/understanding.py
from skill_fleet.core.modules.understanding import (
    GatherRequirementsModule,
    AnalyzeIntentModule,
    FindTaxonomyPathModule,
    AnalyzeDependenciesModule,
)

class UnderstandingWorkflow:
    """Orchestrates understanding phase modules with HITL support."""
    
    def __init__(self):
        self.requirements_module = GatherRequirementsModule()
        self.intent_module = AnalyzeIntentModule()
        self.taxonomy_module = FindTaxonomyPathModule()
        self.dependencies_module = AnalyzeDependenciesModule()
    
    async def execute(self, task_description, user_context, ...) -> dict:
        # Run modules in parallel
        results = await asyncio.gather(
            self._run_requirements(task_description, user_context),
            self._run_intent(task_description, ...),
            self._run_taxonomy(task_description, ...),
        )
        
        # Check for HITL checkpoint
        if needs_clarification(results):
            return {"status": "pending_user_input", ...}
        
        # Synthesize results
        return self._synthesize(results)
```

## Usage Examples

### Example 1: Creating a Skill via API

```python
# FastAPI route
from fastapi import APIRouter, Depends
from skill_fleet.api.services.skill_service import SkillService
from skill_fleet.api.schemas.skills import CreateSkillRequest, CreateSkillResponse

router = APIRouter()

@router.post("/skills/", response_model=CreateSkillResponse)
async def create_skill(
    request: CreateSkillRequest,
    skill_service: SkillService = Depends(get_skill_service),
):
    """Create a new skill."""
    result = await skill_service.create_skill(request)
    return result
```

### Example 2: Using Workflows Directly

```python
# Custom script or service
import asyncio
from skill_fleet.core.workflows.skill_creation import (
    UnderstandingWorkflow,
    GenerationWorkflow,
    ValidationWorkflow,
)

async def create_skill_workflow(task_description: str):
    """Run complete skill creation workflow."""
    
    # Phase 1: Understanding
    understanding = UnderstandingWorkflow()
    phase1_result = await understanding.execute(
        task_description=task_description,
        user_context={},
        taxonomy_structure={},
        existing_skills=[],
    )
    
    # Phase 2: Generation
    generation = GenerationWorkflow()
    phase2_result = await generation.execute(
        plan=phase1_result["plan"],
        understanding=phase1_result,
    )
    
    # Phase 3: Validation
    validation = ValidationWorkflow()
    phase3_result = await validation.execute(
        skill_content=phase2_result["skill_content"],
        plan=phase1_result["plan"],
    )
    
    return phase3_result

# Run it
result = asyncio.run(create_skill_workflow("Build a REST API"))
```

### Example 3: Using Individual Modules

```python
# For custom workflows or testing
from skill_fleet.core.modules.understanding import GatherRequirementsModule

# Create module
module = GatherRequirementsModule()

# Use it directly
result = module.forward(
    task_description="Build a React component library",
    user_context="{"experience": "intermediate"}",
)

print(result["domain"])       # "technical"
print(result["category"])     # "frontend"
print(result["topics"])       # ["react", "components"]
```

### Example 4: CLI Command

```python
# CLI using API client
import typer
from skill_fleet.cli.client import SkillFleetClient

app = typer.Typer()

@app.command()
def create_skill(task: str):
    """Create a skill via the API."""
    client = SkillFleetClient()
    
    response = client.create_skill(task_description=task)
    typer.echo(f"Job created: {response['job_id']}")
    typer.echo(f"Status: {response['status']}")
```

## Migration Checklist

If you have code using old import paths:

### From `core/dspy/` (Deleted)

- [ ] `from skill_fleet.core.dspy import configure_dspy` → `from skill_fleet.dspy import configure_dspy`
- [ ] `from skill_fleet.core.dspy.modules import ...` → `from skill_fleet.core.modules import ...`
- [ ] `from skill_fleet.core.dspy.signatures import ...` → `from skill_fleet.core.signatures import ...`
- [ ] `from skill_fleet.core.dspy.modules.workflows import TaskAnalysisOrchestrator` → `from skill_fleet.core.workflows.skill_creation import UnderstandingWorkflow`

### From `infrastructure/llm/` (Deleted)

- [ ] `from skill_fleet.infrastructure.llm import configure_dspy` → `from skill_fleet.dspy import configure_dspy`
- [ ] `from skill_fleet.infrastructure.llm.dspy_config import ...` → `from skill_fleet.dspy import ...`

### From `core/creator.py` (Deleted)

- [ ] `from skill_fleet.core.creator import TaxonomySkillCreator` → Use `SkillService` from `skill_fleet.api.services`

### From `onboarding/` (Deleted)

- [ ] `from skill_fleet.onboarding import SkillBootstrapper` → Feature removed, use API directly

## Troubleshooting

### Import Error: "No module named 'skill_fleet.core.dspy'"

The `core/dspy/` directory was deleted in the migration. Update your imports:

```python
# ❌ Wrong (old)
from skill_fleet.core.dspy import configure_dspy

# ✅ Correct (new)
from skill_fleet.dspy import configure_dspy
```

### Import Error: "No module named 'skill_fleet.infrastructure.llm'"

The `infrastructure/llm/` directory was deleted. Use the new location:

```python
# ❌ Wrong (old)
from skill_fleet.infrastructure.llm import configure_dspy

# ✅ Correct (new)
from skill_fleet.dspy import configure_dspy
```

### Import Error: "cannot import name 'TaskAnalysisOrchestrator'"

Orchestrators were replaced with Workflow classes:

```python
# ❌ Wrong (old)
from skill_fleet.core.dspy.modules.workflows import TaskAnalysisOrchestrator
orchestrator = TaskAnalysisOrchestrator()

# ✅ Correct (new)
from skill_fleet.core.workflows.skill_creation import UnderstandingWorkflow
workflow = UnderstandingWorkflow()
```

## Best Practices

1. **Use `skill_fleet.dspy`** for DSPy configuration
2. **Use workflows** for high-level operations
3. **Use modules directly** only when you need fine-grained control
4. **Use signatures** for type definitions, not business logic
5. **Import specific classes** rather than using `from module import *`
6. **Use type hints** with imported models

## See Also

- **[Architecture Status](../architecture/restructuring-status.md)** - Current architecture overview
- **[AGENTS.md](../../AGENTS.md)** - Developer working guide
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow
