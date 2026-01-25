# Import Path Guide

**Last Updated**: 2026-01-25

## Overview

After the FastAPI-centric restructure, Skills Fleet uses a **facade pattern** with clean public import paths. This guide provides canonical import paths for all modules.

`★ Insight ─────────────────────────────────────`
The facade pattern separates public API from implementation. Import from `skill_fleet.domain` for domain entities, `skill_fleet.api` for API components, and `skill_fleet.services` for business logic. Direct imports from `skill_fleet.core` or `skill_fleet.db` are for internal use.
`─────────────────────────────────────────────────`

## Recommended Import Patterns

### 1. Domain Layer (DDD Patterns)

```python
# Domain Models
from skill_fleet.domain import (
    Skill,
    SkillMetadata,
    Job,
    JobStatus,
    SkillType,
    SkillWeight,
    LoadPriority,
    TaxonomyPath,
)

# Domain Events
from skill_fleet.domain import (
    DomainEvent,
    SkillCreatedEvent,
    JobCompletedEvent,
)

# Domain Repositories (interfaces)
from skill_fleet.domain import (
    SkillRepository,
    JobRepository,
    TaxonomyRepository,
)

# Domain Services
from skill_fleet.domain import (
    SkillDomainService,
    JobDomainService,
    TaxonomyDomainService,
)

# Domain Specifications
from skill_fleet.domain import (
    Specification,
    AndSpecification,
    SkillIsReadyForPublication,
    JobCanBeStarted,
    JobRequiresHITL,
)
```

### 2. Service Layer

```python
# Base Service Classes
from skill_fleet.core.services import (
    BaseService,
    ServiceError,
    ValidationError,
    ConfigurationError,
)

# Conversation Service (from core/services)
from skill_fleet.core.services import (
    ConversationSession,
    ConversationMessage,
    ConversationState,
    MessageRole,
    AgentResponse,
)

# Cross-cutting Services (new services/ directory)
from skill_fleet.services import (
    BaseService,  # Re-exported from core.services
)
```

### 3. API Layer

```python
# FastAPI Application
from skill_fleet.api.app import create_app, get_app, app

# API Dependencies
from skill_fleet.api.dependencies import (
    SkillsRoot,
    DraftsRoot,
    TaxonomyManagerDep,
)

# API Exceptions
from skill_fleet.api.exceptions import (
    BadRequestException,
    NotFoundException,
    SkillFleetAPIException,
)

# Pydantic Schemas
from skill_fleet.api.schemas import (
    CreateSkillRequest,
    CreateSkillResponse,
    HitlPromptResponse,
    HitlResponseRequest,
)
```

### 4. DSPy Integration

```python
# Task-based Signatures (from dspy/ facade)
from skill_fleet.dspy.signatures import (
    GatherRequirements,
    AnalyzeIntent,
    GenerateContent,
    ValidateSkill,
)

# DSPy Modules
from skill_fleet.dspy.modules import (
    Phase1UnderstandingModule,
    Phase2ContentModule,
    Phase3ValidationModule,
)

# DSPy Programs
from skill_fleet.dspy.programs import (
    SkillCreationProgram,
)

# Streaming Support
from skill_fleet.core.dspy.streaming import (
    StreamingAssistant,
    stream_events_to_sse,
)
```

### 5. CLI Layer

```python
# CLI Commands
from skill_fleet.cli.app import app as cli_app

# CLI Client
from skill_fleet.cli.client import SkillFleetClient
```

### 6. LLM Configuration

```python
# DSPy Configuration
from skill_fleet.llm.dspy_config import (
    configure_dspy,
    get_lm_for_task,
)

# Provider Configuration
from skill_fleet.llm.fleet_config import (
    ProviderConfig,
    ModelConfig,
)
```

### 7. Taxonomy Management

```python
# Taxonomy Manager
from skill_fleet.taxonomy.manager import TaxonomyManager

# Taxonomy Models
from skill_fleet.taxonomy.models import (
    TaxonomyMetadata,
    SkillLocation,
)
```

### 8. Validation

```python
# Skill Validator
from skill_fleet.validators.skill_validator import (
    SkillValidator,
    ValidationReport,
    ValidationError as SkillValidationError,
)
```

### 9. Common Utilities

```python
# Security (path sanitization)
from skill_fleet.common.security import (
    sanitize_taxonomy_path,
    is_safe_path,
)

# Utilities
from skill_fleet.common.utils import (
    safe_json_loads,
    parse_skill_id,
)

# Path Utilities
from skill_fleet.common.paths import (
    get_skills_root,
    get_drafts_root,
)
```

## Module Organization

### Public API Surface (Facade)

```
skill_fleet/
├── domain/           # Domain-driven design layer
│   ├── models/       # Domain entities and value objects
│   ├── repositories/ # Repository interfaces
│   ├── services/     # Domain services
│   └── specifications/ # Business rules
│
├── services/         # Cross-cutting services
│   └── __init__.py   # Re-exports from core.services
│
├── dspy/             # DSPy integration facade
│   ├── signatures/   # Task-based signatures
│   ├── modules/      # DSPy modules
│   └── programs/     # DSPy programs
│
├── api/              # FastAPI application
│   ├── app.py        # Application factory
│   ├── routes/       # API endpoints
│   ├── schemas/      # Pydantic models
│   └── dependencies.py # Dependency injection
│
├── cli/              # Command-line interface
│   ├── app.py        # Typer application
│   └── client.py     # API client
│
└── infrastructure/   # Technical infrastructure
    └── database/     # Database layer re-exports
```

### Internal Implementation

```
skill_fleet/
├── core/             # Core business logic
│   ├── dspy/         # DSPy implementation
│   ├── services/     # Service implementations
│   ├── models.py     # Pydantic models
│   └── config.py     # Configuration
│
├── db/               # Database implementation
│   ├── models.py     # SQLAlchemy models
│   ├── repositories.py # Repository implementations
│   └── database.py   # Connection management
│
├── llm/              # LLM configuration
│   ├── dspy_config.py # DSPy setup
│   └── fleet_config.py # Provider config
│
└── common/           # Shared utilities
    ├── utils.py      # Utilities
    ├── paths.py      # Path helpers
    └── security.py   # Security functions
```

## Import Path Examples

### Example 1: Creating a Custom Domain Service

```python
# services/custom_skill_service.py
from skill_fleet.domain import (
    Skill,
    SkillRepository,
    SkillDomainService,
    SkillIsReadyForPublication,
)
from skill_fleet.core.services import BaseService

class CustomSkillService(BaseService):
    def __init__(self, skill_repo: SkillRepository):
        super().__init__()
        self.skill_repo = skill_repo
        self.domain_service = SkillDomainService(skill_repo)

    async def publish_skill(self, skill_id: str) -> Skill:
        """Publish a skill if it's ready."""
        skill = await self.skill_repo.get(skill_id)

        # Use specification pattern
        spec = SkillIsReadyForPublication(require_content=True)
        if not spec.is_satisfied_by(skill):
            raise ValidationError("Skill is not ready for publication")

        return await self.domain_service.publish(skill)
```

### Example 2: FastAPI Route with Service Layer

```python
# api/routes/custom.py
from fastapi import APIRouter, Depends
from skill_fleet.api.dependencies import SkillsRoot
from skill_fleet.domain import Job, JobStatus
from skill_fleet.core.dspy import SkillCreationProgram

router = APIRouter(prefix="/api/v2/custom", tags=["custom"])

@router.post("/create")
async def create_custom_skill(
    task_description: str,
    skills_root: SkillsRoot = Depends(),
):
    """Create a skill using the workflow orchestrator."""

    # Use DSPy program directly
    program = SkillCreationProgram()
    result = await program.aforward(
        task_description=task_description,
        user_context={"user_id": "api_user"},
        taxonomy_structure="{}",
        existing_skills="[]",
        hitl_callback=None,
        progress_callback=None,
    )

    return {"status": result.status, "skill_id": result.metadata.skill_id}
```

### Example 3: CLI Command Using API Client

```python
# cli/commands/custom.py
import typer
from skill_fleet.cli.client import SkillFleetClient
from skill_fleet.domain import JobStatus

app = typer.Typer()

@app.command()
def create_custom_skill(task: str):
    """Create a skill via the API."""
    client = SkillFleetClient()

    # Create skill
    response = client.create_skill(task_description=task)
    job_id = response["job_id"]

    # Poll for completion
    while True:
        job = client.get_job(job_id)
        status = job["status"]

        if status == JobStatus.COMPLETED:
            typer.echo(f"Skill created: {job['result']['skill_id']}")
            break
        elif status == JobStatus.FAILED:
            typer.error(f"Job failed: {job['error']}")
            break
        elif status == JobStatus.PENDING_HITL:
            typer.echo("Waiting for HITL response...")

        time.sleep(2)
```

## Before vs After Restructure

### Before (Old Import Paths)

```python
# Old: Direct imports from core
from skill_fleet.core.programs.skill_creator import SkillCreationProgram
from skill_fleet.core.models import SkillMetadata
from skill_fleet.taxonomy import TaxonomyManager
```

### After (New Import Paths)

```python
# New: Facade-based imports
from skill_fleet.dspy.programs import SkillCreationProgram
from skill_fleet.domain import SkillMetadata
from skill_fleet.taxonomy.manager import TaxonomyManager
```

## Migration Checklist

If you have code using old import paths:

- [ ] Update `skill_fleet.core.programs` → `skill_fleet.dspy.programs`
- [ ] Update `skill_fleet.core.models` → `skill_fleet.domain`
- [ ] Update `skill_fleet.core.services` → `skill_fleet.services` or keep as `skill_fleet.core.services`
- [ ] Update API route imports to use `skill_fleet.api.routes`
- [ ] Update validator imports to use `skill_fleet.validators`

## Best Practices

1. **Use facade imports** from `skill_fleet.domain`, `skill_fleet.api`, `skill_fleet.services`
2. **Avoid internal imports** from `skill_fleet.core`, `skill_fleet.db` unless necessary
3. **Import specific classes** rather than using `from module import *`
4. **Use type hints** with imported domain models
5. **Dependency injection** for services, not direct instantiation

## Troubleshooting

### Import Error: "No module named 'skill_fleet.domain'"

The domain layer was introduced in the restructure. Ensure you're using the latest version:

```bash
git pull origin main
uv sync
```

### Import Error: "Cannot import 'X' from 'skill_fleet.api'"

Some API components are in submodules:

```python
# Wrong
from skill_fleet.api import CreateSkillRequest

# Correct
from skill_fleet.api.schemas import CreateSkillRequest
```

### Multiple Import Paths Work

Both facade and direct imports work during the migration period. Prefer facade imports for new code.

```python
# Both work, prefer the first
from skill_fleet.domain import Skill  # Facade (recommended)
from skill_fleet.domain.models import Skill  # Direct (also works)
```

## See Also

- **[Architecture: Domain Layer](../architecture/DOMAIN_LAYER.md)** - DDD patterns and entities
- **[Architecture: Service Layer](../architecture/SERVICE_LAYER.md)** - Service architecture
- **[Contributing Guide](CONTRIBUTING.md)** - Development workflow
