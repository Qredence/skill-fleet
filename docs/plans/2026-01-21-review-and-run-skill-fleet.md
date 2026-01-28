# Review and Run Skill-Fleet Commands Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Review and safely execute `skill-fleet` CLI commands (`serve`, `chat`, `dev`) in the current environment to verify functionality.

**Architecture:** The CLI uses Typer. `serve` runs a Uvicorn server. `chat` connects to that server and runs a HITL loop (optionally via TUI). `dev` orchestrates both API and TUI (via npm). We will test `serve` in the background and `chat` in headless mode.

**Tech Stack:** Python, Typer, FastAPI, Uvicorn, uv.

### Task 1: Environment Verification & Setup

**Files:**
- Read: `src/skill_fleet/cli/commands/dev.py` (Already done)
- Check: `cli/tui` directory

**Step 1: Verify Dependencies**
Check if `uv` and `npm` are available.
Run: `uv --version && npm --version`
Expected: Version numbers.

**Step 2: Verify TUI Directory**
Run: `ls -F src/skill_fleet/cli/tui/`
Expected: `package.json`, etc.

### Task 2: Test `skill-fleet serve`

**Files:**
- Log: `serve.log`

**Step 1: Start Server in Background**
Run: `uv run skill-fleet serve --port 8001 --host 127.0.0.1 --auto-accept --skip-db-init > serve.log 2>&1 &`
Expected: Process starts.

**Step 2: Wait and Verify Health**
Run: `sleep 5 && curl -v http://127.0.0.1:8001/docs`
Expected: HTTP 200 OK.

### Task 3: Test `skill-fleet chat` (Headless)

**Files:**
- Log: `chat.log`

**Step 1: Run Chat Command**
Run: `SKILL_FLEET_API_URL=http://127.0.0.1:8001 uv run skill-fleet chat "Create a simple hello-world python skill" --no-tui --auto-approve --force-plain-text`
Expected: Command completes successfully (or fails gracefully if server logic requires more), creating a job and running it.

**Step 2: Cleanup Server**
Run: `pkill -f "skill_fleet.api.app:app" || true`

### Task 4: Analysis of `skill-fleet dev`

**Step 1: Explain `dev` command**
Since `dev` requires interactive TUI and npm compilation which might be heavy/blocking, we will skip execution and just output the analysis based on code review.
