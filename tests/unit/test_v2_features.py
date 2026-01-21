"""Tests for v2 Golden Standard features.

Tests for:
- Skill style detection (navigation_hub, comprehensive, minimal)
- Subdirectory validation
- Progressive disclosure detection
- Quality metrics for v2 features
- Phase 2 generation serialization utilities
"""

from pathlib import Path

import pytest

from skill_fleet.core.dspy.metrics.skill_quality import (
    assess_skill_quality,
    evaluate_code_examples,
    evaluate_patterns,
    evaluate_structure,
    parse_skill_content,
)
from skill_fleet.validators.skill_validator import SkillValidator


@pytest.fixture
def temp_skills_root(tmp_path: Path) -> Path:
    """Create a temporary skills root."""
    skills_root = tmp_path / "skills"
    (skills_root / "_templates").mkdir(parents=True)
    return skills_root


# =============================================================================
# Skill Style Detection Tests
# =============================================================================


def test_detect_skill_style_navigation_hub() -> None:
    """Test navigation_hub style detection: short SKILL.md with many subdirectory references."""
    content = """---
name: dspy-basics
description: Core DSPy fundamentals. Use when creating signatures or building simple DSPy programs.
---

# DSPy Basics

## Quick Start
```python
import dspy
lm = dspy.OpenAI(model='gpt-4')
dspy.settings.configure(lm=lm)
```

## When to Use This Skill
- Creating new signatures
- Building simple programs

## Core Concepts

### Signatures
See [references/signatures.md](references/signatures.md) for detailed signature definitions.

### Modules
See [references/modules.md](references/modules.md) for module patterns.

### Compilers
See [references/compilers.md](references/compilers.md) for compiler usage.

### Optimizers
See [references/optimizers.md](references/optimizers.md) for optimization techniques.

### Metrics
See [references/metrics.md](references/metrics.md) for evaluation metrics.

### Adapters
See [guides/adapters.md](guides/adapters.md) for adapter patterns.

### Testing
See [guides/testing.md](guides/testing.md) for testing strategies.

## Examples

See [examples/basic_program.py](examples/basic_program.py) for a complete example.
See [examples/advanced_program.py](examples/advanced_program.py) for advanced usage.
"""
    scores = assess_skill_quality(content)
    assert scores.skill_style_detected == "navigation_hub"
    assert scores.uses_progressive_disclosure is True


def test_detect_skill_style_comprehensive() -> None:
    """Test comprehensive style detection: long SKILL.md with all content inline."""
    content = """---
name: python-fastapi-production
description: Production FastAPI patterns. Use when building production-ready FastAPI APIs.
---

# FastAPI Production Patterns

## Overview
This skill covers production-ready FastAPI patterns including dependency injection, testing,
deployment, and monitoring.

## When to Use This Skill
- Building production FastAPI APIs
- Implementing dependency injection
- Setting up testing pipelines
- Deploying FastAPI applications

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI, Depends
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str

@app.post("/items/")
async def create_item(item: Item):
    return item
```

### Dependency Injection

```python
from fastapi import Depends, FastAPI

def get_db():
    return "db_connection"

@app.get("/users/")
async def read_users(db = Depends(get_db)):
    return {"users": [], "db": db}
```

## Core Patterns

### Dependency Injection Pattern

FastAPI's dependency injection system is powerful. Use it for:
- Database connections
- Authentication
- Configuration
- Logging

**Good Practice:**
```python
def get_current_user(token: str = Depends(verify_token)):
    return {"user_id": "123"}
```

**Anti-Pattern:**
```python
# Don't pass dependencies manually
@app.get("/users/")
async def read_users(db = get_db()):  # ❌ Wrong
    return {"users": db}
```

### Error Handling Pattern

Use FastAPI's exception handlers for consistent error responses.

```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

app.add_exception_handler(HTTPException, http_exception_handler)
```

### Testing Pattern

Use pytest with httpx for FastAPI testing.

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
```

## Production Patterns

### Database Pooling

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10,
    max_overflow=20,
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/items/")
@limiter.limit("100/minute")
async def read_items():
    return {"items": []}
```

### Monitoring

```python
from prometheus_client import Counter

REQUEST_COUNT = Counter('request_count', 'Total requests')

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.inc()
    return response
```

## Common Mistakes

### Using sync I/O in async endpoints

**Don't do this:**
```python
@app.get("/items/")
async def read_items():
    items = db.query(Item).all()  # ❌ Blocking
    return items
```

**Do this instead:**
```python
@app.get("/items/")
async def read_items():
    items = await db.execute(select(Item))  # ✅ Async
    return items
```

### Not validating request bodies

Always use Pydantic models for validation.

```python
class Item(BaseModel):
    name: str  # Pydantic validates this

@app.post("/items/")
async def create_item(item: Item):
    return item  # item is validated
```

## Red Flags

⚠️ **Red Flag**: Disabling CORS completely in production
⚠️ **Red Flag**: Returning raw exceptions to clients
⚠️ **Red Flag**: Not using dependency injection for shared resources
⚠️ **Red Flag**: Mixing sync and async code in endpoints

## Best Practices

1. **Use async/await** throughout your application
2. **Validate all inputs** with Pydantic models
3. **Use dependency injection** for shared resources
4. **Write tests** for all endpoints
5. **Implement error handling** at the application level
6. **Add logging** and monitoring
7. **Use environment variables** for configuration
8. **Deploy with proper SSL** and security headers

## Key Insights

- **Dependency injection is your friend**: Use it for database connections, auth, config
- **Testing is not optional**: FastAPI's TestClient makes testing easy
- **Async I/O matters**: Don't block your event loop with sync operations
- **Validation saves time**: Let Pydantic handle input validation
- **Error handling matters**: Use exception handlers for consistent responses
"""
    scores = assess_skill_quality(content)
    assert scores.skill_style_detected == "comprehensive"
    assert scores.uses_progressive_disclosure is False


def test_detect_skill_style_minimal() -> None:
    """Test minimal style detection: focused SKILL.md, few sections/content."""
    content = """---
name: vibe-coding
description: Rapidly prototype web apps. Use when you want to quickly build something with creative flow.
---

# Vibe Coding

## When to Use This Skill
- You want to **rapidly prototype** a new web application

## Quick Start

```bash
npx create-next-app@latest my-app
```
"""
    scores = assess_skill_quality(content)
    assert scores.skill_style_detected == "minimal"
    assert scores.uses_progressive_disclosure is False


# =============================================================================
# Subdirectory Validation Tests
# =============================================================================


def test_validate_references_subdirectory(temp_skills_root: Path) -> None:
    """Test that references/ subdirectory is recognized and validated."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "references").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.
""",
        encoding="utf-8",
    )

    (skill_dir / "references" / "api.md").write_text("# API Reference\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    assert results.passed is True
    assert results.errors == []


def test_validate_guides_subdirectory(temp_skills_root: Path) -> None:
    """Test that guides/ subdirectory is recognized and validated."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "guides").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

See [guides/setup.md](guides/setup.md) for setup instructions.
""",
        encoding="utf-8",
    )

    (skill_dir / "guides" / "setup.md").write_text("# Setup Guide\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    assert results.passed is True
    assert results.errors == []


def test_validate_templates_subdirectory(temp_skills_root: Path) -> None:
    """Test that templates/ subdirectory is recognized and validated."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "templates").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

See [templates/starter.py](templates/starter.py) for starter template.
""",
        encoding="utf-8",
    )

    (skill_dir / "templates" / "starter.py").write_text("# Starter\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    assert results.passed is True
    assert results.errors == []


def test_validate_scripts_subdirectory(temp_skills_root: Path) -> None:
    """Test that scripts/ subdirectory is recognized and validated."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "scripts").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

See [scripts/setup.sh](scripts/setup.sh) for setup script.
""",
        encoding="utf-8",
    )

    (skill_dir / "scripts" / "setup.sh").write_text("#!/bin/bash\n", encoding="utf-8")

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    assert results.passed is True
    assert results.errors == []


def test_validate_invalid_subdirectory_name(temp_skills_root: Path) -> None:
    """Test that invalid subdirectory names generate warnings."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "invalid_dir").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.
""",
        encoding="utf-8",
    )

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    # Should pass but warn about unknown subdirectory
    assert results.passed is True
    assert any("unknown subdirectory" in w for w in results.warnings)


def test_validate_legacy_subdirectory_warning(temp_skills_root: Path) -> None:
    """Test that legacy subdirectory names (capabilities/, resources/, tests/) generate warnings."""
    skill_dir = temp_skills_root / "test_skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "capabilities").mkdir()
    (skill_dir / "resources").mkdir()
    (skill_dir / "tests").mkdir()

    (skill_dir / "SKILL.md").write_text(
        """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.
""",
        encoding="utf-8",
    )

    validator = SkillValidator(temp_skills_root)
    results = validator.validate_subdirectories(skill_dir)

    # Should pass but warn about legacy subdirectories
    assert results.passed is True
    warnings_text = " ".join(results.warnings).lower()
    assert "deprecated" in warnings_text or "legacy" in warnings_text


# =============================================================================
# Progressive Disclosure Detection Tests
# =============================================================================


def test_detects_progressive_disclosure_with_links() -> None:
    """Test progressive disclosure detection with markdown links."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Core Concepts

### Pattern 1
See [references/pattern1.md](references/pattern1.md) for details.

### Pattern 2
See [references/pattern2.md](references/pattern2.md) for details.

### Pattern 3
See [references/pattern3.md](references/pattern3.md) for details.

## Guides

See [guides/setup.md](guides/setup.md) for setup.
See [guides/deploy.md](guides/deploy.md) for deployment.
"""
    frontmatter, body = parse_skill_content(content)
    flags, _, strengths = evaluate_structure(body)

    assert flags["uses_progressive_disclosure"] is True
    assert any("progressive disclosure" in s for s in strengths)


def test_detects_progressive_disclosure_with_text_refs() -> None:
    """Test progressive disclosure detection with text references."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Documentation

For more detailed information, see the `references/` directory.

The `guides/` directory contains step-by-step tutorials.

Check `templates/` for reusable code snippets.

Additional scripts are available in the `scripts/` directory.
"""
    frontmatter, body = parse_skill_content(content)
    flags, _, strengths = evaluate_structure(body)

    assert flags["uses_progressive_disclosure"] is True
    assert any("progressive disclosure" in s for s in strengths)


def test_detects_progressive_disclosure_with_section_headers() -> None:
    """Test progressive disclosure detection with section headers."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Reference Files

Detailed documentation is available in separate reference files.

## Guide Files

Step-by-step guides are available in the guides directory.

## Templates

Reusable templates are available in the templates directory.
"""
    frontmatter, body = parse_skill_content(content)
    flags, _, strengths = evaluate_structure(body)

    assert flags["uses_progressive_disclosure"] is True


def test_no_progressive_disclosure_detected() -> None:
    """Test that skills without subdirectory references don't trigger progressive disclosure."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Pattern 1
All content is inline here.

## Pattern 2
All content is inline here too.

## Pattern 3
Everything is inline, no external references.
"""
    frontmatter, body = parse_skill_content(content)
    flags, _, _ = evaluate_structure(body)

    assert flags["uses_progressive_disclosure"] is False


# =============================================================================
# Quality Metrics Tests for v2 Features
# =============================================================================


def test_has_when_to_use_section_required() -> None:
    """Test that 'When to Use This Skill' section is detected."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Use this skill when testing.

## Quick Start
Quick start here.
"""
    scores = assess_skill_quality(content)

    assert scores.has_when_to_use_section is True
    assert scores.has_when_to_use is True  # v1 alias
    assert scores.has_quick_start is True

    # Should have strength for required section
    assert any("When to Use" in s for s in scores.strengths)


def test_when_to_use_section_missing_generates_issue() -> None:
    """Test that missing 'When to Use' section generates issue."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## Overview
Test skill.

## Quick Start
Quick start here.
"""
    scores = assess_skill_quality(content)

    assert scores.has_when_to_use_section is False
    assert scores.has_when_to_use is False

    # Should have issue about missing section
    assert any("When to Use" in issue for issue in scores.issues)


def test_has_quick_start_recommended() -> None:
    """Test that Quick Start section is detected and recommended."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Quick Start
```python
print("quick start")
```
"""
    scores = assess_skill_quality(content)

    assert scores.has_quick_start is True

    # Should have strength for recommended section
    assert any("Quick Start" in s for s in scores.strengths)


def test_quick_start_missing_generates_warning() -> None:
    """Test that missing Quick Start section doesn't fail but may warn."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Overview
Test skill.

## Patterns
Some patterns here.
"""
    scores = assess_skill_quality(content)

    assert scores.has_quick_start is False

    # Should have warning about missing Quick Start
    # (This is recommended, not required, so overall score may still be good)
    # The warning is in the issues list for awareness


def test_uses_progressive_disclosure_flag() -> None:
    """Test that progressive disclosure flag is set in quality scores."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## References
See [references/api.md](references/api.md) for API docs.

## Guides
See [guides/tutorial.md](guides/tutorial.md) for tutorial.
"""
    scores = assess_skill_quality(content)

    assert scores.uses_progressive_disclosure is True

    # Should have strength for using progressive disclosure
    assert any("progressive disclosure" in s for s in scores.strengths)


def test_skill_style_detected_field() -> None:
    """Test that skill style is detected and set in quality scores."""
    # Navigation hub
    content_hub = """---
name: test-hub
description: Test hub skill.
---
# Test

## When to Use This Skill
Testing hub.

See [references/doc1.md](references/doc1.md)
See [references/doc2.md](references/doc2.md)
See [references/doc3.md](references/doc3.md)
"""
    scores_hub = assess_skill_quality(content_hub)
    assert scores_hub.skill_style_detected == "navigation_hub"

    # Comprehensive
    content_comp = (
        """---
name: test-comprehensive
description: Test comprehensive skill.
---
# Test

## When to Use This Skill
Testing comprehensive.

## Pattern 1
Content

## Pattern 2
Content

## Pattern 3
Content

## Pattern 4
Content

## Pattern 5
Content

## Pattern 6
Content
"""
        + "Content\n" * 1000  # Make content clearly > 8000 characters
    )
    scores_comp = assess_skill_quality(content_comp)
    assert scores_comp.skill_style_detected == "comprehensive"

    # Minimal
    content_min = """---
name: test-minimal
description: Test minimal skill.
---
# Test

## When to Use This Skill
Testing minimal.

## Pattern 1
Content.

## Pattern 2
Content.

## Pattern 3
Content.
"""
    scores_min = assess_skill_quality(content_min)
    assert scores_min.skill_style_detected == "minimal"


def test_overall_quality_score_with_v2_metrics() -> None:
    """Test that v2 metrics contribute to overall quality score."""
    # High quality v2 skill with all v2 features
    content = """---
name: perfect-v2-skill
description: Use when testing v2 quality metrics with all features.
---

# Perfect v2 Skill

## When to Use This Skill
Use this skill when testing all v2 Golden Standard features.

## Quick Start

```python
# Quick start example
print("Perfect v2 skill")
```

    ## Overview
    This skill demonstrates all v2 Golden Standard features.
    
    ## Core Principle
    
    > **Core principle:** Documentation must be modular and progressively disclosed.
    
    ## Iron Law
    
    **ALWAYS** include a Quick Start section for technical skills.
    **NEVER** skip the "When to Use" section.
    
    ## Core Patterns

### Pattern 1: With Anti-Pattern
**Good Practice ✅**:
```python
# Good code
def good_function():
    return "good"
```

**Anti-Pattern ❌**:
```python
# Bad code
def bad_function():
    return "bad"
```

### Pattern 2: With Key Insight
**Key Insight**: Patterns should have both good and bad examples for maximum clarity.

### Pattern 3: Production Pattern
Use this production pattern for best results:
```python
# Production code
def production_function():
    return "production"
```

    ## Common Mistakes
    
    Don't make these common mistakes:
    1. Missing Quick Start section
    2. Not using progressive disclosure
    3. Forgetting "When to Use" section
    
    ## Red Flags
    
    - No input validation
    - Hardcoded secrets
    
    ## Real World Impact

This skill has been tested in production environments and improved quality scores by 25%.

## References

See [references/api.md](references/api.md) for detailed API documentation.
See [references/patterns.md](references/patterns.md) for more patterns.

## Guides

See [guides/setup.md](guides/setup.md) for setup guide.
See [guides/troubleshooting.md](guides/troubleshooting.md) for troubleshooting.
"""
    scores = assess_skill_quality(content)

    # All v2 features should be detected
    assert scores.has_when_to_use_section is True
    assert scores.has_quick_start is True
    assert scores.uses_progressive_disclosure is True
    assert scores.has_common_mistakes is True
    assert scores.has_red_flags is True
    assert scores.has_real_world_impact is True
    assert scores.has_anti_patterns is True
    assert scores.has_production_patterns is True
    assert scores.has_key_insights is True

    # Overall score should be high (all features present)
    assert scores.overall_score >= 0.8

    # Should have many strengths, few issues
    assert len(scores.strengths) > len(scores.issues)


def test_code_examples_quality() -> None:
    """Test code example quality evaluation."""
    # High quality code examples
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Examples

```python
# Example 1: Complete and executable
def example1():
    return "complete"
```

```javascript
// Example 2: Language specified
function example2() {
    return "complete";
}
```

```python
# Example 3: Substantial code
class Example3:
    def __init__(self):
        self.value = "substantial"

    def method(self):
        return self.value
```

```python
# Example 4: Another substantial example
def example4(param: str) -> str:
    '''Complete function with type hints.'''
    return param.upper()
```

```python
# Example 5: Multiple lines
def example5():
    lines = ["line1", "line2", "line3", "line4"]
    for line in lines:
        print(line)
    return "done"
```
    """
    frontmatter, body = parse_skill_content(content)
    metrics, issues, strengths = evaluate_code_examples(body)

    assert metrics["code_examples_count"] >= 5
    assert metrics["code_examples_quality"] > 0.7
    assert any("language" in s for s in strengths)
    assert any("substantial" in s for s in strengths)


def test_code_examples_with_placeholders_low_quality() -> None:
    """Test that code examples with placeholders get low quality score."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

    ## Examples
    
    ```
    # Placeholder code
    def example1():
        pass  # TODO: implement
    ```
    
    ```
    def example2():
        raise NotImplementedError()
    ```
    
    ```
    # TODO: add implementation
    def example3():
        ...
    ```
    
    ```
    # Incomplete
    def example4():
        # ...
        pass
    ```

"""
    frontmatter, body = parse_skill_content(content)
    metrics, issues, strengths = evaluate_code_examples(body)

    assert metrics["code_examples_count"] >= 4
    assert metrics["code_examples_quality"] < 0.7  # Lower quality due to placeholders
    assert any("placeholder" in i for i in issues)


def test_patterns_with_good_bad_contrast() -> None:
    """Test pattern evaluation with good/bad examples."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Core Patterns

### Pattern 1
**Good Practice ✅**:
```python
def good_pattern():
    return "good"
```

**Anti-Pattern ❌**:
```python
def bad_pattern():
    return "bad"
```

**Key Insight**: Always use the good pattern, never the bad pattern.

### Pattern 2
**Production Pattern**:
```python
def production_pattern():
    return "production"
```

**Common Mistake**:
```python
def mistake_pattern():
    return "mistake"
```

**Key Insight**: Mistakes happen, but learn from them.
"""
    frontmatter, body = parse_skill_content(content)
    metrics, issues, strengths = evaluate_patterns(body)

    assert metrics["has_anti_patterns"] is True
    assert metrics["has_production_patterns"] is True
    assert metrics["has_key_insights"] is True
    assert metrics["pattern_count"] >= 2

    assert any("anti-pattern" in s for s in strengths)
    assert any("production pattern" in s for s in strengths)
    assert any("key insights" in s for s in strengths)


def test_patterns_missing_key_insights_generates_issue() -> None:
    """Test that patterns without key insights generate issues."""
    content = """---
name: test-skill
description: Test skill.
---
# Test

## When to Use This Skill
Testing.

## Core Patterns

### Pattern 1
```python
def pattern1():
    return "pattern1"
```

### Pattern 2
```python
def pattern2():
    return "pattern2"
```

### Pattern 3
```python
def pattern3():
    return "pattern3"
```
"""
    frontmatter, body = parse_skill_content(content)
    metrics, issues, strengths = evaluate_patterns(body)

    assert metrics["pattern_count"] >= 3
    assert metrics["has_key_insights"] is False

    assert any("key insights" in i.lower() for i in issues)
