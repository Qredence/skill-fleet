# CLI Dependencies Review

## Unused Imports

### Found via ruff F401

- **src/skill_fleet/cli/commands/chat.py:10** - `rich.live.Live` imported but unused

**Details:**
- File uses `console.print()` and `console.status()` instead of `Live` context manager
- Import can be safely removed

## Circular Dependencies

### Analysis Results

No circular dependencies detected in the CLI module:

- **main.py imports**: Only imports from `skill_fleet.common.paths` (safe, one-way dependency)
- **interactive_cli.py imports**: No imports from `skill_fleet` modules
- **Potential circular patterns checked**:
  - `main.py <-> workflow.creator <-> agent.agent` - NOT PRESENT
  - `interactive_cli.py -> agent.agent -> interactive_cli.py` - NOT PRESENT

**Assessment**: Import structure is clean, no circular dependency issues found.

## Dependency Issues

### 1. Hardcoded Timeout
- **Location**: `src/skill_fleet/cli/client.py:19`
- **Issue**: `httpx.AsyncClient` timeout hardcoded to 30.0 seconds
- **Impact**: Users cannot configure timeout for slow API responses
- **Recommendation**: Add timeout parameter to CLI arguments

### 2. Rich Console Duplication
- **Count**: 13 separate `Console()` instantiations across 9 files
- **Files affected**:
  - `src/skill_fleet/cli/commands/serve.py` (1)
  - `src/skill_fleet/cli/app.py` (1)
  - `src/skill_fleet/cli/interactive_typer.py` (3)
  - `src/skill_fleet/cli/onboarding_cli.py` (1)
  - `src/skill_fleet/cli/main.py` (3)
  - `src/skill_fleet/cli/commands/chat.py` (1)
  - `src/skill_fleet/cli/interactive_cli.py` (1)
  - `src/skill_fleet/cli/commands/list_skills.py` (1)
  - `src/skill_fleet/cli/commands/create.py` (1)
- **Impact**: Inconsistent console configuration, potential style mismatches
- **Recommendation**: Create shared Rich console utility singleton

### 3. Async/Await Pattern Inconsistency
- **Analysis**: Mixed async/sync function usage across files
- **Files with more async than sync functions**:
  - `client.py`: 7 async, 1 sync (API client - expected)
- **Files with more sync than async functions**:
  - `commands/chat.py`: 1 async, 2 sync
  - `commands/create.py`: 1 async, 1 sync
  - `commands/list_skills.py`: 1 async, 1 sync
- **Assessment**: Pattern is appropriate for CLI entry points (sync wrapper around async operations)

## Version Compatibility

### All Dependencies Installed and Compatible

Checked dependencies from `pyproject.toml`:

| Dependency | Required | Installed | Status |
|------------|-----------|-----------|--------|
| dspy | >=3.0.4 | 3.1.0 | ✓ Compatible |
| rich | >=13.7.1 | 13.7.1 | ✓ Compatible |
| mlflow | >=3.8.1 | 3.8.1 | ✓ Compatible |
| fastapi[standard] | >=0.128.0 | 0.128.0 | ✓ Compatible |
| google-genai | >=1.56.0 | 1.56.0 | ✓ Compatible |
| litellm[proxy] | >=1.80.11 | 1.80.11 | ✓ Compatible |
| openai | >=2.14.0 | 2.14.0 | ✓ Compatible |
| pydantic | >=2.12.5 | 2.12.5 | ✓ Compatible |
| python-dotenv | >=1.2.1 | 1.2.1 | ✓ Compatible |
| pyyaml | >=6.0.0 | 6.0.3 | ✓ Compatible |
| typer | >=0.21.1 | 0.21.1 | ✓ Compatible |
| click | >=8.3.1 | 8.3.1 | ✓ Compatible |
| uvicorn[standard] | >=0.31.1 | 0.31.1 | ✓ Compatible |
| sqlalchemy | >=2.0.45 | 2.0.45 | ✓ Compatible |
| asyncpg | >=0.31.0 | 0.31.0 | ✓ Compatible |
| datasets | >=4.4.2 | 4.4.2 | ✓ Compatible |
| typing-extensions | >=4.0 | 4.15.0 | ✓ Compatible |

**Additional dependency detected**:
- **httpx**: 0.28.1 (not explicitly listed in pyproject.toml, likely transitive dependency via FastAPI/litellm)

**Python 3.12+ Features Used**:
- `from __future__ import annotations` (PEP 563) - Used in most files
- `type[]` syntax for generic types - Used throughout
- No deprecated APIs detected

## Recommendations

### 1. Remove Unused Imports
```bash
# Run ruff with --fix to remove unused import automatically
uv run ruff check src/skill_fleet/cli/ --select F401 --fix
```

### 2. Create Shared Rich Console Utility
Create `src/skill_fleet/cli/utils/console.py`:
```python
"""Shared Rich console configuration for CLI."""

from rich.console import Console
from rich.theme import Theme

# Define consistent color theme
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
})

# Singleton console instance
console = Console(theme=theme)
```

Then replace all `console = Console()` with:
```python
from skill_fleet.cli.utils.console import console
```

### 3. Consolidate Async Wrapper Pattern
Create shared async wrapper utility:
```python
"""Async CLI utilities."""

import asyncio
from functools import wraps
from rich.console import Console

console = Console()

def async_cli_command(func):
    """Decorator for async CLI commands."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user[/yellow]")
            return 1
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return 1
    return wrapper
```

### 4. Add Timeout Configuration
Update `client.py` to accept timeout parameter:
```python
def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
    """Initialize client."""
    self.base_url = base_url.rstrip("/")
    self.client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)
```

Add CLI argument in `app.py` or `main.py`:
```python
typer.Option("--timeout", default=30.0, help="API request timeout in seconds")
```

### 5. Document External Dependencies
Add `docs/dependencies.md` with:
- Purpose of each dependency
- Why specific version constraints exist
- Transitive dependencies to be aware of
- Security implications of each dependency

## Summary

### Critical Issues
- None identified

### High Priority Issues
1. Unused import in `commands/chat.py:10`
2. Hardcoded timeout in `client.py:19`

### Medium Priority Issues
1. Rich console duplication (13 instances)
2. No centralized configuration for theming

### Low Priority Issues
1. Mixed async/sync patterns (appropriate for CLI design)

### No Issues Found
- No circular dependencies
- No deprecated API usage
- All dependencies compatible
- Python 3.12+ features used correctly
