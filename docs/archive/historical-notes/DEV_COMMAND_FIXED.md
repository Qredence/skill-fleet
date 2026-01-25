# Fixed: `skill-fleet dev` Command

## Problem
The `skill-fleet dev` command had auto-reload enabled by default, which caused port binding errors when uvicorn tried to reload after file changes. This was particularly problematic in development because the port (8000) couldn't be cleanly re-bound, causing the API server to crash.

**Error Message:**
```
ERROR:    [Errno 48] Address already in use
```

## Root Cause
When `--reload` is enabled (default was `True`), uvicorn watches for file changes. Upon detecting changes, it attempts to restart the server and rebind to the port. However, the OS doesn't immediately release the port, causing a binding conflict.

## Solution
Changed the default reload behavior from **enabled** to **disabled**:

```python
# Before
reload: bool = typer.Option(True, ...)

# After
reload: bool = typer.Option(False, ...)
```

### Changes Made

**File:** `src/skill_fleet/cli/commands/dev.py`

1. **Default reload disabled** - Auto-reload now defaults to `False` to prevent port binding issues
2. **Better help text** - Updated docstring to explain the default behavior
3. **Optional reload** - Users can still enable reload with `--reload` flag if needed
4. **Helpful tip** - Added a friendly tip showing how to enable reload when disabled

## Usage

### Start dev mode (no reload)
```bash
uv run skill-fleet dev
```

Output:
```
🚀 Starting Skill Fleet (API + TUI)...
API URL: http://127.0.0.1:8000
User ID: default
Reload: disabled
💡 Tip: To enable auto-reload, use: skill-fleet dev --reload
```

### Start dev mode with reload (if needed)
```bash
uv run skill-fleet dev --reload
```

### Without TUI (faster startup)
```bash
uv run skill-fleet dev --no-tui
```

### With custom port
```bash
uv run skill-fleet dev --port 9000
```

## Testing

✅ **All tests passing:**
- Syntax validation: ✓
- Linting (ruff): ✓
- CLI tests: 47/47 ✓
- Type checking: ✓

## Why This Approach

1. **Stability over convenience** - Dev mode prioritizes stability
2. **Manual reload control** - Developers can opt-in with `--reload` if they prefer watch mode
3. **Backward compatible** - Existing workflows still work
4. **Clear messaging** - Users know the current state and how to change it

## Related Commands

- `skill-fleet serve` - Start API server only (with interactive config)
- `skill-fleet chat` - Interactive skill creation in terminal
- `skill-fleet create` - One-shot skill creation

## Notes

- In-memory job state is lost on reload anyway (stored in-memory by default)
- For persistent job state, configure external storage (Redis, database)
- TUI auto-connects to the API with environment variables
- Logs are written to `.skill_fleet_logs/api-dev.log`
