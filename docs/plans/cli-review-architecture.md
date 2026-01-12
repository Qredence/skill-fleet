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

---

## Code Quality Issues

### Long Functions (>50 lines)

**interactive_cli.py (5 long functions)**
- `run()` - 164 lines: Complex interaction loop with state management
- `__init__()` - 61 lines: Large initialization logic
- `_handle_command()` - 54 lines: Command parsing and routing
- `_display_checklist_status()` - 95 lines: UI rendering logic
- `_respond_with_streaming()` - 56 lines: Streaming response handling
- `_display_multi_choice_question()` - 55 lines: Question formatting

**main.py (4 long functions)**
- `create_skill()` - 141 lines: Skill creation workflow orchestration
- `optimize_workflow_cli()` - 84 lines: Optimization logic with MIPROv2/GEPA
- `show_analytics()` - 54 lines: Analytics display
- `build_parser()` - 207 lines: Argument parser configuration

**interactive_typer.py (3 long functions)**
- `interactive_chat()` - 65 lines: Chat interface
- `test_dynamic_questions()` - 105 lines: Question testing
- `test_deep_understanding()` - 130 lines: Understanding verification

**onboarding_cli.py (1 long function)**
- `collect_onboarding_responses()` - 98 lines: User data collection

**commands/chat.py (2 long functions)**
- `chat_command()` - 99 lines: Chat dashboard orchestration
- `create_dashboard_layout()` - 69 lines: Rich layout creation

**commands/create.py (1 long function)**
- `create_command()` - 79 lines: Command execution wrapper

### Code Duplication

**Console() Instantiations (5 total)**
- `main.py`: 3 instances
- `app.py`: 1 instance
- `interactive_cli.py`: 1 instance
- **Impact**: Inconsistent styling, multiple Rich console objects created
- **Recommendation**: Create singleton console manager in shared utility

**Async Wrapper Patterns**
- `client.py`: 7 async functions with similar patterns
- `commands/create.py`, `commands/chat.py`: Repeated async wrappers with `try/except/finally` and `client.close()`
- **Impact**: Duplicated error handling and cleanup logic
- **Recommendation**: Extract shared async wrapper with context manager

**Error Handling Patterns**
- `main.py`: 5 try/except blocks
- `interactive_cli.py`: 5 try blocks, 9 except blocks
- Mix of `print(..., file=sys.stderr)` and `console.print("[red]Error...[/red]")`
- **Impact**: Inconsistent error reporting across CLI
- **Recommendation**: Create unified error display utility

### Hardcoded Values

**Timeouts and Delays**
- `client.py:19`: `timeout=30.0` - httpx client timeout (30 seconds)
- `interactive_cli.py:529`: `refresh_per_second=10` - UI refresh rate
- `commands/chat.py:183`: `await asyncio.sleep(2)` - 2-second delay
- `commands/create.py:87`: `await asyncio.sleep(2)` - 2-second delay

**Magic Numbers (analysis)**
- `main.py`: 30 magic numbers (excluding 0,1,2,10)
- `interactive_cli.py`: 7 magic numbers
- `client.py`: 2 magic numbers (8000, 30)
- `onboarding_cli.py`: 6 magic numbers
- Sample: 100, 70, 60, 8, 20, 200, 150, 8000, 30

**Long String Literals**
- `main.py`: 86 long strings (>50 characters)
- `interactive_cli.py`: 119 long strings
- `client.py`: 12 long strings
- `app.py`: 6 long strings
- `onboarding_cli.py`: 17 long strings
- **Impact**: UI messages and help text embedded in code
- **Recommendation**: Extract to constants or external message files

### Recommendations

1. **Extract Shared Patterns**
   - Create `src/skill_fleet/cli/utils/console.py` with singleton Console manager
   - Create `src/skill_fleet/cli/utils/async_wrapper.py` for consistent async handling
   - Create `src/skill_fleet/cli/utils/errors.py` for unified error display

2. **Break Down Long Functions**
   - `interactive_cli.py:run()` → Extract UI update loop, command handler, state manager
   - `main.py:create_skill()` → Extract workflow steps to separate functions
   - `main.py:build_parser()` → Extract subparser builders to functions
   - `commands/chat.py:chat_command()` → Extract dashboard setup, event loop

3. **Define Constants**
   - Create `src/skill_fleet/cli/constants.py` for:
     - HTTP timeouts
     - UI refresh rates
     - Sleep delays
     - Exit codes
     - Color schemes
   - Replace all magic numbers with named constants

4. **Refactor Code Duplication**
   - Consolidate Console() to single instance
   - Create async context manager for httpx client lifecycle
   - Standardize error message format with Rich Panel
