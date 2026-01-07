---
name: memory-blocks-custom-memory
description: Custom memory block for storing and retrieving arbitrary contextual information.
metadata:
  skill_id: memory_blocks/custom_memory
  type: memory
---

# Custom Memory Skill  

## Overview  
The **Custom Memory** skill (`memory_blocks/custom_memory`) implements a lightweight key‑value store that can be used across the project to persist arbitrary context data. It abstracts the underlying storage mechanisms provided by the interaction history and project context blocks, offering a clean API for all memory operations.

## Files  
- `__init__.py` – package initializer, re‑exports public functions.  
- `store_context.py` – `store_context(key, value)` – persist a value under a given key.  
- `retrieve_context.py` – `retrieve_context(key, default=None)` – fetch a stored value.  
- `update_context.py` – `update_context(key, value)` – overwrite an existing entry.  
- `delete_context.py` – `delete_context(key)` – remove a key/value pair.  
- `list_all_keys.py` – `list_all_keys()` – enumerate all stored keys.

## Core Functions  

```python
def store_context(key: str, value: Any) -> None:
    """Persist `value` under `key` using the interaction history storage engine."""
    ...

def retrieve_context(key: str, default: Any = None) -> Any:
    """Retrieve the value associated with `key`, returning `default` if absent."""
    ...

def update_context(key: str, value: Any) -> None:
    """Replace the existing value for `key` with `value`."""
    ...

def delete_context(key: str) -> None:
    """Remove `key` and its value from the store."""
    ...

def list_all_keys() -> List[str]:
    """Return a list of all keys currently stored."""
    ...
```

## Composition Support  
- **Inheritance of storage** from `memory_blocks/interaction_history` provides robust, thread‑safe writes.  
- **Context initialization** from `memory_blocks/project_context` ensures that newly created entries are compatible with project‑wide metadata (e.g., namespace prefixes, validation schemas).  
- The skill can be **imported and composed** in any downstream module that requires context persistence.

## Documentation  
Each public function includes full docstrings, type hints, and error handling that mirrors the conventions of its parent skills.