# Caching Layer Architecture

**Last Updated**: 2026-01-25

## Overview

The caching layer provides in-memory caching for frequently accessed data, reducing database queries and API response times. It uses a decorator-based pattern for declarative cache configuration with intelligent invalidation.

`★ Insight ─────────────────────────────────────`
The cache uses TTL-based expiration with different strategies for different data types. Global data (taxonomy) has longer TTL (5min), user-specific data has medium TTL (2min), and branch-specific data has the longest TTL (10min) since taxonomy branches change infrequently.
`─────────────────────────────────────────────────`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     API Routes                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │  @cache_endpoint(ttl=300, pattern="/skills/*")   │  │
│  │  async def get_skill(...)                        │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  Cache Manager                           │
│  ┌──────────────────┐  ┌──────────────────────────┐    │
│  │   In-Memory      │  │    Pattern-Based         │    │
│  │   Cache Store    │◄─┤    Invalidation         │    │
│  │   (dict)         │  │    (regex matching)     │    │
│  └──────────────────┘  └──────────────────────────┘    │
└────────────────────────┬────────────────────────────────┘
                         │ Cache Miss
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Data Sources                                │
│  • Taxonomy Manager  • Job Store  • Repository          │
└─────────────────────────────────────────────────────────┘
```

## TTL Configuration

| Cache Type | TTL | Use Case |
|------------|-----|----------|
| **Global** | 5 minutes (300s) | Taxonomy structure, global settings |
| **User** | 2 minutes (120s) | User-specific data, profiles |
| **Branch** | 10 minutes (600s) | Taxonomy branch data |
| **Custom** | Configurable | Per-endpoint configuration |

### Default TTL Values

```python
# In cache manager
DEFAULT_TTL = 300  # 5 minutes
GLOBAL_TTL = 300   # 5 minutes
USER_TTL = 120     # 2 minutes
BRANCH_TTL = 600   # 10 minutes
```

## Usage Patterns

### 1. Decorator-Based Caching

```python
from skill_fleet.api.cache import cache_endpoint, cache_user_data, cache_branch_data

# Cache with default TTL (5 minutes)
@cache_endpoint
async def get_taxonomy():
    """Cached taxonomy response."""
    return TaxonomyManager().get_taxonomy()

# Cache with custom TTL
@cache_endpoint(ttl=600)
async def get_skill_details(skill_id: str):
    """Cached skill details (10 minutes)."""
    return TaxonomyManager().get_skill_metadata(skill_id)

# User-specific caching
@cache_user_data
async def get_user_profile(user_id: str):
    """Cached per-user data (2 minutes)."""
    return UserProfile.get(user_id)

# Branch-specific caching
@cache_branch_data
async def get_taxonomy_branch(branch_path: str):
    """Cached taxonomy branch (10 minutes)."""
    return TaxonomyManager().get_branch(branch_path)
```

### 2. Manual Cache Operations

```python
from skill_fleet.api.cache_manager import cache_manager

# Get from cache
cached_value = cache_manager.get("taxonomy:global")

# Set in cache
cache_manager.set("taxonomy:global", taxonomy_data, ttl=300)

# Invalidate by pattern
cache_manager.invalidate_pattern("/skills/*")
cache_manager.invalidate_pattern("/taxonomy/user/*")

# Clear all cache
cache_manager.clear()
```

### 3. Cache Invalidation on Write

```python
from skill_fleet.api.cache_manager import cache_manager

async def create_skill(skill_data):
    """Create a skill and invalidate related cache."""
    skill = await repository.create(skill_data)

    # Invalidate all skill-related cache entries
    cache_manager.invalidate_pattern("/skills/*")
    cache_manager.invalidate_pattern("/taxonomy/*")

    return skill
```

## Cache Key Generation

Cache keys are generated based on:

1. **Endpoint path**: The API route path
2. **Query parameters**: URL parameters
3. **User context**: For user-specific caches
4. **Custom key function**: Override default behavior

### Default Key Format

```
{cache_type}:{path}:{query_params_hash}:{user_id}
```

**Examples**:
- `global:/taxonomy:{}` - Global taxonomy
- `user:/taxonomy/user/abc123:{user_id}` - User taxonomy
- `endpoint:/skills/python-async:{}` - Skill details

### Custom Key Functions

```python
from skill_fleet.api.cache import cache_endpoint

@cache_endpoint(key_function=lambda kwargs: f"custom:{kwargs['skill_id']}")
async def get_skill(skill_id: str):
    """Use custom cache key."""
    return get_skill_by_id(skill_id)
```

## Pattern-Based Invalidation

The cache supports regex-based pattern invalidation for bulk cache clearing.

```python
from skill_fleet.api.cache_manager import cache_manager

# Invalidate all skill caches
cache_manager.invalidate_pattern("/skills/*")

# Invalidate all user taxonomy caches
cache_manager.invalidate_pattern("/taxonomy/user/*")

# Invalidate specific skill and its dependencies
cache_manager.invalidate_pattern(f"/skills/{skill_id}/*")
cache_manager.invalidate_pattern("/taxonomy/*")
```

### Common Invalidations

| Event | Invalidation Pattern |
|-------|---------------------|
| Skill created | `/skills/*`, `/taxonomy/*` |
| Skill updated | `/skills/{id}/*`, `/taxonomy/*` |
| Skill deleted | `/skills/{id}/*`, `/taxonomy/*` |
| Taxonomy updated | `/taxonomy/*` |
| User profile updated | `/user/{id}/*` |

## Cache Statistics

The cache manager provides statistics for monitoring and debugging.

```python
from skill_fleet.api.cache_manager import cache_manager

# Get cache statistics
stats = cache_manager.get_stats()
print(f"Hits: {stats['hits']}")
print(f"Misses: {stats['misses']}")
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Size: {stats['size']}")
```

**Statistics Output**:
```json
{
  "hits": 1523,
  "misses": 87,
  "hit_rate": 0.946,
  "size": 423,
  "evictions": 12,
  "invalidations": 45
}
```

## In-Memory Cache Implementation

The current implementation uses an in-memory dictionary:

```python
class InMemoryCache:
    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}
        self._stats = CacheStats()

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            self._stats.misses += 1
            return None

        if entry.is_expired():
            del self._cache[key]
            self._stats.misses += 1
            return None

        self._stats.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=time.time() + ttl,
        )
```

## Redis Migration Guide

For production deployments requiring distributed caching, migrate to Redis:

### 1. Install Dependencies

```bash
uv add redis
```

### 2. Configure Redis

```yaml
# config/config.yaml
cache:
  backend: redis  # or "memory" for in-memory
  redis:
    url: "redis://localhost:6379/0"
    prefix: "skill_fleet:"
    default_ttl: 300
```

### 3. Use Redis Backend

```python
from skill_fleet.api.cache_manager import get_cache_backend

# Automatically uses Redis if configured
cache = get_cache_backend()
await cache.set("key", value, ttl=300)
value = await cache.get("key")
```

### Redis vs In-Memory

| Feature | In-Memory | Redis |
|---------|-----------|-------|
| **Setup** | No dependencies | Requires Redis server |
| **Performance** | Fastest (local) | Fast (network) |
| **Scalability** | Single-process | Distributed |
| **Persistence** | Lost on restart | Optional persistence |
| **Use Case** | Development, single-instance | Production, multi-instance |

## Best Practices

### 1. Choose Appropriate TTL

```python
# ❌ Too short - cache ineffective
@cache_endpoint(ttl=10)
async def get_taxonomy():
    pass

# ✅ Appropriate for data that changes infrequently
@cache_endpoint(ttl=300)
async def get_taxonomy():
    pass

# ❌ Too long - stale data
@cache_endpoint(ttl=3600)
async def get_job_status(job_id: str):
    pass

# ✅ Short TTL for rapidly changing data
@cache_endpoint(ttl=30)
async def get_job_status(job_id: str):
    pass
```

### 2. Always Invalidate on Write

```python
async def update_skill(skill_id: str, data: dict):
    skill = await repository.update(skill_id, data)

    # Always invalidate cache after writes
    cache_manager.invalidate_pattern(f"/skills/{skill_id}/*")

    return skill
```

### 3. Use User-Specific Caching for Personalized Data

```python
@cache_user_data  # Automatically includes user_id in cache key
async def get_user_recommendations(user_id: str):
    return get_recommendations(user_id)
```

### 4. Monitor Cache Hit Rates

```python
# Periodically check cache health
stats = cache_manager.get_stats()
if stats['hit_rate'] < 0.7:
    logger.warning(f"Low cache hit rate: {stats['hit_rate']:.2%}")
    # Consider adjusting TTL or cache size
```

## Troubleshooting

### Low Hit Rate

**Symptoms**: Cache hit rate below 70%

**Solutions**:
1. Increase TTL for frequently accessed data
2. Check cache key generation - ensure consistency
3. Verify invalidation patterns aren't too broad
4. Monitor cache size - may need eviction policy

### Stale Data

**Symptoms**: Cache returns outdated data

**Solutions**:
1. Reduce TTL for rapidly changing data
2. Implement write-through caching
3. Add explicit invalidation on data changes
4. Use cache versioning

### High Memory Usage

**Symptoms**: Cache grows unbounded

**Solutions**:
1. Implement LRU eviction policy
2. Set maximum cache size
3. Use shorter TTLs
4. Move to Redis with configured maxmemory

## Configuration

```python
# In skill_fleet/api/cache_config.py
class CacheConfig:
    """Cache configuration."""

    # Default TTL
    DEFAULT_TTL = 300  # 5 minutes

    # Per-type TTL
    GLOBAL_TTL = 300
    USER_TTL = 120
    BRANCH_TTL = 600

    # Cache limits
    MAX_SIZE = 10000  # Maximum entries (in-memory only)
    EVICTION_POLICY = "lru"  # or "fifo", "lfu"

    # Redis configuration
    REDIS_URL = "redis://localhost:6379/0"
    REDIS_PREFIX = "skill_fleet:"
```

## See Also

- **[Service Layer](SERVICE_LAYER.md)** - Service architecture with caching
- **[API Endpoints](../api/endpoints.md)** - Cached endpoints
- **[Performance Tuning](../operations/PERFORMANCE.md)** - Production optimization
