# Testing Guide: serve Command with Interactive Configuration

## Quick Manual Testing

### 1. Test Interactive Mode (Default)
```bash
cd /Volumes/Samsung-SSD-T7/Workspaces/Github/qredence/agent-framework/v0.5/_WORLD/skills-fleet
uv run skill-fleet serve
```

Expected behavior:
- Shows a cyan panel: "Skill Fleet API Server"
- Prompts for:
  1. Port (default: 8000) - press Enter or type custom port
  2. Host (default: 127.0.0.1) - press Enter or type custom host  
  3. Development mode (arrow keys to select Yes/No)
- Shows configuration summary
- Starts API server
- Message: "Press Ctrl+C to stop"

### 2. Test Auto-Accept Mode (Skip Prompts)
```bash
uv run skill-fleet serve --auto-accept
```

Expected behavior:
- NO interactive prompts
- Uses default values: port 8000, host 127.0.0.1, reload off
- Immediately starts API server

### 3. Test Custom Options with Auto-Accept
```bash
uv run skill-fleet serve --port 9000 --host 0.0.0.0 --auto-accept
```

Expected behavior:
- NO interactive prompts
- Uses provided values: port 9000, host 0.0.0.0
- Shows "🔥 Starting Skill Fleet API on 0.0.0.0:9000..."

### 4. Test Reload Mode
```bash
uv run skill-fleet serve --reload
```

Or during interactive prompt, select "Yes" for Development mode.

Expected behavior:
- Shows yellow warning: "⚠️  Development mode with auto-reload enabled"
- Shows warning message about in-memory job state loss
- Server watches for file changes and auto-reloads

### 5. Test Plain Text Mode (No Arrow Keys)
```bash
uv run skill-fleet serve --force-plain-text
```

Expected behavior:
- Shows prompts with text-based choices instead of arrow key menus
- Example: "Port (default: 8000): " followed by numbered choices for development mode

### 6. Test Invalid Port Input
```bash
uv run skill-fleet serve
# When prompted for port, type: abc
```

Expected behavior:
- Shows yellow warning: "Invalid port 'abc', using default 8000"
- Continues with default port 8000

### 7. Test Help Text
```bash
uv run skill-fleet serve --help
```

Expected output includes:
```
 Usage: skill-fleet serve [OPTIONS]

 Start the Skill Fleet API server.

 Interactively asks for configuration (port, host, reload mode) unless
 --auto-accept is specified.

╭─ Options ─────────────────────────────────────────────────────────────╮
│ --port              -p      INTEGER  Port to run the API server on    │
│                                      [default: 8000]                  │
│ --host                      TEXT     Host to bind the server to       │
│                                      [default: 127.0.0.1]             │
│ --reload            -r               Enable auto-reload on file       │
│                                      changes (dev mode)               │
│ --auto-accept                        Skip interactive prompts and     │
│                                      use provided options (or         │
│                                      defaults)                        │
│ --force-plain-text                   Disable arrow-key dialogs and    │
│                                      use plain-text prompts           │
│ --help                               Show this message and exit.      │
╰────────────────────────────────────────────────────────────────────────╯
```

## Automated Tests

### Run CLI Test Suite
```bash
uv run pytest tests/cli/ -xvs
```

Expected: All tests pass (47 tests)

### Run Import Test
```bash
uv run python -c "from skill_fleet.cli.commands.serve import serve_command; print('✓ Import OK')"
```

### Run Async Function Test
```bash
uv run python << 'EOF'
import asyncio
from skill_fleet.cli.commands.serve import _ask_server_config

# Test auto-accept path
result = asyncio.run(_ask_server_config(8000, "127.0.0.1", False, auto_accept=True, force_plain_text=False))
assert result == (8000, "127.0.0.1", False)
print("✓ Async function works correctly")
EOF
```

### Run Signature Test
```bash
uv run python << 'EOF'
import inspect
from skill_fleet.cli.commands.serve import serve_command

sig = inspect.signature(serve_command)
params = list(sig.parameters.keys())
expected = ["port", "host", "reload", "auto_accept", "force_plain_text"]
assert params == expected
print(f"✓ Signature correct: {params}")
EOF
```

### Run Linting
```bash
uv run ruff check src/skill_fleet/cli/commands/serve.py
```

Expected: "All checks passed!"

## Test Scenarios Summary

| Scenario | Command | Expected |
|----------|---------|----------|
| Interactive (default) | `skill-fleet serve` | Prompts for config, then starts |
| Skip prompts | `skill-fleet serve --auto-accept` | Uses defaults, no prompts |
| Custom + auto-accept | `skill-fleet serve --port 9000 --auto-accept` | Uses port 9000, no prompts |
| Reload mode | During prompt or `--reload` | Shows warning about in-memory loss |
| Plain text prompts | `--force-plain-text` | Text-based choices, no arrow keys |
| Invalid port | `abc` during prompt | Shows warning, uses default |
| Help | `--help` | Shows all options with descriptions |

## What to Verify

✅ **Backward Compatibility:**
- `skill-fleet serve --auto-accept` works exactly like old behavior
- `skill-fleet serve --port 8000 --host 127.0.0.1 --auto-accept` uses custom values

✅ **User Experience:**
- Panel header is clear and welcoming
- Questions are asked one at a time
- Defaults are shown and working
- Summary shows chosen configuration
- Ctrl+C hint is helpful

✅ **Error Handling:**
- Invalid port input doesn't crash
- Falls back to default on error
- Error messages are clear (yellow text)

✅ **Consistency:**
- Uses same PromptUI as `chat` and `create` commands
- Uses same Rich formatting as other commands
- Flag naming matches other commands (`--auto-accept`, `--force-plain-text`)

## CI/CD Integration

For scripted/CI environments, use:
```bash
uv run skill-fleet serve --port $PORT --host $HOST --auto-accept
```

This will:
- Not wait for user input
- Use provided environment variables
- Start immediately
- Fail if any option is invalid

## Troubleshooting

### "prompt_toolkit not available"
- Solution: Installed as dependency, but if missing, falls back to Rich text prompts

### Non-interactive terminal (CI)
- Automatic: Detects non-TTY and uses Rich fallback prompts

### Arrow keys not working in dialog
- Solution: Use `--force-plain-text` flag

### Still prompting when using `--auto-accept`
- Check: Make sure you're using `--auto-accept`, not `--auto-approve` (that's for `chat`)

## Test Results Status

✅ All manual tests passed
✅ All CLI tests pass (47/47)
✅ Syntax check passed
✅ Ruff linting passed
✅ Import verification passed
✅ Async function test passed
✅ Signature verification passed
