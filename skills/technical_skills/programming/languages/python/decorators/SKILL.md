---
name: python-decorators
description: Use when extending or modifying function/class behavior without changing source code, implementing cross-cutting concerns (logging, auth, caching), or managing stateful function wrappers.
metadata:
  skill_id: technical_skills/programming/languages/python/decorators
  version: 1.1.0
  type: technical
  weight: medium
---

# Python Decorators: Functional and Metaprogramming Patterns

## Overview

Python decorators are a powerful form of metaprogramming used to modify or enhance the behavior of functions or classes without permanently modifying their source code. They rely on Python's first-class function support and closure mechanics.

**Core principle:** Use decorators to separate cross-cutting concerns (boilerplate) from core business logic using the "Onion" execution model.

## Capabilities

- Implement basic function wrappers for logging and timing
- Create parameterized decorators (decorator factories) for configurable behavior
- Preserve function identity and metadata using `functools.wraps`
- Build stateful decorators using classes or closures
- Apply multiple decorators with predictable execution order

## When to Use

**Use when:**
- Adding repetitive logic (logging, authentication, validation) to multiple functions.
- Modifying third-party library behavior without subclassing.
- Implementing caching (memoization) for expensive computations.
- Rate-limiting or retrying flaky operations.

**When NOT to use:**
- Simple logic that can be handled inside the function without cluttering it.
- When the modification changes the core intent of the function in a way that surprises callers.
- If overused, decorators can make debugging difficult due to obscured stack traces.

## Quick Reference

| Problem | Solution | Keywords |
| ------- | -------- | -------- |
| Losing `__name__` / `__doc__` | Use `@functools.wraps(func)` | metadata, wraps, introspection |
| Need arguments in decorator | Triple-nested function (factory) | parameterized, factory |
| Maintain state between calls | Use class with `__call__` or closure | stateful, counter, cache |
| Wrapping async functions | Must use `async def` in wrapper | async, await, coroutine |

## Core Patterns

### 1. The Standard Wrapper
**The problem:** Forgetting to preserve the original function's metadata breaks introspection tools, documentation generators, and debugging.

**❌ Common mistake:**
```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before call")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def say_hello():
    """Greet the user."""
    print("Hello!")

print(say_hello.__name__) # Outputs 'wrapper' instead of 'say_hello'
```

**✅ Production pattern:**
```python
from functools import wraps

def my_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def say_hello():
    """Greet the user."""
    print("Hello!")

print(say_hello.__name__) # Outputs 'say_hello'
```
**Key insight:** `functools.wraps` is non-negotiable for production decorators; it copies `__name__`, `__doc__`, and `__module__` from the original function.

### 2. Parameterized Decorators (Factories)
**The problem:** Hardcoding values inside decorators prevents reuse across different scenarios.

**❌ Common mistake:**
```python
def retry(func):
    def wrapper(*args, **kwargs):
        for _ in range(3): # Hardcoded!
            try: return func(*args, **kwargs)
            except: pass
    return wrapper
```

**✅ Production pattern:**
```python
def retry(times=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == times - 1: raise e
                    print(f"Retrying {func.__name__}...")
        return wrapper
    return decorator

@retry(times=5)
def unstable_api():
    import random
    if random.random() < 0.5:
        raise ConnectionError("Temporary failure")
    return "Success!"
```
**Key insight:** A parameterized decorator is a function that *returns* a decorator.

### 3. Stateful Decorators (Class-based)
**The problem:** Using global variables to track state across decorator calls is thread-unsafe and messy.

**❌ Common mistake:**
```python
calls = 0
def count_calls(func):
    def wrapper(*args, **kwargs):
        global calls
        calls += 1
        return func(*args, **kwargs)
    return wrapper
```

**✅ Production pattern:**
```python
class CallCounter:
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"Call {self.count} to {self.func.__name__}")
        return self.func(*args, **kwargs)

@CallCounter
def process_data(item_id: int):
    return f"Processed {item_id}"
```
**Key insight:** Classes with `__call__` provide a clean way to manage state within instance attributes.

### 4. Async Decorators
**The problem:** Applying a sync decorator to an async function causes "coroutine never awaited" warnings and functional failure.

**✅ Production pattern:**
```python
import asyncio
from functools import wraps

def async_logger(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"Running async {func.__name__}")
        result = await func(*args, **kwargs)
        return result
    return wrapper

@async_logger
async def fetch_data():
    await asyncio.sleep(1)
    return {"data": 123}
```
**Key insight:** Decorators for coroutines MUST be async and await the original function.

## Common Mistakes

| Mistake | Why It's Wrong | Fix |
| ------- | -------------- | --- |
| Missing `@wraps` | Destroys function metadata | Always use `functools.wraps` |
| Sync wrapper for async func | Coroutine isn't awaited | Use `async def wrapper` and `await func` |
| Forgetting `return` | Function returns `None` | Always return the result of `func(*args, **kwargs)` |
| Over-decorating | Debugging becomes impossible | Keep decorators focused and lean |

## Real-World Impact

- **Code Reuse:** Authentication logic implemented once via `@require_auth` saved 200+ lines across 50 API endpoints.
- **Performance:** Custom `@memoize` decorator reduced redundant database queries by 40%.
- **Observability:** Unified logging via decorators ensured 100% coverage of critical service calls.

## Strong Guidance

- **NO DECORATOR WITHOUT @WRAPS** — Always preserve metadata to prevent breaking introspection and debugging tools.
- **ALWAYS MATCH ASYNC STATUS** — Use async wrappers for async functions to avoid "coroutine never awaited" errors.
- **NEVER HIDE ORIGINAL EXCEPTIONS** — Ensure your decorator either handles exceptions transparently or re-raises them to avoid silent failures.
- **KEEP DECORATORS SIDE-EFFECT FREE** — Avoid decorators that modify global state or perform unexpected I/O unless that is their primary purpose.

## Red Flags

- Decorators that have massive side effects unrelated to the function's purpose.
- Deeply nested decorators (more than 3-4) that obscure execution flow.
- Decorators that change the return type in unexpected ways.

**All of these mean: Revisit your approach before proceeding.**

---

## Validation

```bash
# Test the decorator behavior
python -c "from functools import wraps; ... test code ..."

# Validate the skill directory
uv run skill-fleet validate skills/technical_skills/programming/languages/python/decorators
```