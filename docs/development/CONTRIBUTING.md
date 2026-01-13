# Contributing to Skills Fleet

Thank you for your interest in contributing to Skills Fleet! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup Steps

1. Clone the repository:
```bash
git clone https://github.com/Qredence/skill-fleet.git
cd skill-fleet
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Verify your installation:
```bash
uv run pytest tests/
```

## Code Style

### Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check code style
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Type Hints

- Use `str | int` syntax (Python 3.10+ union syntax)
- Import `from __future__ import annotations` in all modules
- Avoid `Any` when possible; use proper types
- All public functions must include type hints

### Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Include type hints in function signatures
- Document complex algorithms with inline comments

```python
from __future__ import annotations

from typing import Any

def process_skill(skill_id: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Process a skill with the given options.

    Args:
        skill_id: The unique identifier for the skill
        options: Optional processing options

    Returns:
        A dictionary containing processing results

    Raises:
        ValueError: If skill_id is invalid
    """
    ...
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/unit/test_workflow_modules.py

# Run with coverage
uv run pytest --cov=skill_fleet tests/

# Run with verbose output
uv run pytest -v tests/
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names following `test_<function>_<condition>` pattern
- Mock external dependencies (LMs, filesystem)
- Test both success and failure paths

```python
def test_safe_json_loads_with_valid_json():
    """Test safe_json_loads with valid JSON string."""
    result = safe_json_loads('{"key": "value"}')
    assert result == {"key": "value"}

def test_safe_json_loads_with_invalid_json():
    """Test safe_json_loads with invalid JSON returns default."""
    result = safe_json_loads('invalid json', default={})
    assert result == {}
```

## Pull Request Process

### Before Submitting

1. **Run tests locally**: Ensure all tests pass
2. **Run linting**: Fix any ruff issues
3. **Update documentation**: Document new features or API changes
4. **Update CHANGELOG.md**: Add your changes to the Unreleased section

### Submitting a PR

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```
3. Make your changes and commit:
```bash
git add .
git commit -m "feat: add new feature description"
```
4. Push to your fork:
```bash
git push origin feature/your-feature-name
```
5. Open a pull request against the main branch

### Commit Message Conventions

We follow semantic commit messages:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add revision feedback support to skill editing
fix: handle None values in safe_json_loads
docs: update API reference for new modules
test: add tests for common utility functions
```

### PR Checklist

Before submitting your PR, ensure:

- [ ] All tests pass locally
- [ ] Code passes `uv run ruff check .`
- [ ] Documentation updated for new features
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Commit messages follow conventions
- [ ] PR description clearly explains the changes

### Branch Protection & Required Checks

The `main` branch is protected with the following requirements:
- At least 1 approving review required
- All CI status checks must pass:
  - Linting (ruff check and format)
  - Tests (Python 3.12 and 3.13)
  - Build verification
  - Security checks
- All conversations must be resolved
- Linear history enforced (no merge commits)

See the [Branch Protection Guide](../../.github/BRANCH_PROTECTION.md) for complete details on repository protection rules.

## Project Structure

```
skill-fleet/
├── src/skill_fleet/
│   ├── agent/          # Conversational agent for skill creation
│   ├── analytics/      # Usage analytics and recommendations
│   ├── cli/            # Command-line interface
│   ├── common/         # Shared utilities
│   ├── llm/            # LLM configuration and DSPy setup
│   ├── onboarding/     # User onboarding and bootstrap
│   ├── taxonomy/       # Skill taxonomy management
│   ├── validators/     # Skill validation
│   └── workflow/       # DSPy-powered skill creation workflow
├── docs/               # Documentation
├── tests/              # Test suite
└── config/             # Configuration files
```

## Getting Help

- **Documentation**: Start with [docs/overview.md](../overview.md)
- **Issues**: Check [GitHub Issues](https://github.com/Qredence/skill-fleet/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/Qredence/skill-fleet/discussions) for questions

## License

By contributing to Skills Fleet, you agree that your contributions will be licensed under the same license as the project.
