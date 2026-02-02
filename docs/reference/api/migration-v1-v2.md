# API Versioning Guide

**Last Updated**: 2026-01-25

## Overview

Skills Fleet has two API versions with different purposes and stability levels:

| Version | Status | Purpose | Base Path |
|---------|--------|---------|-----------|
| **v2** | ✅ **Current/Stable** | Main API for skill creation, taxonomy, validation, HITL | `/api/v2/` |
| **v1** | 🔄 **Experimental** | Chat streaming endpoints (newer feature) | `/api/v1/` |

`★ Insight ─────────────────────────────────────`
The version numbers reflect the order of implementation, not stability. v2 is the production-ready, well-documented API. v1 was introduced later for experimental chat features and uses the v1 namespace to indicate it's still evolving.
`─────────────────────────────────────────────────`

## Version Comparison

### v2 API (Main/CURRENT)

**Status**: Production-ready, fully documented

**Purpose**: Core skill lifecycle operations

**Endpoints**:
- `POST /api/v2/skills/create` - Create skill (async with HITL)
- `GET /api/v2/skills/{path}` - Get skill by path or ID
- `GET /api/v2/hitl/{job_id}/prompt` - Get HITL prompt
- `POST /api/v2/hitl/{job_id}/response` - Submit HITL response
- `GET /api/v2/taxonomy` - Get taxonomy structure
- `GET /api/v2/taxonomy/xml` - Get agentskills.io XML
- `POST /api/v2/validation/skill` - Validate skill
- `POST /api/v2/evaluation/evaluate` - Evaluate skill quality
- `POST /api/v2/optimization/start` - Start DSPy optimization
- `GET /api/v2/jobs/{job_id}` - Get job status
- `POST /api/v2/drafts/{job_id}/promote` - Promote draft skill

**Workflow**: Asynchronous job-based pattern with Human-in-the-Loop checkpoints

### v1 API (Experimental)

**Status**: Experimental, newer feature

**Purpose**: Real-time conversational interface

**Endpoints**:
- `POST /api/v1/chat/stream` - Server-Sent Events (SSE) streaming chat
- `POST /api/v1/chat/sync` - Non-streaming chat (compatibility)

**Workflow**: Event-streaming pattern for real-time assistant responses

## When to Use Each Version

### Use v2 API when:
- Creating, validating, or managing skills
- Implementing HITL workflows
- Working with taxonomy and skill metadata
- Building production integrations
- Need stable, documented endpoints

### Use v1 API when:
- Building real-time chat interfaces
- Implementing streaming responses
- prototyping conversational features
- Can handle potential breaking changes

## Migration Considerations

### From v1 to v2 (Historical Context)

If you have code using a legacy "v1" API from before the restructure:

1. **Update base URLs**:
   ```python
   # Old (if existed)
   base_url = "http://localhost:8000/api/v1"

   # Current
   base_url = "http://localhost:8000/api/v2"
   ```

2. **Update endpoint paths**:
   ```python
   # Skill creation
   POST /api/v2/skills/create

   # HITL interactions
   GET /api/v2/hitl/{job_id}/prompt
   POST /api/v2/hitl/{job_id}/response
   ```

3. **Update response handling**:
   - v2 uses consistent JSON response format
   - All v2 endpoints support standard HTTP status codes

### For New Chat Features (v1)

The v1 chat API is intentionally separate because:
- It uses a different architectural pattern (SSE streaming vs job-based)
- It's still evolving and may have breaking changes
- It doesn't integrate with the HITL workflow system

**Example: Chat v1 vs Skills v2**

```python
# v1 Chat: Direct streaming response
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat/sync",
    json={"message": "Create a Python decorators skill"}
)
result = response.json()
# Returns: {"thinking": [...], "response": "..."}

# v2 Skills: Job-based with HITL
response = requests.post(
    "http://localhost:8000/api/v2/skills/create",
    json={"task_description": "Python decorators skill", "user_id": "user_123"}
)
job_id = response.json()["job_id"]
# Then poll HITL endpoint for interactive workflow
```

## Endpoint Mapping

| Feature | v2 (Main) | v1 (Experimental) |
|---------|-----------|-------------------|
| Skill creation | `POST /api/v2/skills/create` | N/A |
| Skill retrieval | `GET /api/v2/skills/{path}` | N/A |
| HITL workflow | `GET/POST /api/v2/hitl/{job_id}/*` | N/A |
| Taxonomy | `GET /api/v2/taxonomy` | N/A |
| Validation | `POST /api/v2/validation/*` | N/A |
| Evaluation | `POST /api/v2/evaluation/*` | N/A |
| Chat streaming | N/A | `POST /api/v1/chat/stream` |
| Chat sync | N/A | `POST /api/v1/chat/sync` |

## Breaking Changes Notice

### v2 API
- **Stability**: Production-ready
- **Breaking changes**: Unlikely without major version bump
- **Deprecation policy**: 6-month notice for breaking changes

### v1 Chat API
- **Stability**: Experimental
- **Breaking changes**: May occur without notice
- **Deprecation policy**: None (experimental feature)

## Future Plans

1. **v1 Chat Stabilization**: Once the chat API matures, it may be:
   - Merged into v2 as `/api/v2/chat/*`
   - Or kept separate at v1 if architectural patterns remain distinct

2. **v3 Consideration**: A future v3 API could:
   - Unify chat and skill creation patterns
   - Introduce GraphQL or gRPC alternatives
   - Provide WebSocket support for real-time features

## Best Practices

1. **Default to v2**: Use v2 for all production code
2. **Pin v1 explicitly**: If using v1 chat, pin the API version in your client
3. **Watch for deprecations**: Monitor changelog for v1 changes
4. **Provide feedback**: If using v1, share your use case to help stabilize it

## See Also

- **[v2 Endpoints Reference](endpoints.md)** - Complete v2 API documentation
- **[v2 Schemas](schemas.md)** - Request/response models
- **[Chat Interface](../concepts/conversational-interface.md)** - Chat system architecture
