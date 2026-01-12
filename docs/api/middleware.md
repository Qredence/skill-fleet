# API Middleware & Error Handling

**Last Updated**: 2026-01-12

## Overview

This document covers the middleware components and error handling strategies used in the Skills Fleet API.

`★ Insight ─────────────────────────────────────`
Middleware provides cross-cutting concerns like CORS, authentication, logging, and error handling. Centralizing these concerns ensures consistent behavior across all endpoints.
`─────────────────────────────────────────────────`

## CORS Middleware

Cross-Origin Resource Sharing (CORS) allows web browsers to make requests to the API from different origins.

### Configuration

**Location**: `src/skill_fleet/api/app.py`

```python
from fastapi.middleware.cors import CORSMiddleware

cors_origins_raw = os.environ.get("SKILL_FLEET_CORS_ORIGINS", "*")
cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Environment Variable

```bash
# Allow specific origins
export SKILL_FLEET_CORS_ORIGINS="https://example.com,https://app.example.com"

# Allow all origins (not recommended for production)
export SKILL_FLEET_CORS_ORIGINS="*"
```

### Security Considerations

| Setting | Development | Production |
|---------|-------------|------------|
| `allow_origins` | `["*"]` | Specific origins |
| `allow_credentials` | `True` | `True` if needed |
| `allow_methods` | `["*"]` | Specific methods |
| `allow_headers` | `["*"]` | Specific headers |

**Production Recommendation:**
```bash
export SKILL_FLEET_CORS_ORIGINS="https://your-frontend.com"
```

---

## Error Handling

### Global Exception Handler

FastAPI provides automatic exception handling. You can customize with:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
        }
    )
```

### HTTPException

For expected errors, use `HTTPException`:

```python
from fastapi import HTTPException

@app.get("/skills/{skill_id}")
async def get_skill(skill_id: str):
    skill = load_skill(skill_id)
    if skill is None:
        raise HTTPException(
            status_code=404,
            detail=f"Skill not found: {skill_id}"
        )
    return skill
```

### Validation Errors

Pydantic validation errors are handled automatically:

```json
{
    "detail": [
        {
            "loc": ["body", "task_description"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

### Custom Exception Handlers

Create handlers for specific exception types:

```python
class SkillFleetError(Exception):
    """Base exception for Skills Fleet errors."""
    pass

class TaxonomyNotFoundError(SkillFleetError):
    """Raised when a taxonomy path doesn't exist."""
    pass

@app.exception_handler(TaxonomyNotFoundError)
async def taxonomy_not_found_handler(request: Request, exc: TaxonomyNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": f"Taxonomy path not found: {exc.args[0]}"}
    )
```

---

## Logging Middleware

### Request Logging

```python
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {duration:.3f}s"
    )

    return response
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.post("/skills/create")
async def create_skill(request: CreateSkillRequest):
    logger.info("Creating skill",
        task_description=request.task_description,
        user_id=request.user_id,
    )
    ...
```

---

## Authentication Middleware (Future)

### API Key Authentication

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key from request header."""
    correct_key = os.environ.get("SKILL_FLEET_API_KEY")
    if api_key != correct_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/skills/create", dependencies=[Depends(verify_api_key)])
async def create_skill(...):
    ...
```

### JWT Authentication

```python
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/protected", dependencies=[Depends(verify_token)])
async def protected_route():
    ...
```

---

## Rate Limiting Middleware

### Using slowapi

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
    )

@app.post("/skills/create")
@limiter.limit("10/minute")
async def create_skill(...):
    ...
```

---

## Request ID Middleware

Add unique request IDs for tracing:

```python
import uuid

from fastapi import Request

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

## Compression Middleware

Enable response compression:

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## Trusted Host Middleware

Protect against host header attacks:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "example.com", "*.example.com"]
)
```

---

## Middleware Execution Order

Middleware runs in the order it's added (reverse for response):

```python
app.add_middleware(TrustedHostMiddleware, ...)
app.add_middleware(GZipMiddleware, ...)
app.add_middleware(CORSMiddleware, ...)

# Request flow:
# TrustedHost → GZip → CORS → Route Handler
# Response flow:
# Route Handler → CORS → GZip → TrustedHost
```

---

## See Also

- **[API Overview](index.md)** - Architecture and setup
- **[Endpoints Documentation](endpoints.md)** - Endpoint reference
- **[Jobs Documentation](jobs.md)** - Background job system
