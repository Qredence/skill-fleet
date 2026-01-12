# API Documentation

**Last Updated**: 2026-01-12
**Location**: `src/skill_fleet/api/`

## Overview

The Skills Fleet FastAPI REST API provides programmatic access to the skill creation workflow, taxonomy management, and validation services. The API supports asynchronous skill creation with Human-in-the-Loop (HITL) interactions through a job-based architecture.

`★ Insight ─────────────────────────────────────`
The API uses a **job-based pattern** for long-running skill creation. Instead of blocking HTTP requests, skills are created in background jobs. Clients poll for status and respond to HITL checkpoints via separate endpoints, making the API suitable for web UIs and webhooks.
`─────────────────────────────────────────────────`

## Quick Start

```bash
# Start the API server
uv run skill-fleet serve --port 8000

# Or using uvicorn directly
uvicorn skill_fleet.api:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

- **OpenAPI docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health check**: `http://localhost:8000/health`

## API Architecture

```mermaid
flowchart LR
    Client[Client] --> API[FastAPI Server]
    API --> Background[Background Tasks]
    API --> DSPy[DSPy Modules/Programs]
    API --> Taxonomy[Taxonomy Manager]

    Background --> Jobs[Job Store]
    Jobs --> HITL[HITL Checkpoints]

    Client -.->|Poll| Jobs
    Client -.->|Respond| HITL

    DSPy --> LLM[LLM Provider]
```

### Key Components

| Component | Description | File |
|-----------|-------------|------|
| **FastAPI App** | Main application with CORS, route registration | `app.py` |
| **Skills Routes** | Skill creation endpoints | `routes/skills.py` |
| **HITL Routes** | Human-in-the-Loop endpoints | `routes/hitl.py` |
| **Taxonomy Routes** | Taxonomy management endpoints | `routes/taxonomy.py` |
| **Validation Routes** | Skill validation endpoints | `routes/validation.py` |
| **Job System** | Background job management | `jobs.py` |
| **Discovery** | Auto-exposure of DSPy modules | `discovery.py` |

## Base URL

```
http://localhost:8000/api/v2
```

All endpoints are prefixed with `/api/v2` for versioning.

## Authentication

Currently, the API does not enforce authentication. For production use, you should:

1. Add API key middleware
2. Implement OAuth2/JWT authentication
3. Use environment variables for API secrets

```python
# Example: Add API key middleware
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.environ.get("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
```

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for web clients.

**Environment Variable:**
```bash
export SKILL_FLEET_CORS_ORIGINS="https://example.com,https://app.example.com"
```

**Default**: `*` (all origins allowed - not recommended for production)

## Response Format

All responses follow a consistent format:

**Success Response:**
```json
{
    "status": "success",
    "data": { ... }
}
```

**Error Response:**
```json
{
    "detail": "Error message"
}
```

**FastAPI HTTPException is used for errors:**
- `400`: Bad Request
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## API Endpoints Overview

| Route | Methods | Description |
|-------|---------|-------------|
| `/health` | GET | Health check |
| `/api/v2/skills` | POST | Create skill (async) |
| `/api/v2/hitl/{job_id}/prompt` | GET | Get HITL prompt for job |
| `/api/v2/hitl/{job_id}/response` | POST | Submit HITL response |
| `/api/v2/taxonomy` | GET | Get taxonomy structure |
| `/api/v2/taxonomy/xml` | GET | Generate agentskills.io XML |
| `/api/v2/validation/skill` | POST | Validate a skill |
| `/api/v2/validation/frontmatter` | POST | Validate YAML frontmatter |

## Auto-Discovery

The API automatically discovers and exposes DSPy modules:

```python
# Auto-exposed endpoints
/api/v2/programs/{module_name}  # All DSPy programs
/api/v2/modules/{module_name}   # All DSPy modules
```

Modules are discovered from:
- `skill_fleet.core.programs`
- `skill_fleet.core.modules`

## Next Steps

- **[Endpoints Documentation](endpoints.md)** - Detailed endpoint reference
- **[Schemas Documentation](schemas.md)** - Request/response models
- **[Middleware Documentation](middleware.md)** - CORS and error handling
- **[Jobs Documentation](jobs.md)** - Background job system

## Related Documentation

- **[DSPy Overview](../dspy/)** - DSPy architecture and modules
- **[HITL System](../hitl/)** - Human-in-the-Loop interactions
- **[CLI Reference](../cli-reference.md)** - Command-line interface
