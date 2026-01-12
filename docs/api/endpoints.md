# API Endpoints Reference

**Last Updated**: 2026-01-12
**Base URL**: `http://localhost:8000/api/v2`

## Overview

This document provides detailed reference for all API endpoints, including request/response formats, status codes, and usage examples.

`★ Insight ─────────────────────────────────────`
Skill creation is asynchronous because it involves multiple LLM calls and HITL checkpoints. The job-based pattern allows the API to return immediately while the skill is created in the background. Clients poll for status and respond to HITL prompts as needed.
`─────────────────────────────────────────────────`

## Health Check

### GET /health

Check API availability and version.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
    "status": "ok",
    "version": "2.0.0"
}
```

---

## Skills Endpoints

### POST /api/v2/skills/create

Initiate a new skill creation job. The skill is created asynchronously in the background.

**Request:**
```http
POST /api/v2/skills/create
Content-Type: application/json

{
    "task_description": "Create a Python async/await programming skill",
    "user_id": "user_123"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_description` | `string` | Yes | Description of the skill to create |
| `user_id` | `string` | No | User identifier (default: "default") |

**Response (202 Accepted):**
```json
{
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "accepted"
}
```

**Error Response (400 Bad Request):**
```json
{
    "detail": "task_description is required"
}
```

**Job Lifecycle:**
```
pending → running → pending_hitl → running → completed
                        ↓
                      failed
```

---

## HITL Endpoints

Human-in-the-Loop (HITL) endpoints allow clients to interact with skill creation jobs at key checkpoints.

### GET /api/v2/hitl/{job_id}/prompt

Retrieve the current HITL prompt for a job. Poll this endpoint to check if the job needs human input.

**Request:**
```http
GET /api/v2/hitl/f47ac10b-58cc-4372-a567-0e02b2c3d479/prompt
```

**Response (200 OK):**
```json
{
    "status": "pending_hitl",
    "type": "clarify",
    "questions": [
        {
            "question": "What level of detail should this skill cover?",
            "options": ["beginner", "intermediate", "advanced"]
        }
    ],
    "rationale": "Need to understand target audience"
}
```

**HITL Types and Response Fields:**

| Type | Description | Response Fields |
|------|-------------|-----------------|
| **`clarify`** | Clarifying questions | `questions`, `rationale` |
| **`confirm`** | Confirm understanding | `summary`, `path` |
| **`preview`** | Preview content | `content`, `highlights` |
| **`validate`** | Validation results | `report`, `passed`, `skill_content` |

**Job Status Values:**
| Status | Description |
|--------|-------------|
| `pending` | Job queued, not yet started |
| `running` | Job in progress |
| `pending_hitl` | Awaiting human input |
| `completed` | Job finished successfully |
| `failed` | Job failed (check `error` field) |

---

### POST /api/v2/hitl/{job_id}/response

Submit a response to an HITL prompt.

**Request:**
```http
POST /api/v2/hitl/f47ac10b-58cc-4372-a567-0e02b2c3d479/response
Content-Type: application/json

{
    "action": "proceed",
    "response": "intermediate"
}
```

**Response Actions:**

| Action | Description |
|--------|-------------|
| `proceed` | Continue to next phase |
| `revise` | Restart current phase with feedback |
| `refine` | Run refinement with feedback |
| `cancel` | Cancel skill creation |

**Response (202 Accepted):**
```json
{
    "status": "accepted"
}
```

**Example Workflow:**

```python
import requests
import time

JOB_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
BASE_URL = "http://localhost:8000/api/v2"

# Create skill
response = requests.post(f"{BASE_URL}/skills/create", json={
    "task_description": "Create a Python async skill",
    "user_id": "user_123"
})
job_id = response.json()["job_id"]

# Poll for HITL prompts
while True:
    prompt = requests.get(f"{BASE_URL}/hitl/{job_id}/prompt").json()
    status = prompt["status"]

    if status == "pending_hitl":
        print(f"HITL Type: {prompt['type']}")
        print(f"Data: {prompt}")

        # Get user input
        action = input("Action (proceed/revise/refine/cancel): ")
        user_response = input("Response: ")

        # Submit response
        requests.post(f"{BASE_URL}/hitl/{job_id}/response", json={
            "action": action,
            "response": user_response
        })
    elif status == "completed":
        print("Skill completed!")
        print(prompt["skill_content"])
        break
    elif status == "failed":
        print(f"Job failed: {prompt['error']}")
        break

    time.sleep(2)
```

---

## Taxonomy Endpoints

### GET /api/v2/taxonomy

Get the full taxonomy structure.

**Request:**
```http
GET /api/v2/taxonomy
```

**Response (200 OK):**
```json
{
    "taxonomy": {
        "technical_skills": {
            "programming": {
                "languages": {
                    "python": {
                        "async": { ... },
                        "decorators": { ... }
                    }
                }
            }
        }
    },
    "total_skills": 42
}
```

---

### GET /api/v2/taxonomy/xml

Generate `<available_skills>` XML for agent context injection following agentskills.io standard.

**Request:**
```http
GET /api/v2/taxonomy/xml
```

**Response (200 OK):**
```xml
Content-Type: application/xml

<available_skills>
  <skill>
    <name>python-decorators</name>
    <description>Ability to design, implement, and apply Python decorators...</description>
    <location>/path/to/skills/technical_skills/programming/languages/python/decorators/SKILL.md</location>
  </skill>
  <skill>
    <name>python-async</name>
    <description>Proficiency with Python's async/await syntax...</description>
    <location>/path/to/skills/technical_skills/programming/languages/python/async/SKILL.md</location>
  </skill>
</available_skills>
```

---

## Validation Endpoints

### POST /api/v2/validation/skill

Validate a skill directory against taxonomy standards and agentskills.io compliance.

**Request:**
```http
POST /api/v2/validation/skill
Content-Type: application/json

{
    "skill_path": "skills/technical_skills/programming/python/decorators"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `skill_path` | `string` | Yes | Path to the skill directory |
| `strict` | `boolean` | No | Treat warnings as errors (default: false) |

**Response (200 OK):**
```json
{
    "status": "pass",
    "errors": [],
    "warnings": [
        {
            "check": "examples_count",
            "message": "Only 2 examples found, recommended minimum is 3"
        }
    ],
    "checks": [
        {
            "name": "metadata_exists",
            "status": "pass"
        },
        {
            "name": "frontmatter_valid",
            "status": "pass"
        },
        {
            "name": "yaml_frontmatter",
            "status": "pass"
        },
        {
            "name": "documentation_complete",
            "status": "pass"
        },
        {
            "name": "examples_present",
            "status": "warning"
        }
    ]
}
```

---

### POST /api/v2/validation/frontmatter

Validate SKILL.md YAML frontmatter for agentskills.io compliance.

**Request:**
```http
POST /api/v2/validation/frontmatter
Content-Type: application/json

{
    "content": "---\nname: python-decorators\ndescription: Ability to design and implement Python decorators\n---\n\n# Python Decorators\n..."
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `string` | Yes | Full SKILL.md content including frontmatter |

**Response (200 OK):**
```json
{
    "valid": true,
    "errors": [],
    "warnings": [],
    "parsed": {
        "name": "python-decorators",
        "description": "Ability to design and implement Python decorators"
    }
}
```

**Validation Checks:**
- Frontmatter exists (starts with `---`)
- Valid YAML syntax
- Required fields present (`name`, `description`)
- Name format: 1-64 chars, kebab-case
- Description length: 1-1024 chars

---

## Auto-Discovered Endpoints

DSPy modules and programs are automatically exposed as API endpoints:

```
/api/v2/programs/{module_name}
/api/v2/modules/{module_name}
```

Available modules depend on what's registered in:
- `skill_fleet.core.programs`
- `skill_fleet.core.modules`

**Example:**
```http
POST /api/v2/programs/SkillCreationProgram
Content-Type: application/json

{
    "task_description": "...",
    "user_context": {...},
    "taxonomy_structure": "{}",
    "existing_skills": "[]"
}
```

---

## Error Handling

The API uses standard HTTP status codes:

| Code | Description | Example |
|------|-------------|---------|
| **200** | Success | GET request successful |
| **202** | Accepted | Background job started |
| **400** | Bad Request | Missing required field |
| **404** | Not Found | Job ID doesn't exist |
| **422** | Validation Error | Invalid data format |
| **500** | Internal Server Error | Unexpected error |

**Error Response Format:**
```json
{
    "detail": "Human-readable error message"
}
```

---

## Rate Limiting

Currently, no rate limiting is enforced. For production use, consider:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v2/skills/create")
@limiter.limit("10/minute")
async def create_skill(...):
    ...
```

---

## Webhook Support (Future)

Webhooks allow the API to notify your application when jobs complete, rather than polling.

**Proposed Implementation:**
```python
# Create skill with webhook
{
    "task_description": "...",
    "webhook_url": "https://your-app.com/webhooks/skill-complete",
    "webhook_secret": "your-secret"
}

# Webhook payload (POST to webhook_url)
{
    "job_id": "...",
    "status": "completed",
    "result": {...},
    "signature": "hmac-sha256 hash"
}
```

---

## See Also

- **[API Overview](index.md)** - Architecture and setup
- **[Schemas Documentation](schemas.md)** - Request/response models
- **[Jobs Documentation](jobs.md)** - Background job system
- **[HITL System](../hitl/)** - Human-in-the-Loop details
