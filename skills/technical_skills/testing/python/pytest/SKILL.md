---
name: pytest-foundations
description: A workflow-oriented guide to setting up and using pytest with modern
  Python best practices, including the src layout and pyproject.toml configuration.
category: technical_skills/testing/python
metadata:
  skill_id: technical_skills/testing/python/pytest-foundations
  version: 1.0.0
  type: technical
---

# pytest Foundations

Testing in Python has evolved. While the built-in `unittest` module is functional, `pytest` has become the industry standard due to its "no-boilerplate" philosophy, powerful fixture system, and rich ecosystem. This guide focuses on setting up a professional testing environment using modern packaging standards.

## Why pytest?

Unlike `unittest`, which requires creating classes and using specific method names like `assertEqual`, `pytest` allows you to write tests as simple functions using standard Python `assert` statements.

| Feature | unittest (Standard Library) | pytest |
| :--- | :--- | :--- |
| **Boilerplate** | High (Classes, setup methods) | Low (Functions, decorators) |
| **Assertions** | `self.assertEqual(a, b)` | `assert a == b` |
| **Fixtures** | `setUp` / `tearDown` methods | Flexible, scoped decorators |
| **Discovery** | Manual or basic | Automatic and highly configurable |

## Project Architecture: The `src` Layout

A common mistake in Python projects is putting source code in the root directory. Modern best practice dictates the `src` layout. This structure forces you to install your package to run tests, ensuring that your tests run against the code as a user would see it, rather than accidental local imports.

```text
my_project/
├── pyproject.toml      # Configuration "Source of Truth"
├── src/                # Application code
│   └── calculator/
│       ├── __init__.py
│       └── logic.py
└── tests/              # Test suite
    ├── conftest.py     # Shared fixtures
    └── test_logic.py   # Test modules
```

## Modern Configuration with `pyproject.toml`

Instead of scattered configuration files (`pytest.ini`, `setup.cfg`), use `pyproject.toml`. This centralizes your tool settings.

```toml
[tool.pytest.ini_options]
# Specifies where pytest should look for tests
testpaths = ["tests"]

# Ensures the src directory is on the path for discovery
pythonpath = ["src"]

# Default CLI arguments
# -ra: show extra test summary info
# -q: quiet mode (less verbose)
addopts = "-ra -q"
```

## Writing and Discovering Tests

Pytest discovers tests based on naming conventions:
- Files should be named `test_*.py` or `*_test.py`.
- Test functions should start with `test_`.

### A Basic Test
```python
# src/calculator/logic.py
def add(a: int, b: int) -> int:
    return a + b

# tests/test_logic.py
from calculator.logic import add

def test_add_integers():
    assert add(1, 2) == 3
```

### Running Tests
Execute your tests from the project root:
```bash
# Recommended: ensures the current environment is used
python -m pytest 
```

## Eliminating Repetition with Fixtures

Fixtures provide a way to supply data, objects, or state to your tests. They are defined using the `@pytest.fixture` decorator.

### Setup and Teardown
Use `yield` to handle setup and teardown logic within a single fixture.

```python
import pytest
import pathlib

@pytest.fixture
def temporary_file(tmp_path: pathlib.Path):
    # Setup: Create a file
    f = tmp_path / "hello.txt"
    f.write_text("content")
    
    yield f  # This is what the test receives
    
    # Teardown: (Optional) logic after the test finishes
    print("\nCleaning up...")
```

### Fixture Scope
You can control how often a fixture is created using the `scope` parameter:
- `function` (default): Run once per test function.
- `module`: Run once per module (`.py` file).
- `session`: Run once for the entire test run.

## Scaling Tests with Parametrization

Instead of writing five tests for five different inputs, use `@pytest.mark.parametrize`. This keeps your code DRY (Don't Repeat Yourself).

```python
import pytest
from calculator.logic import add

@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (10, 20, 30),
])
def test_add_various_inputs(a: int, b: int, expected: int):
    assert add(a, b) == expected
```

## Final Project Walkthrough

Imagine a simple user management logic:

**1. The Code (`src/auth/manager.py`)**
```python
class UserSession:
    def __init__(self, username: str):
        self.username = username
        self.active = True

    def logout(self):
        self.active = False
```

**2. The Tests (`tests/test_auth.py`)**
```python
import pytest
from auth.manager import UserSession

@pytest.fixture
def active_session():
    """Provides a fresh session for every test."""
    return UserSession(username="dev_user")

def test_initial_session_state(active_session: UserSession):
    assert active_session.username == "dev_user"
    assert active_session.active is True

def test_logout_deactivates_session(active_session: UserSession):
    active_session.logout()
    assert active_session.active is False
```

By following this foundation, your test suite remains maintainable, scalable, and integrated into the modern Python packaging ecosystem.