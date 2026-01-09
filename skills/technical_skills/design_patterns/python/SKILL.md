---
name: design-patterns-python
description: "> Skill Overview  \n> This skill teaches how to recognize, implement,\
  \ and combine classic software design patterns using modern Python features (type\
  \ hints, `abc`, `contextlib`, `asyncio`).  It is organized as a reusable package\
  \ that can be dropped into any Python project."
metadata:
  skill_id: technical_skills/design_patterns/python
  version: 1.0.0
  type: technical
  weight: medium
---

# Design Patterns in Python

> **Skill Overview**  
> This skill teaches how to recognize, implement, and combine classic software design patterns using modern Python features (type hints, `abc`, `contextlib`, `asyncio`).  It is organized as a reusable package that can be dropped into any Python project.

## Table of Contents
- [Folder Structure](#folder-structure)
- [Pattern Implementations](#pattern-implementations)
  - [Singleton](#singleton)
  - [Factory](#factory)
  - [Observer (Async)](#observer-async)
  - [Context Manager](#context-manager)
- [Examples](#examples)
- [Testing](#testing)
- [Composition & Integration](#composition--integration)
- [Contributing](#contributing)
- [License](#license)

---

### Folder Structure
```
patterns/
│   __init__.py
│   singleton.py
│   factory.py
│   observer.py
│   context_manager.py
│
examples/
│   __init__.py
│   example_singleton.py
│   example_factory.py
│   example_observer.py
│   example_context_manager.py
│
tests/
│   __init__.py
│   test_singleton.py
│   test_factory.py
│   test_observer.py
│   test_context_manager.py
│
README.md
```

---

### Pattern Implementations

#### Singleton (`patterns/singleton.py`)
```python
from abc import ABCMeta, abstractmethod

class Singleton(metaclass=ABCMeta):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @abstractmethod
    def operation(self):
        """Business‑specific operation."""
        pass
```

#### Factory (`patterns/factory.py`)
```python
from abc import ABCMeta, abstractmethod

class Factory(metaclass=ABCMeta):
    _creators = {}

    @classmethod
    def register(cls, key, creator):
        """Register a creator callable for a given key."""
        cls._creators[key] = creator

    @classmethod
    def create(cls, key, *args, **kwargs):
        """Instantiate the registered creator."""
        creator = cls._creators.get(key)
        if not creator:
            raise ValueError(f"No creator registered for key: {key}")
        return creator(*args, **kwargs)
```

#### Observer (Async) (`patterns/observer.py`)
```python
import asyncio
from abc import ABCMeta, abstractmethod

class Subject(metaclass=ABCMeta):
    def __init__(self):
        self._observers = set()

    async def attach(self, observer):
        self._observers.add(observer)

    async def detach(self, observer):
        self._observers.discard(observer)

    async def notify(self, state):
        """Notify all observers concurrently."""
        await asyncio.gather(*(obs.update(state) for obs in self._observers))

class ConcreteSubject(Subject):
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self._queue = queue

    async def some_operation(self, data):
        await self._queue.put(data)
        await self.notify(data)
```

#### Context Manager (`patterns/context_manager.py`)
```python
from contextlib import contextmanager

@contextmanager
def managed_resource(resource_path):
    """Open a file and guarantee closure."""
    resource = open(resource_path, 'r')
    try:
        yield resource
    finally:
        resource.close()
```

---

### Examples (`examples/`)

| Example | Description |
|---------|-------------|
| `example_singleton.py` | Demonstrates that only one instance of a class exists. |
| `example_factory.py`   | Shows how to register and retrieve objects via a factory. |
| `example_observer.py`  | Async subject notifies observers through an `asyncio.Queue`. |
| `example_context_manager.py` | Uses the `managed_resource` context manager safely. |

All examples can be executed directly (`python <file>.py`) and illustrate typical usage patterns.

---

### Testing (`tests/`)

Each pattern ships with a pytest suite:

- **`test_singleton.py`** – Verifies that multiple instantiations return the same object.  
- **`test_factory.py`** – Checks registration and creation of objects.  
- **`test_observer.py`** – Async test confirming that observers receive updates.  
- **`test_context_manager.py`** – Ensures the context manager closes resources properly.

Run the full suite with:
```bash
pytest -q
```

---

### Composition & Integration

This skill is designed to be **composed** with other technical skills:

| Integration Point | How to Combine |
|-------------------|----------------|
| **Testing Skill** | Import the provided test modules; extend them with property‑based tests (`hypothesis`). |
| **Concurrency Skill** | Replace the `asyncio.Queue` with a custom event loop or add back‑pressure strategies. |
| **Data Structures Skill** | Use specialized collections (e.g., `deque`, `PriorityQueue`) inside patterns for performance tuning. |
| **Domain‑Specific Patterns** | Wrap the generic patterns in domain‑oriented wrappers (e.g., `UserFactory`, `OrderObserver`). |

**Composition Patterns**  
1. **Pipeline Pattern** – Chain Singleton → Factory → Observer → Context Manager to build a processing pipeline.  
2. **Decorator‑Pattern Wrapper** – Decorate a Singleton with additional responsibilities without altering its core logic.  
3. **Strategy‑Pattern Plug‑in** – Swap the concrete `creator` in the Factory at runtime based on configuration files.

---

### Contributing
Contributions are welcome! Please:

1. Fork the repository.  
2. Create a feature branch (`git checkout -b feat/<name>`).  
3. Write tests for new patterns or extensions.  
4. Submit a Pull Request with a clear description.

---

### License
This project is licensed under the MIT License – see the `LICENSE` file for details.

---