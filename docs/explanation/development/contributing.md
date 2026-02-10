# Contributing to Skill Fleet

**Last Updated**: 2026-01-31

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) for package management
- Git

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd skill-fleet

# Install dependencies
uv sync

# Install development dependencies
uv sync --group dev

# Set up pre-commit hooks
uv run pre-commit install
```

### Environment Configuration

Create a `.env` file:

```bash
# Required: LLM API key
LITELLM_API_KEY=your_litellm_key
LITELLM_BASE_URL=http://localhost:4000
# or fallback:
GOOGLE_API_KEY=your_google_key

# Optional: Database (defaults to SQLite)
DATABASE_URL=sqlite:///skill_fleet.db

# Optional: Development settings
LOG_LEVEL=DEBUG
```

---

## Project Structure

```
skill_fleet/
├── src/skill_fleet/          # Main source code
│   ├── api/                  # FastAPI layer
│   ├── core/                 # DSPy workflows and modules
│   ├── infrastructure/       # Database, monitoring
│   └── cli/                  # Command-line interface
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── docs/                     # Documentation
├── config/                   # Configuration files
└── pyproject.toml            # Project configuration
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=skill_fleet --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_module.py

# Run integration tests
uv run pytest tests/integration/ -v
```

### Code Quality

```bash
# Type checking
uv run mypy src/skill_fleet

# Linting
uv run ruff check src/skill_fleet

# Formatting
uv run ruff format src/skill_fleet

# All checks (as CI would run)
uv run ruff check src/skill_fleet && uv run mypy src/skill_fleet && uv run pytest
```

### Running the API Server

```bash
# Development mode with auto-reload
uv run skill-fleet serve --reload

# With specific port
uv run skill-fleet serve --port 8080

# With auto-accept (skip interactive prompts)
uv run skill-fleet serve --auto-accept
```

---

## Adding New Modules

### Creating a DSPy Module

1. **Define the signature** in `core/signatures/{category}/`:

```python
# src/skill_fleet/core/signatures/my_category/my_feature.py
import dspy

class MyFeature(dspy.Signature):
    """Clear description of what this does."""

    input_field: str = dspy.InputField(desc="Description of input")
    output_field: str = dspy.OutputField(desc="Description of output")
```

2. **Create the module** in `core/modules/{category}/`:

```python
# src/skill_fleet/core/modules/my_category/my_feature.py
import dspy
from skill_fleet.core.modules.base import BaseModule
from skill_fleet.core.signatures.my_category.my_feature import MyFeature

class MyFeatureModule(BaseModule):
    """Module docstring."""

    def __init__(self):
        super().__init__()
        self.feature = dspy.ChainOfThought(MyFeature)

    def forward(self, input_data: str) -> dict:
        """Execute the module."""
        start_time = time.time()

        # Sanitize input
        clean_input = self._sanitize_input(input_data)

        # Execute
        result = self.feature(input_data=clean_input)

        # Build output
        output = {"output": result.output_field}

        # Validate
        if not self._validate_result(output, required=["output"]):
            output["output"] = "default"

        # Log
        self._log_execution(
            inputs={"input": clean_input[:100]},
            outputs=output,
            duration_ms=(time.time() - start_time) * 1000
        )

        return output
```

3. **Add tests**:

```python
# tests/unit/modules/my_category/test_my_feature.py
import pytest
from skill_fleet.core.modules.my_category.my_feature import MyFeatureModule

@pytest.fixture
def module():
    return MyFeatureModule()

def test_my_feature_success(module):
    result = module.forward("test input")
    assert "output" in result
    assert result["output"] is not None

def test_my_feature_empty_input(module):
    result = module.forward("")
    assert "output" in result  # Should handle gracefully
```

---

## API Development

### Adding New Endpoints

1. **Add to router** in `api/v1/`:

```python
# src/skill_fleet/api/v1/my_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-feature")

@router.post("/")
async def create_my_feature(request: MyFeatureRequest):
    """Endpoint description."""
    # Implementation
    return {"result": "success"}
```

2. **Register in main router**:

```python
# src/skill_fleet/api/main.py
from skill_fleet.api.v1 import my_feature

app.include_router(my_feature.router, prefix="/api/v1")
```

3. **Add tests**:

```python
# tests/integration/test_my_feature.py
def test_create_my_feature(client):
    response = client.post("/api/v1/my-feature/", json={"key": "value"})
    assert response.status_code == 200
```

---

## Documentation

### Docstring Style

Use Google-style docstrings:

```python
def my_function(arg1: str, arg2: int) -> dict:
    """Short description.

    Longer description if needed.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When input is invalid

    Example:
        >>> my_function("test", 42)
        {"result": "success"}
    """
```

### Updating Documentation

Documentation is in `docs/` using the Diátaxis framework:

- **Tutorials**: `docs/tutorials/` - Learning-oriented
- **How-To Guides**: `docs/how-to-guides/` - Task-oriented
- **Reference**: `docs/reference/` - Information-oriented
- **Explanation**: `docs/explanation/` - Understanding-oriented

When adding features, update relevant documentation sections.

---

## Testing Guidelines

### Unit Tests

- Test individual modules in isolation
- Mock external dependencies (LLM calls)
- Focus on edge cases and error handling

```python
@pytest.mark.asyncio
async def test_module_async():
    module = MyModule()

    # Mock the LLM call
    with patch.object(module.generator, 'acall') as mock_call:
        mock_call.return_value = MagicMock(output="test")

        result = await module.aforward("input")
        assert result["output"] == "test"
```

### Integration Tests

- Test workflow integration
- Use test database
- Verify end-to-end flow

```python
def test_skill_creation_workflow(client, db_session):
    # Create job
    response = client.post("/api/v1/skills/create", json={
        "task_description": "Create a Python skill"
    })
    job_id = response.json()["job_id"]

    # Poll for completion
    wait_for_job_completion(client, job_id)

    # Verify result
    job = client.get(f"/api/v1/jobs/{job_id}").json()
    assert job["status"] == "completed"
```

---

## Commit Guidelines

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build/tooling changes

**Examples**:
```
feat(modules): add GenerateTestCasesModule

Implements test case generation for validation workflow.
Generates positive, negative, and edge case tests.

fix(api): handle missing job_id in HITL response

docs: update module reference with new signatures
```

---

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release commit: `git commit -m "chore(release): version X.Y.Z"`
4. Tag release: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`

---

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issue for bugs/features
- **Discussions**: Use GitHub Discussions for questions

---

## Code Review Checklist

Before submitting PR:

- [ ] Tests pass (`uv run pytest`)
- [ ] Type checking passes (`uv run mypy`)
- [ ] Linting passes (`uv run ruff check`)
- [ ] Code is formatted (`uv run ruff format`)
- [ ] Docstrings added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if user-facing)
