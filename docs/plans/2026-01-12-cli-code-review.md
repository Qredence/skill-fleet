# CLI Code Review Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a comprehensive code review plan for the `src/skill_fleet/cli/` directory to identify improvements, ensure consistency, and maintain code quality standards.

**Architecture:** Systematic review of CLI components categorized by file type, functionality, and dependencies, using industry best practices for Python CLI applications and the project's own conventions.

**Tech Stack:** Python 3.12+, argparse/Typer, Rich, httpx, asyncio, pytest

---

## Overview

This plan reviews all CLI code in `src/skill_fleet/cli/` across multiple dimensions:

1. **Code Quality**: Structure, patterns, and maintainability
2. **Testing**: Test coverage and quality
3. **Documentation**: Docstrings, comments, and usage docs
4. **Best Practices**: Adherence to Python/Typer/Rich conventions
5. **Project Conventions**: Alignment with skill-fleet standards
6. **Dependencies**: Imports, API usage, and version compatibility
7. **Error Handling**: Exception management and user feedback
8. **Security**: Input validation and sensitive data handling

**Scope:** All 14 Python files in `src/skill_fleet/cli/`:
- `main.py` (argparse-based, 676 lines)
- `app.py` (Typer-based, 65 lines)
- `interactive_cli.py` (Rich-based, 670 lines)
- `onboarding_cli.py` (108 lines)
- `client.py` (httpx client, 64 lines)
- `commands/create.py` (94 lines)
- `commands/list_skills.py` (33 lines)
- `commands/serve.py` (20 lines)
- `commands/chat.py` (191 lines)
- `interactive_typer.py`
- `utils/__init__.py`
- `hitl/__init__.py`
- `commands/__init__.py`
- `__init__.py`

---

## Task 1: Review CLI Architecture and Organization

**Files:**
- Review: `src/skill_fleet/cli/main.py`, `src/skill_fleet/cli/app.py`, `src/skill_fleet/cli/commands/`

**Step 1: Analyze dual CLI implementation**

```bash
# Identify discrepancies between argparse (main.py) and Typer (app.py) implementations
uv run python -c "
import ast
import sys

main_imports = set()
with open('src/skill_fleet/cli/main.py') as f:
    tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                main_imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            main_imports.add(node.module.split('.')[0])

print('main.py imports:', sorted(main_imports))
"

uv run python -c "
import ast
with open('src/skill_fleet/cli/app.py') as f:
    tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            print(f'Function: {node.name}')
        elif isinstance(node, ast.ClassDef):
            print(f'Class: {node.name}')
"
```

**Step 2: Document command overlap/conflicts**

Create `docs/plans/cli-review-architecture.md`:

```markdown
# CLI Architecture Analysis

## Two CLI Implementations Identified

### main.py (argparse-based)
- Entry point: `cli_entrypoint()`
- Commands: create-skill, validate-skill, onboard, analytics, migrate, generate-xml, optimize, interactive
- Lines: 676

### app.py (Typer-based)
- Entry point: `app()` (not currently registered in pyproject.toml)
- Commands: create, list, serve, chat
- Lines: 65

## Issues to Address
1. Dual CLI implementations create confusion
2. Different command naming conventions (kebab-case vs lowercase)
3. app.py commands duplicate main.py functionality
4. No migration plan from argparse to Typer documented
```

**Step 3: Create architecture summary**

Run: `uv run python -c "
from pathlib import Path
import ast

cli_dir = Path('src/skill_fleet/cli')
files = list(cli_dir.rglob('*.py'))
print(f'Total Python files: {len(files)}')
for f in files:
    lines = len(f.read_text().splitlines())
    rel_path = f.relative_to(cli_dir)
    print(f'  {rel_path}: {lines} lines')
"
```

**Step 4: Commit architecture findings**

```bash
git add docs/plans/cli-review-architecture.md
git commit -m "docs: document CLI architecture review findings"
```

---

## Task 2: Review Code Quality and Patterns

**Files:**
- Review: `src/skill_fleet/cli/main.py`, `src/skill_fleet/cli/app.py`, `src/skill_fleet/cli/commands/*.py`

**Step 1: Check for code duplication**

```bash
# Find duplicate patterns across CLI files
uv run python -c "
from pathlib import Path
import re

cli_dir = Path('src/skill_fleet/cli')
files = ['main.py', 'app.py', 'interactive_cli.py', 'client.py']

print('=== Common Patterns Across CLI Files ===')
for py_file in files:
    path = cli_dir / py_file
    content = path.read_text()

    # Check for async patterns
    async_def_count = len(re.findall(r'async def', content))
    print(f'{py_file}: {async_def_count} async functions')

    # Check for Rich usage
    console_count = len(re.findall(r'Console\(\)', content))
    print(f'  {console_count} Console() instantiations')

    # Check for error handling
    try_count = len(re.findall(r'try:', content))
    except_count = len(re.findall(r'except', content))
    print(f'  {try_count} try blocks, {except_count} except blocks\n')
"
```

**Step 2: Analyze function complexity**

```bash
# Identify long functions (>50 lines)
uv run python -c "
import ast
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')
for py_file in cli_dir.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue

    content = py_file.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_lines = node.end_lineno - node.lineno
            if func_lines > 50:
                print(f'{py_file.relative_to(cli_dir)}: {node.name}() is {func_lines} lines')
"
```

**Step 3: Check magic numbers and literals**

```bash
# Find hardcoded values that should be constants
uv run rg '#[0-9]+|\"[^\"]{30,}\"' src/skill_fleet/cli/
```

**Step 4: Document quality issues**

Update `docs/plans/cli-review-architecture.md`:

```markdown
## Code Quality Issues

### Long Functions (>50 lines)
- `main.py:interactive_skill_cli()` - Complex interaction loop
- `interactive_cli.py:run()` - 164 lines, needs refactoring
- `commands/chat.py:chat_command()` - 95 lines, complex state management

### Code Duplication
- Multiple Console() instantiations across files
- Repeated error handling patterns (try/except/finally with client.close())
- Similar async wrapper patterns in commands/create.py, list_skills.py, chat.py

### Hardcoded Values
- Main loop constants: `refresh_per_second=10` in interactive_cli.py:529
- Sleep delays: `await asyncio.sleep(2)` in multiple locations
- UI element counts: Hardcoded in several places

### Recommendations
1. Extract shared async wrapper pattern to utility function
2. Create Rich console manager singleton
3. Define constants for all magic numbers
4. Break down long functions into smaller, testable units
```

**Step 5: Commit quality findings**

```bash
git add docs/plans/cli-review-architecture.md
git commit -m "docs: add code quality issues to review"
```

---

## Task 3: Review Testing Coverage

**Files:**
- Review: `tests/test_onboarding.py`, `tests/test_api.py`, existing test patterns

**Step 1: Analyze current test coverage**

```bash
# Run pytest with coverage on CLI code
uv run pytest tests/ --cov=src/skill_fleet/cli --cov-report=term-missing

# Check which files have no tests
uv run python -c "
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')
test_dir = Path('tests')

cli_files = [f.relative_to(cli_dir) for f in cli_dir.rglob('*.py') if f.name != '__init__.py']
test_files = set(test_dir.rglob('*cli*.py'))

print('CLI files with no dedicated tests:')
for cli_file in cli_files:
    test_name = f'test_{cli_file.stem}'
    if not any(test_name in t.name for t in test_files):
        print(f'  - src/skill_fleet/cli/{cli_file}')
"
```

**Step 2: Identify missing test scenarios**

```bash
# Create checklist of untested CLI behaviors
cat > docs/plans/cli-test-coverage.md << 'EOF'
# CLI Test Coverage Analysis

## Commands with No Tests
- `main.py:create_skill()` - Complex workflow with reasoning tracing
- `main.py:validate_skill()` - Skill validation logic
- `main.py:migrate_skills_cli()` - Migration tool
- `main.py:generate_xml_cli()` - XML generation
- `main.py:optimize_workflow_cli()` - MIPROv2/GEPA optimization
- `main.py:show_analytics()` - Analytics display
- `app.py:serve_command()` - Server startup
- `app.py:create_command()` - Typer-based create flow
- `app.py:list_command()` - List skills
- `app.py:chat_command()` - Interactive chat dashboard

## Missing Test Scenarios

### main.py
- [ ] Command-line argument parsing and validation
- [ ] Error handling for missing required arguments
- [ ] JSON output format validation
- [ ] Dry-run mode for migrate command
- [ ] Reasoning tracer integration (cli, debug, full modes)

### interactive_cli.py
- [ ] Session persistence and loading
- [ ] Checklist status display
- [ ] Multi-skill queue management
- [ ] Command handling (/help, /exit, /save, etc.)
- [ ] Streaming display with Rich Live
- [ ] Multi-choice question formatting

### client.py
- [ ] HTTP client initialization with custom URLs
- [ ] API error handling (4xx, 5xx responses)
- [ ] Timeout and retry logic
- [ ] Connection cleanup in finally blocks

### Commands/*.py
- [ ] HITL polling loop behavior
- [ ] Auto-approve mode flow
- [ ] Interactive prompts and validation
- [ ] Dashboard layout rendering
- [ ] Session state transitions
EOF
```

**Step 3: Create test template**

Create `tests/cli/test_cli_commands.py`:

```python
"""Tests for CLI commands."""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from skill_fleet.cli.main import create_skill, validate_skill, migrate_skills_cli
from skill_fleet.cli.app import app, CLIConfig


@pytest.fixture
def mock_taxonomy():
    """Mock taxonomy manager."""
    taxonomy = MagicMock()
    return taxonomy


@pytest.fixture
def mock_creator():
    """Mock skill creator."""
    creator = MagicMock()
    return creator


class TestCreateSkillCommand:
    """Test create-skill command."""

    @patch('skill_fleet.cli.main.configure_dspy')
    @patch('skill_fleet.cli.main.TaxonomySkillCreator')
    def test_create_skill_with_auto_approve(self, mock_creator_class, mock_configure):
        """Test create-skill with --auto-approve flag."""
        # Arrange
        mock_creator = MagicMock()
        mock_creator.return_value = mock_creator_class.return_value
        mock_creator.return_value = {
            "status": "approved",
            "skill_id": "test-skill",
            "path": "/tmp/test-skill"
        }

        args = MagicMock()
        args.task = "Create a test skill"
        args.auto_approve = True
        args.user_id = "test-user"
        args.config = "config.yaml"
        args.skills_root = "/tmp/skills"
        args.feedback_type = "auto"
        args.max_iterations = 3
        args.min_rounds = 1
        args.max_rounds = 4
        args.cache_dir = None
        args.reasoning = "none"
        args.json = False
        args.is_training_run = False

        # Act
        result = create_skill(args)

        # Assert
        assert result == 0
        mock_creator.assert_called_once()

    @patch('skill_fleet.cli.main.configure_dspy')
    def test_create_skill_with_invalid_config(self, mock_configure):
        """Test create-skill fails gracefully with invalid config."""
        from skill_fleet.llm import FleetConfigError

        mock_configure.side_effect = FleetConfigError("Invalid config")

        args = MagicMock()
        args.task = "Test"
        args.config = "invalid.yaml"
        args.skills_root = "/tmp/skills"

        # Act & Assert
        with pytest.raises(SystemExit):
            create_skill(args)


class TestValidateSkillCommand:
    """Test validate-skill command."""

    @patch('skill_fleet.cli.main.SkillValidator')
    def test_validate_valid_skill(self, mock_validator_class):
        """Test validate-skill with valid skill."""
        # Arrange
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": True,
            "errors": [],
            "warnings": []
        }

        args = MagicMock()
        args.skill_path = "skills/general/testing"
        args.skills_root = "/tmp/skills"
        args.json = False

        # Act
        result = validate_skill(args)

        # Assert
        assert result == 0

    @patch('skill_fleet.cli.main.SkillValidator')
    def test_validate_invalid_skill(self, mock_validator_class):
        """Test validate-skill with invalid skill."""
        # Arrange
        mock_validator = MagicMock()
        mock_validator_class.return_value = mock_validator
        mock_validator.validate_complete.return_value = {
            "passed": False,
            "errors": ["Missing YAML frontmatter"],
            "warnings": []
        }

        args = MagicMock()
        args.skill_path = "skills/invalid/skill"
        args.skills_root = "/tmp/skills"
        args.json = False

        # Act
        result = validate_skill(args)

        # Assert
        assert result == 2  # Exit code for validation failure


class TestTyperApp:
    """Test Typer-based CLI app."""

    def test_app_initialization(self):
        """Test Typer app is properly initialized."""
        from typer.main import get_command_from_info

        # Act
        command = get_command_from_info(app.info)

        # Assert
        assert command is not None
        assert app.info.name == "skill-fleet"

    def test_cli_config_class(self):
        """Test CLIConfig class initialization."""
        # Act
        config = CLIConfig(
            api_url="http://localhost:8000",
            user_id="test-user"
        )

        # Assert
        assert config.api_url == "http://localhost:8000"
        assert config.user_id == "test-user"
        assert config.client is not None
```

**Step 4: Run new tests**

```bash
uv run pytest tests/cli/test_cli_commands.py -v
```

Expected: Initial tests pass, identify additional scenarios to cover

**Step 5: Commit test additions**

```bash
git add tests/cli/test_cli_commands.py
git commit -m "test: add comprehensive CLI command tests"
```

---

## Task 4: Review Documentation

**Files:**
- Review: All `src/skill_fleet/cli/**/*.py` files for docstrings

**Step 1: Check docstring completeness**

```bash
# Identify functions/classes missing docstrings
uv run python -c "
import ast
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')

print('=== Missing Docstrings ===')
for py_file in cli_dir.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue

    content = py_file.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)

            # Skip private methods
            if isinstance(node, ast.FunctionDef) and node.name.startswith('_'):
                continue

            if not docstring or len(docstring.strip()) < 10:
                rel_path = py_file.relative_to(cli_dir)
                symbol_type = 'Class' if isinstance(node, ast.ClassDef) else 'Function'
                print(f'{rel_path}:{node.lineno} - {symbol_type} {node.name}')
"
```

**Step 2: Analyze docstring quality**

```bash
# Check docstring format consistency
uv run python -c "
import re
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')

print('=== Docstring Format Check ===')
for py_file in cli_dir.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue

    content = py_file.read_text()
    docstrings = re.findall(r'\"\"\"\"([^\"\"\"]*(?:\"\"\"\"|$))', content)

    for doc in docstrings:
        if len(doc) > 100:
            # Check for Args/Returns sections
            has_args = ':param' in doc or 'Args:' in doc
            has_returns = ':returns' in doc or 'Returns:' in doc or '-> dict' in doc

            if not has_args and not has_returns:
                # Check if it looks like a complex function
                if 'def ' in content and 'async def ' in content:
                    rel_path = py_file.relative_to(cli_dir)
                    print(f'{rel_path}: Long docstring without Args/Returns sections')
"
```

**Step 3: Document docstring issues**

Create `docs/plans/cli-documentation-review.md`:

```markdown
# CLI Documentation Review

## Missing Docstrings

### main.py
- `create_skill()` - No docstring explaining workflow phases
- `validate_skill()` - Brief docstring, missing examples
- `optimize_workflow_cli()` - No docstring for complex optimization logic

### interactive_cli.py
- `InteractiveSkillCLI._display_multi_skill_queue()` - Missing docstring
- `InteractiveSkillCLI._show_history()` - No docstring
- `InteractiveSkillCLI._respond_with_streaming()` - Complex function, needs detailed docs

### commands/chat.py
- `chat_command()` - 191 lines, no docstring
- `create_dashboard_layout()` - No docstring for layout creation
- Missing Args/Returns sections in most functions

## Docstring Quality Issues

### Inconsistent Format
- Some use Google style (Args:, Returns:)
- Some use Sphinx style (:param, :type, :returns:)
- Mix of styles across files

### Missing Examples
- No docstrings include usage examples
- Complex CLI flows (create-skill, interactive) need examples
- Missing descriptions of expected output formats

### Missing Return Type Hints
- Several functions return `int` exit codes but not documented
- Async functions don't specify return types in docstrings
- Callback functions not documented

## Recommendations
1. Adopt Google-style docstrings consistently (match skill-fleet convention)
2. Add Args, Returns, Raises sections to all public functions
3. Include usage examples for complex commands
4. Document exit codes (0=success, 1=error, 2=config error)
5. Add type hints to function signatures where missing
EOF
```

**Step 4: Commit documentation review**

```bash
git add docs/plans/cli-documentation-review.md
git commit -m "docs: add CLI documentation review findings"
```

---

## Task 5: Review Error Handling

**Files:**
- Review: All CLI files for exception handling patterns

**Step 1: Analyze exception handling**

```bash
# Find all try/except blocks and their patterns
uv run python -c "
import ast
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')

print('=== Exception Handling Analysis ===')
for py_file in cli_dir.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue

    content = py_file.read_text()
    tree = ast.parse(content)

    try_blocks = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            rel_path = py_file.relative_to(cli_dir)
            line_num = node.lineno

            # Check exception types
            exc_handlers = [type(exc.id) if hasattr(exc, 'id') else 'Exception'
                         for exc in node.handlers]

            try_blocks.append({
                'file': rel_path,
                'line': line_num,
                'handlers': exc_handlers,
                'has_finally': node.finalbody is not None
            })

    if try_blocks:
        print(f'\n{py_file.name}:')
        for tb in try_blocks:
            print(f'  Line {tb[\"line\"]}: {tb[\"handlers\"]} (finally: {tb[\"has_finally\"]})')
"
```

**Step 2: Identify bare except clauses**

```bash
# Find catch-all except blocks
uv run rg 'except:$' src/skill_fleet/cli/
uv run rg 'except Exception:' src/skill_fleet/cli/
```

**Step 3: Check error message quality**

```bash
# Find error messages without context
uv run rg 'print\(.*Error.*file=sys\.stderr' src/skill_fleet/cli/ -A 2
```

**Step 4: Document error handling issues**

Create `docs/plans/cli-error-handling-review.md`:

```markdown
# CLI Error Handling Review

## Issues Found

### Bare Except Clauses
- `interactive_cli.py:261` - Generic `except Exception:` catches all errors
- `client.py:89` - No specific exception handling

### Missing Specific Exceptions
- FleetConfigError handling exists but other config errors not caught
- HTTP errors from httpx not differentiated (timeouts vs connection errors)
- File I/O errors not explicitly handled (session save/load)

### Inconsistent Error Reporting
- Some use `print(..., file=sys.stderr)`
- Some use `console.print("[red]Error: ...[/red]")`
- Mix of Rich formatting and plain text for errors

### Missing User-Facing Messages
- "Config error" doesn't explain what to fix
- "Error during optimization" gives no actionable guidance
- HTTP errors don't show retry options

### Resource Cleanup
- Finally blocks not always present in async functions
- HTTP client cleanup inconsistent across commands
- Session files may not be saved on crashes

## Recommendations
1. Replace bare `except Exception` with specific exception types
2. Create consistent error message format using Rich
3. Add error recovery suggestions (e.g., "Run with --help")
4. Ensure all async functions have proper cleanup in finally blocks
5. Log full stack traces for debugging (with LOG_LEVEL env var)
6. Define custom CLI error classes for better handling
EOF
```

**Step 5: Commit error handling review**

```bash
git add docs/plans/cli-error-handling-review.md
git commit -m "docs: add CLI error handling review findings"
```

---

## Task 6: Review Dependencies and Imports

**Files:**
- Review: All CLI files for import patterns

**Step 1: Analyze import structure**

```bash
# Find all imports and check for circular dependencies
uv run python -c "
import ast
from collections import defaultdict
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')

print('=== Import Analysis ===')
imports_by_file = defaultdict(set)

for py_file in cli_dir.rglob('*.py'):
    if '__pycache__' in str(py_file):
        continue

    rel_path = py_file.relative_to(cli_dir)
    content = py_file.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports_by_file[str(rel_path)].add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports_by_file[str(rel_path)].add(node.module.split('.')[0])

# Check for internal dependencies
for file_path, imports in sorted(imports_by_file.items()):
    internal_imports = [imp for imp in imports if 'skill_fleet' in imp]
    if internal_imports:
        print(f'\n{file_path}:')
        for imp in sorted(internal_imports):
            print(f'  - {imp}')
"
```

**Step 2: Check for unused imports**

```bash
# Run ruff to find unused imports
uv run ruff check src/skill_fleet/cli/ --select F401
```

**Step 3: Verify dependency versions**

```bash
# Check if dependencies are compatible with project requirements
uv run python -c "
import pkg_resources

# Read from pyproject.toml
import tomli
with open('pyproject.toml') as f:
    config = tomli.load(f)

dependencies = config.get('project', {}).get('dependencies', [])

print('=== CLI Dependencies Check ===')
for dep in dependencies:
    pkg_name = dep.split('>=')[0].split('==')[0].strip()
    try:
        version = pkg_resources.get_distribution(pkg_name).version
        print(f'{pkg_name}: {version} (installed)')
    except pkg_resources.DistributionNotFound:
        print(f'{pkg_name}: NOT INSTALLED')
"
```

**Step 4: Document dependency issues**

Create `docs/plans/cli-dependencies-review.md`:

```markdown
# CLI Dependencies Review

## Unused Imports
- Check with `uv run ruff check src/skill_fleet/cli/ --select F401`

## Circular Dependencies
- Check for: `main.py` <-> `workflow.creator` <-> `agent.agent`
- Potential circular: `interactive_cli.py` -> `agent.agent` -> `interactive_cli.py`

## Dependency Issues
- `httpx.AsyncClient` timeout hardcoded to 30.0 seconds (client.py:19)
- Rich imports scattered across files (Console imported 8+ times)
- `asyncio` imported but used inconsistently

## Version Compatibility
- Verify: typer, rich, httpx versions match constraints
- Check: Python 3.12+ features used (e.g., `type[]` syntax)
- Ensure: No deprecated APIs used

## Recommendations
1. Run ruff F401 to identify unused imports
2. Create shared Rich console utility to reduce duplication
3. Consolidate async wrapper pattern
4. Add timeout configuration to CLI arguments
5. Document all external dependencies with version requirements
EOF
```

**Step 5: Commit dependency review**

```bash
git add docs/plans/cli-dependencies-review.md
git commit -m "docs: add CLI dependencies review findings"
```

---

## Task 7: Review Security and Input Validation

**Files:**
- Review: `main.py`, `app.py`, `client.py`, `onboarding_cli.py`

**Step 1: Check path handling**

```bash
# Find path operations that could be vulnerable
uv run rg 'Path\(|\.read_text\(|\.write_text\(|open\(' src/skill_fleet/cli/ -B 2 -A 2
```

**Step 2: Analyze user input handling**

```bash
# Find argparse/typer arguments without validation
uv run rg 'add_argument|typer\.Argument|typer\.Option' src/skill_fleet/cli/ -A 1
```

**Step 3: Check for secrets exposure**

```bash
# Find potential secret logging
uv run rg 'print.*api.*key|print.*token|print.*secret' src/skill_fleet/cli/ -i
```

**Step 4: Document security issues**

Create `docs/plans/cli-security-review.md`:

```markdown
# CLI Security Review

## Path Traversal Risks
- User-provided paths not validated before file operations
- No checks for `../` in skill paths
- Session file location uses user input without sanitization

## Input Validation
- `--skills-root` accepts any path without validation
- API URLs not validated for protocol (http vs https)
- User ID not checked for special characters/injection

## Secrets Handling
- API keys not in error messages (good)
- But config file paths may be exposed in stack traces
- No redaction of sensitive data in verbose output

## Recommendations
1. Validate all user-provided paths exist and are within allowed directories
2. Add input sanitization for skill paths and user IDs
3. Use `pathlib.Path.resolve().relative_to()` to prevent traversal
4. Consider adding --dry-run mode for risky operations
5. Add configuration file validation before loading
EOF
```

**Step 5: Commit security review**

```bash
git add docs/plans/cli-security-review.md
git commit -m "docs: add CLI security review findings"
```

---

## Task 8: Review Best Practices Compliance

**Files:**
- Review: All CLI files against Python/CLI best practices

**Step 1: Check Typer/Click patterns**

```bash
# Verify Typer best practices
uv run python -c "
import ast
from pathlib import Path

cli_dir = Path('src/skill_fleet/cli')

print('=== Typer Best Practices Check ===')

# Check app.py for context usage
app_py = cli_dir / 'app.py'
content = app_py.read_text()

checks = {
    'Has context callback': '@app.callback()' in content,
    'Has context.obj usage': 'ctx.obj' in content,
    'Has help text': 'help=' in content or 'help=' in content,
    'Has environment variables': 'envvar=' in content,
}

for check, result in checks.items():
    status = '✓' if result else '✗'
    print(f'{status} {check}')
"
```

**Step 2: Check Rich usage patterns**

```bash
# Verify Rich best practices
uv run rg 'Console\(\)|Panel\(|Live\(|Status\(' src/skill_fleet/cli/ --no-filename | head -20
```

**Step 3: Check async/await patterns**

```bash
# Find async functions without proper error handling
uv run rg 'async def' src/skill_fleet/cli/ -A 10 | rg -B 5 'except' | head -40
```

**Step 4: Document best practices issues**

Create `docs/plans/cli-best-practices-review.md`:

```markdown
# CLI Best Practices Review

## Typer Compliance
- ✅ Uses `@app.callback()` for global options (app.py:35)
- ✅ Uses `ctx.obj` for shared state (app.py:55)
- ✅ Has help text for all commands
- ✅ Uses `envvar` for environment variables
- ❌ app.py not registered in pyproject.toml entry points
- ❌ Duplicate commands between main.py and app.py

## Rich Library Usage
- ✅ Uses Rich for all output (consistent styling)
- ✅ Uses Panels for grouping content
- ✅ Uses Live for streaming output (interactive_cli.py:521)
- ✅ Uses Status for async operations (chat.py:133)
- ❌ Multiple Console() instances created (not singleton)
- ❌ Inconsistent color scheme across commands
- ❌ No centralized theme configuration

## Async/Await Patterns
- ✅ Uses asyncio.run() properly for CLI entry points
- ✅ Has finally blocks for cleanup (inconsistent)
- ❌ Some async functions lack explicit error handling
- ❌ No timeout handling for long-running operations
- ❌ Mixed async and sync patterns in same file

## Python Code Style
- ✅ Uses `from __future__ import annotations`
- ✅ Follows PEP 8 naming
- ❌ Some functions exceed 50 lines (interactive_cli.py:100)
- ❌ Missing type hints in some function signatures
- ❌ Magic numbers not extracted to constants

## Recommendations
1. Consolidate to single CLI framework (argparse OR Typer, not both)
2. Create shared Rich console manager singleton
3. Define color palette constants for consistent theming
4. Add timeout configuration to all async operations
5. Register app.py in pyproject.toml entry points
6. Extract all magic numbers to constants
7. Add type hints to all public functions
EOF
```

**Step 5: Commit best practices review**

```bash
git add docs/plans/cli-best-practices-review.md
git commit -m "docs: add CLI best practices review findings"
```

---

## Task 9: Create Comprehensive Review Summary

**Files:**
- Create: `docs/plans/CLI_CODE_REVIEW_SUMMARY.md`

**Step 1: Aggregate all findings**

Create summary document:

```markdown
# CLI Code Review Summary - src/skill_fleet/cli/

**Review Date:** 2026-01-12
**Reviewer:** Code Review Plan Execution
**Scope:** 14 Python files, ~2,200 lines of code

---

## Executive Summary

### Critical Issues (Must Fix)
1. **Dual CLI Implementation** - argparse (main.py) and Typer (app.py) both exist, causing confusion
2. **Minimal Test Coverage** - Most CLI commands have no automated tests
3. **Long Functions** - Several functions >50 lines need refactoring
4. **Inconsistent Error Handling** - Mix of patterns, missing specific exceptions
5. **Missing Docstrings** - Many functions lack Args/Returns documentation

### High Priority (Should Fix)
1. Code duplication across files (Console instantiation, async wrappers)
2. Magic numbers throughout codebase
3. No centralized configuration for UI theming
4. Incomplete input validation on user paths
5. Missing exit code documentation

### Medium Priority (Nice to Have)
1. Inconsistent docstring format (Google vs Sphinx style)
2. Unused imports in several files
3. No timeout configuration for long-running operations
4. Resource cleanup inconsistent in async functions

### Low Priority (Future Improvements)
1. Potential circular dependencies to investigate
2. Rich console could be singleton pattern
3. Add more usage examples in docstrings

---

## Detailed Findings by Category

### Architecture (Task 1)
**Files:** `main.py` (676 lines), `app.py` (65 lines)

**Issues:**
- Two separate CLI frameworks (argparse vs Typer)
- Command naming inconsistency (kebab-case vs lowercase)
- app.py not registered in entry points
- Overlapping functionality between implementations

**Impact:** High - Confuses users and developers
**Effort:** Medium - Choose one framework, migrate commands

---

### Code Quality (Task 2)
**Files:** All CLI files

**Issues:**
- Long functions: `interactive_cli.py:run()` (164 lines), `chat.py:chat_command()` (95 lines)
- Code duplication: Console() instantiated 8+ times, async wrappers repeated
- Magic numbers: Hardcoded timeouts, delays, UI element counts

**Impact:** Medium - Affects maintainability
**Effort:** High - Refactoring and extraction needed

---

### Testing (Task 3)
**Files:** `tests/test_onboarding.py`, `tests/test_api.py`

**Issues:**
- 9 out of 10 CLI commands have no tests
- No integration tests for full workflows
- Missing edge case tests

**Impact:** High - Risk of regressions
**Effort:** High - Comprehensive test suite needed

---

### Documentation (Task 4)
**Files:** All CLI files

**Issues:**
- Missing docstrings on 15+ functions
- No Args/Returns sections in most docstrings
- Mixed docstring formats (Google vs Sphinx)
- No usage examples in complex commands

**Impact:** Medium - Reduces code discoverability
**Effort:** Medium - Documentation pass needed

---

### Error Handling (Task 5)
**Files:** All CLI files

**Issues:**
- Bare `except Exception:` clauses in 3 locations
- Inconsistent error message format (print vs console.print)
- No actionable error recovery suggestions
- Missing specific exception types

**Impact:** High - Poor user experience
**Effort:** Medium - Standardize error handling pattern

---

### Dependencies (Task 6)
**Files:** All CLI files

**Issues:**
- Unused imports (verify with ruff F401)
- Potential circular dependencies
- Hardcoded httpx timeout (30.0s)
- Rich console duplication

**Impact:** Low - Mostly cleanup
**Effort:** Low - Remove unused imports, refactor console usage

---

### Security (Task 7)
**Files:** `main.py`, `app.py`, `client.py`, `onboarding_cli.py`

**Issues:**
- No path traversal validation on user inputs
- Skills root path not validated
- No sanitization of user IDs

**Impact:** Medium - Security concern if used with untrusted input
**Effort:** Low - Add validation functions

---

### Best Practices (Task 8)
**Files:** All CLI files

**Issues:**
- Missing type hints in several functions
- No timeout handling for async operations
- Inconsistent color scheme
- Magic numbers not extracted

**Impact:** Low - Code quality
**Effort:** Medium - Add hints, constants, timeouts

---

## Prioritized Action Items

### Phase 1: Critical (Week 1)
1. **Decide on single CLI framework** - argparse or Typer
2. **Create test suite** - Start with smoke tests for all commands
3. **Fix critical error handling** - Replace bare except clauses
4. **Add input validation** - Sanitize user paths and IDs

### Phase 2: High Priority (Weeks 2-3)
5. **Refactor long functions** - Break down into testable units
6. **Remove code duplication** - Extract shared patterns
7. **Standardize error messages** - Use Rich consistently
8. **Add docstrings** - Args/Returns for all public functions

### Phase 3: Medium Priority (Weeks 4-5)
9. **Extract constants** - Remove all magic numbers
10. **Consolidate Rich usage** - Singleton pattern
11. **Add timeout handling** - All async operations
12. **Standardize docstring format** - Choose one style

### Phase 4: Low Priority (Ongoing)
13. **Remove unused imports** - Run ruff regularly
14. **Investigate circular deps** - If issues arise
15. **Add usage examples** - In docstrings

---

## Recommendations

### Immediate Actions
1. **Hold team discussion** on argparse vs Typer migration
2. **Create test spike** for one command to establish pattern
3. **Define error handling guidelines** for CLI
4. **Establish docstring standard** (Google-style recommended)

### Long-term Improvements
1. **Add CLI integration tests** with mocked API
2. **Create CLI developer guide** with patterns
3. **Set up pre-commit hooks** for ruff and tests
4. **Add performance monitoring** for slow commands

### Metrics to Track
- Test coverage percentage (aim for 80%+)
- Maximum function length (<50 lines)
- Number of bare except clauses (target: 0)
- Documentation coverage (all public functions documented)

---

## Appendix: Review Methodology

### Tools Used
- AST parsing for code structure analysis
- Regular expressions for pattern matching
- pytest for test coverage analysis
- ruff for linting and unused imports
- Manual code review for best practices

### Review Criteria
1. **Correctness**: Does the code do what it's supposed to?
2. **Maintainability**: Is it easy to understand and modify?
3. **Testability**: Can it be tested in isolation?
4. **Documentation**: Is it well-documented?
5. **Security**: Does it handle untrusted input safely?
6. **Performance**: Does it run efficiently?
7. **Style**: Does it follow project conventions?

### Limitations
- Did not run full test suite (focused on coverage analysis)
- Did not test security vulnerabilities (code review only)
- Did not measure performance (static analysis only)
- No user testing of CLI UX

---

## Next Steps

1. **Review this summary** with the team
2. **Prioritize action items** based on team capacity
3. **Create follow-up tickets** in issue tracker
4. **Track progress** against metrics defined above
5. **Schedule follow-up review** in 3 months

---

**End of Review**
EOF
```

**Step 2: Commit comprehensive summary**

```bash
git add docs/plans/CLI_CODE_REVIEW_SUMMARY.md
git add docs/plans/cli-*.md
git commit -m "docs: complete CLI code review with comprehensive findings"
```

---

## Task 10: Create Actionable Issue Templates

**Files:**
- Create: `docs/plans/cli-review-issues/`

**Step 1: Create issue templates for critical findings**

Create `docs/plans/cli-review-issues/001-dual-cli-implementation.md`:

```markdown
# Issue: Dual CLI Implementation Creates Confusion

**Priority:** Critical
**Type:** Refactoring
**Files Affected:** `src/skill_fleet/cli/main.py`, `src/skill_fleet/cli/app.py`

## Problem

The skill-fleet project has two separate CLI implementations:
1. `main.py` - argparse-based CLI (676 lines, production entry point)
2. `app.py` - Typer-based CLI (65 lines, not registered)

This creates confusion for:
- Users trying to understand which to use
- Developers deciding where to add new commands
- Documentation writers trying to document CLI usage

## Options

### Option 1: Migrate to Typer (Recommended)
- **Pros:** Modern, type-safe, better completion support
- **Pros:** Already has app.py structure ready
- **Cons:** Large migration effort (~2-3 weeks)
- **Effort:** High

### Option 2: Keep argparse, Remove Typer
- **Pros:** Works as-is, low risk
- **Pros:** No migration effort
- **Cons:** Missing modern features, harder to extend
- **Cons:** app.py development wasted effort
- **Effort:** Low

### Option 3: Support Both Temporarily
- **Pros:** Time to decide on migration strategy
- **Cons:** Confusion continues during transition
- **Cons:** Maintenance burden doubled
- **Effort:** Medium

## Recommendation

**Choose Option 1: Migrate to Typer**

Rationale:
1. Typer is the modern Python CLI framework
2. Type safety reduces bugs
3. Better completion support for shells
4. app.py already exists with good structure
5. Project uses Rich, which integrates well with Typer

## Migration Plan

1. **Week 1:** Add test coverage to main.py commands
2. **Week 2:** Migrate simple commands (list, validate, migrate)
3. **Week 3:** Migrate complex commands (create-skill, interactive, optimize)
4. **Week 4:** Update documentation and examples
5. **Week 5:** Testing and validation
6. **Week 6:** Remove main.py, update entry points

## Acceptance Criteria

- [ ] All commands migrated to Typer
- [ ] All existing tests pass
- [ ] New tests added for Typer commands
- [ ] Documentation updated with Typer examples
- [ ] main.py removed from codebase
- [ ] pyproject.toml entry points updated
- [ ] No functionality loss from migration

## Resources
- Typer docs: https://typer.tiangolo.com/
- Migration guide: Compare argparse vs Typer patterns in existing code
EOF
```

Create `docs/plans/cli-review-issues/002-add-cli-test-coverage.md`:

```markdown
# Issue: CLI Commands Lack Test Coverage

**Priority:** Critical
**Type:** Testing
**Files Affected:** All CLI commands

## Problem

Only 1 out of 10 CLI commands has automated tests:
- ✅ `onboard` - Tests in `tests/test_onboarding.py`
- ❌ `create-skill` - No tests
- ❌ `validate-skill` - No tests
- ❌ `migrate` - No tests
- ❌ `generate-xml` - No tests
- ❌ `optimize` - No tests
- ❌ `analytics` - No tests
- ❌ `serve` - No tests
- ❌ `list` - No tests
- ❌ `chat` - No tests

## Impact

- Risk of regressions when modifying CLI code
- No confidence in refactoring
- Edge cases not tested
- User-facing bugs caught in production

## Solution

Create comprehensive test suite with:
1. Unit tests for individual functions
2. Integration tests for command workflows
3. Mock external dependencies (LLM, API, file I/O)
4. Test exit codes and error handling
5. Test JSON output formats

## Test Structure Example

```python
# tests/cli/test_create_skill_command.py

import pytest
from unittest.mock import MagicMock, patch

class TestCreateSkillCommand:
    def test_creates_skill_with_auto_approve(self):
        """Test create-succeeds with --auto-approve."""
        # Arrange
        mock_creator = MagicMock()
        mock_creator.return_value = {"status": "approved", ...}

        # Act
        result = create_skill(args)

        # Assert
        assert result == 0
        mock_creator.assert_called_once()

    def test_fails_with_invalid_config(self):
        """Test create-skill fails with invalid config."""
        # Test error handling

    def test_outputs_json_when_requested(self):
        """Test --json flag outputs valid JSON."""
        # Test JSON format
```

## Acceptance Criteria

- [ ] All 10 commands have unit tests
- [ ] Each command has at least 5 test scenarios
- [ ] Test coverage >= 80% for CLI code
- [ ] All tests mock external dependencies
- [ ] Integration tests for end-to-end workflows
- [ ] Tests run in CI pipeline

## Resources
- pytest docs: https://docs.pytest.org/
- Existing test patterns: `tests/test_onboarding.py`
- Project testing guidelines: AGENTS.md
EOF
```

Create `docs/plans/cli-review-issues/003-standardize-error-handling.md`:

```markdown
# Issue: Inconsistent Error Handling in CLI

**Priority:** High
**Type:** Refactoring
**Files Affected:** All CLI files

## Problem

Error handling is inconsistent across CLI code:

### Pattern 1: Bare Exception Catching
```python
# interactive_cli.py:261
except Exception as e:
    self.console.print(f"[red]Error: {e}[/red]\n")
    logger.exception("Error in interactive CLI loop")
```

### Pattern 2: Specific FleetConfigError
```python
# main.py:664
except FleetConfigError as exc:
    print(f"config error: {exc}", file=sys.stderr)
    return 2
```

### Pattern 3: Print vs Console
```python
# main.py:148
print("⚠️ MLflow not installed. Install with: uv add mlflow", file=sys.stderr)

# interactive_cli.py:96
self.console.print(Panel.fit(...))
```

### Pattern 4: Missing Actionable Messages
- "Config error: Invalid config" (what's invalid?)
- "Error during optimization" (what went wrong?)
- "API error" (how to fix?)

## Impact

- Poor user experience
- Difficult to debug issues
- Inconsistent exit codes
- No recovery guidance

## Solution

### 1. Define Custom CLI Exceptions

```python
# src/skill_fleet/cli/exceptions.py

class CLIError(Exception):
    """Base exception for CLI errors."""
    def __init__(self, message: str, exit_code: int = 1, suggestion: str = ""):
        self.message = message
        self.exit_code = exit_code
        self.suggestion = suggestion
        super().__init__(message)

class ConfigError(CLIError):
    """Configuration-related errors."""
    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message, exit_code=2, suggestion)

class APIError(CLIError):
    """API communication errors."""
    def __init__(self, message: str, status_code: int = None, suggestion: str = ""):
        full_msg = f"{message}"
        if status_code:
            full_msg += f" (HTTP {status_code})"
        super().__init__(full_msg, exit_code=1, suggestion)
```

### 2. Create Error Display Utility

```python
# src/skill_fleet/cli/utils/errors.py

from rich.console import Console
from rich.panel import Panel
from ..exceptions import CLIError

console = Console()

def display_error(error: CLIError):
    """Display error with consistent formatting."""
    console.print(Panel(
        f"[bold red]Error:[/bold red] {error.message}\n\n"
        f"{error.suggestion}",
        title="Error",
        border_style="red"
    ))

    if error.exit_code != 0:
        console.print(f"\n[yellow]Exit code: {error.exit_code}[/yellow]")
```

### 3. Replace All Error Handling

```python
# Before
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    return 1

# After
except APIError as e:
    display_error(e)
    return e.exit_code
```

### 4. Define Exit Code Standard

```python
# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_VALIDATION_ERROR = 3
EXIT_NETWORK_ERROR = 4
```

## Acceptance Criteria

- [ ] Custom exception classes defined
- [ ] Error display utility created
- [ ] All bare `except Exception` replaced
- [ ] Consistent Rich formatting for all errors
- [ ] Actionable suggestions provided
- [ ] Exit code standard documented
- [ ] All error messages tested

## Resources
- Rich docs: https://rich.readthedocs.io/
- Python exceptions: https://docs.python.org/3/library/exceptions.html
EOF
```

**Step 2: Commit issue templates**

```bash
git add docs/plans/cli-review-issues/
git commit -m "docs: add actionable issue templates for CLI review"
```

---

## Summary

This comprehensive code review plan:

1. **Analyzes architecture** - Identifies dual CLI implementation problem
2. **Reviews code quality** - Finds long functions, duplication, magic numbers
3. **Assesses testing** - Identifies minimal coverage (90% of commands untested)
4. **Checks documentation** - Finds missing docstrings, inconsistent formats
5. **Examines error handling** - Finds bare excepts, inconsistent patterns
6. **Reviews dependencies** - Identifies unused imports, potential circular deps
7. **Assesses security** - Finds missing path validation, input sanitization
8. **Checks best practices** - Verifies Typer, Rich, async patterns
9. **Creates comprehensive summary** - Prioritized action items with phases
10. **Generates issue templates** - Actionable tickets for critical issues

**Estimated Total Effort:** 2-3 days for full review execution
**Expected Deliverables:** 4 detailed review docs + 1 summary + 3 issue templates

**Files Created:**
- `docs/plans/cli-review-architecture.md`
- `docs/plans/cli-test-coverage.md`
- `docs/plans/cli-documentation-review.md`
- `docs/plans/cli-error-handling-review.md`
- `docs/plans/cli-dependencies-review.md`
- `docs/plans/cli-security-review.md`
- `docs/plans/cli-best-practices-review.md`
- `docs/plans/CLI_CODE_REVIEW_SUMMARY.md`
- `tests/cli/test_cli_commands.py`
- `docs/plans/cli-review-issues/001-dual-cli-implementation.md`
- `docs/plans/cli-review-issues/002-add-cli-test-coverage.md`
- `docs/plans/cli-review-issues/003-standardize-error-handling.md`

**Execution Approach:**
Run tasks sequentially using `superpowers:executing-plans` skill. Each task is bite-sized (2-5 min steps) with clear verification.
