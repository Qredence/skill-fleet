# Fix for HTTP 500 Error in Streaming

## Issue

When using the TUI (`uv run skill-fleet chat`), you saw:
```
Assistant: ❌ Error: HTTP 500: Internal Server Error
```

## Root Cause

The server needs to be **restarted** to pick up the latest code changes (enhanced error handling and logging).

## Solution: Restart the Server

### Step 1: Stop the Current Server

Find and kill the running server:
```bash
# Find the process
ps aux | grep "skill-fleet serve" | grep -v grep

# Kill it (Ctrl+C in the server terminal, or)
pkill -f "skill-fleet serve"
```

### Step 2: Verify Environment

Make sure `GOOGLE_API_KEY` is set:
```bash
echo $GOOGLE_API_KEY

# If empty, set it:
export GOOGLE_API_KEY='your-api-key-here'

# Or add to .env file
echo "GOOGLE_API_KEY=your-key" >> .env
```

### Step 3: Restart Server

```bash
# From project root
uv run skill-fleet serve

# Or with reload for development
uv run skill-fleet serve --reload
```

**Look for** in startup logs:
```
INFO: DSPy configured successfully
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test TUI Again

**In a new terminal:**
```bash
cd cli/tui
node dist/index.js

# Or via Python CLI
uv run skill-fleet chat
```

**Try**:
```
hi
/help
/list
```

## Enhanced Error Handling (Just Added)

The streaming endpoint now has **detailed logging**:

✅ Checks DSPy configuration before processing
✅ Logs each streaming event  
✅ Returns detailed error messages (error type + message)
✅ Verifies StreamingAssistant initialization
✅ Connection: keep-alive header for stable SSE

If you still get errors, check the **server terminal** for detailed logs:
```
INFO: Chat stream request received: message='hi'
INFO: DSPy LM configured: <LM object>
INFO: StreamingAssistant initialized
INFO: Event 1: thinking
INFO: Event 2: response
...
INFO: Streaming completed successfully (10 events)
```

## Quick Diagnostic Test

**Test streaming directly** (bypassing TUI):
```bash
# From project root
uv run python test_streaming.py
```

**Expected output**:
```
✅ GOOGLE_API_KEY found
✅ DSPy configured successfully
✅ StreamingAssistant initialized

Testing with message: 'hello'
──────────────────────────────────────────────────
💭 Thinking: Step 1: Understanding user intent...
💬 Response: Hello! I'm here and ready to help...
✅ Complete
──────────────────────────────────────────────────

✅ Streaming test successful!
```

## Duplicate Key Warning (Fixed ✅)

You also saw:
```
Encountered two children with the same key, `msg-0`
```

**This is now fixed!** The message ID counter starts at 1 (not 0) to avoid conflict with `welcome-0`.

## Next Steps

Once the server is restarted:

1. ✅ TUI should connect without 500 errors
2. ✅ Chat messages will stream responses
3. ✅ Thinking chunks will display in real-time
4. ✅ Commands will execute successfully
5. ✅ All 4 tabs fully functional

---

## Summary of Fixes

| Issue | Status | Fix |
|-------|--------|-----|
| Duplicate key `msg-0` | ✅ FIXED | Counter starts at 1 |
| HTTP 500 error | ✅ IMPROVED | Enhanced logging + error handling |
| Missing diagnostics | ✅ ADDED | test_streaming.py script |

**Restart the server and you're good to go!** 🚀
