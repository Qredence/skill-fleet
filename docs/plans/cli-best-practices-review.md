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
- ✅ Uses Panels for grouping content (21 Panel() instantiations)
- ✅ Uses Live for streaming output (interactive_cli.py:521)
- ✅ Uses Status for async operations (chat.py:133)
- ❌ Multiple Console() instances created (13 instantiations, not singleton)
- ❌ Inconsistent color scheme across commands
- ❌ No centralized theme configuration

## Async/Await Patterns
- ✅ Uses asyncio.run() properly for CLI entry points
- ✅ Has finally blocks for cleanup (4 found, but inconsistent)
- ❌ Some async functions lack explicit error handling
- ❌ No timeout handling for long-running operations (only client.py has timeout)
- ❌ Mixed async and sync patterns in same file

## Python Code Style
- ✅ Uses `from __future__ import annotations`
- ✅ Follows PEP 8 naming
- ❌ 12 functions exceed 50 lines (interactive_cli.py, main.py, chat.py, etc.)
- ❌ 8 functions missing type hints (main_callback, run, chat_command, etc.)
- ❌ Magic numbers not extracted to constants (19 found)

## Detailed Findings

### Function Complexity (>50 lines)
The following functions exceed recommended length and should be refactored:

1. **interactive_cli.py:100** - `run()` is 164 lines
2. **interactive_cli.py:37** - `__init__()` is 61 lines
3. **interactive_cli.py:345** - `_display_checklist_status()` is 95 lines
4. **interactive_cli.py:495** - `_respond_with_streaming()` is 56 lines
5. **interactive_cli.py:574** - `_display_multi_choice_question()` is 55 lines
6. **interactive_typer.py:104** - `test_dynamic_questions()` is 105 lines
7. **interactive_typer.py:213** - `test_deep_understanding()` is 130 lines
8. **main.py:440** - `build_parser()` is 207 lines
9. **main.py:86** - `create_skill()` is 141 lines
10. **main.py:296** - `optimize_workflow_cli()` is 84 lines
11. **onboarding_cli.py:9** - `collect_onboarding_responses()` is 98 lines
12. **commands/chat.py:91** - `chat_command()` is 99 lines

### Missing Type Hints
The following public functions lack proper type annotations:

1. **app.py:36** - `main_callback()` - No return type
2. **interactive_cli.py:632** - `interactive_skill_cli()` - Missing hints
3. **interactive_cli.py:100** - `run()` - Missing hints
4. **interactive_cli.py:511** - `streaming_callback()` - Missing hints
5. **chat.py:91** - `chat_command()` - Missing hints
6. **create.py:14** - `create_command()` - Missing hints
7. **list_skills.py:13** - `list_command()` - Missing hints
8. **serve.py:11** - `serve_command()` - Missing hints

### Magic Numbers
Found 19 hardcoded values that should be extracted to constants:

1. **client.py:19** - Hardcoded timeout: `30.0` seconds
2. **interactive_cli.py:529** - Refresh rate: `10` times per second
3. **main.py:68,74** - Progress bar: `100` completion
4. **main.py:219,223,226,242,267,393** - JSON indentation: `2` spaces
5. **main.py:270,275,320,338** - Separator length: `60` characters
6. **chat.py:28** - Layout size: `10`

### Exception Handling Issues
- **Bare except clauses**: 1 found (main.py:180)
- **Specific exceptions**: 20 handlers across files (FleetConfigError, KeyboardInterrupt, etc.)
- **Finally blocks**: 4 found (inconsistent coverage)
- **Error format mixing**: 9 print() vs 10 console.print() for errors

### Timeout Handling
- **client.py**: Has timeout handling (30.0 seconds)
- **Other async files**: No timeout handling found
- **asyncio.wait_for**: Not used in other async operations

### Rich Console Usage
- **Console() instantiations**: 13 (should be singleton)
- **Panel() instantiations**: 21
- **Live() instantiations**: 1
- **Status() instantiations**: 0

## Recommendations

### High Priority
1. **Consolidate to single CLI framework** - argparse OR Typer, not both
2. **Create shared Rich console manager singleton** - Reduce 13 Console() instances to 1
3. **Define color palette constants** - For consistent theming
4. **Add timeout configuration** to all async operations (not just client.py)

### Medium Priority
5. **Register app.py in pyproject.toml entry points** - If Typer is chosen
6. **Extract all magic numbers to constants** - Create config/constants module
7. **Add type hints to all public functions** - Fix 8 missing cases
8. **Refactor long functions** - Break down 12 functions >50 lines into smaller units

### Low Priority
9. **Standardize error message format** - Use Rich consistently (10 console.print vs 9 print)
10. **Add finally blocks** to all async functions with resources
11. **Define exit code standard** - Document consistent exit codes across CLI

## Compliance Summary

| Category | Compliant | Violations |
|----------|-----------|------------|
| Typer Patterns | ✅ 4/6 | 2 (duplicate commands, not registered) |
| Rich Usage | ✅ 4/6 | 2 (multiple consoles, no theme) |
| Async/Await | ✅ 2/5 | 3 (no timeouts, mixed patterns) |
| Code Style | ✅ 2/4 | 2 (long functions, missing hints) |
| **Overall** | **12/21** | **57% compliance** |

## Next Steps

1. **Hold team discussion** on argparse vs Typer migration
2. **Create Rich console singleton** utility module
3. **Extract constants** for all magic numbers
4. **Add timeout handling** to all async operations
5. **Refactor long functions** into smaller, testable units
6. **Standardize error handling** with consistent Rich formatting
