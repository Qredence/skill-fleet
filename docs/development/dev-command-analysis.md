# Analysis of `skill-fleet dev`

This document analyzes the implementation of the `skill-fleet dev` command (`src/skill_fleet/cli/commands/dev.py`), which orchestrates the development environment by running both the FastAPI backend and the Node.js TUI.

## Process Management

The command manages two distinct subprocesses:

1.  **API Server (Python/Uvicorn)**
    *   **Command:** `sys.executable -m uvicorn skill_fleet.app.main:app ...`
    *   **Logging:** `stdout` and `stderr` are redirected to a file: `.skill_fleet_logs/api-dev.log`. This prevents API logs from interfering with the TUI interface.
    *   **Readiness:** The command polls the `/docs` endpoint (via `_wait_for_api_ready`) to ensure the API is accepting requests before launching the TUI.

2.  **TUI (Node/NPM)**
    *   **Command:** `npm run <script>` (default script is `dev`).
    *   **Directory:** Runs in `cli/tui` relative to the repository root.
    *   **Environment:** Injects `SKILL_FLEET_API_URL` and `SKILL_FLEET_USER_ID` into the process environment.
    *   **Output:** Inherits `stdout`/`stderr` (default `subprocess.Popen` behavior), allowing the TUI to render directly to the terminal.

## Reload Handling

*   **Implementation:** The `--reload` flag is passed directly to Uvicorn.
*   **Default:** Disabled (`False`) by default.
*   **Caveats:**
    *   **State Loss:** The CLI explicitly warns that in-memory state (like active jobs) is lost when Uvicorn reloads.
    *   **Port Conflicts:** The help text notes that reload is disabled by default to "prevent port binding issues," suggesting historical issues with Uvicorn holding onto ports during rapid restarts.

## Cleanup Strategy

The command uses a robust cleanup strategy in a `finally` block:

1.  **Monitoring Loop:** A `while True` loop continuously polls both processes using `.poll()`.
2.  **Coupled Lifecycle:**
    *   If the API stops, the TUI is terminated.
    *   If the TUI stops, the API is terminated.
3.  **Termination Protocol:**
    *   Upon exit (including `KeyboardInterrupt`), it iterates through both process handles.
    *   Attempts `terminate()` (SIGTERM).
    *   Waits up to 5 seconds.
    *   Escalates to `kill()` (SIGKILL) if the process refuses to exit.
    *   Closes the API log file handle.

## Identified Risks & Observations

1.  **Log Management:** API logs are appended (`"a"`) indefinitely without rotation. Frequent use could lead to large log files in `.skill_fleet_logs/`.
2.  **Path Coupling:** The TUI directory is hardcoded as `repo_root / "cli" / "tui"`. Changes to the project structure would break this command.
3.  **Zombie Processes:** While the `finally` block handles SIGINT, an abrupt SIGKILL to the main process would leave the subprocesses running (orphaned).
4.  **Health Check Limitations:** The readiness check relies on the `/docs` endpoint. This proves the web server is running but does not guarantee that internal subsystems (databases, LLM connections) are fully operational.
5.  **NPM Dependency:** The command assumes `npm` is in the system PATH. While it catches `FileNotFoundError`, it doesn't validate the node version or `node_modules` state before execution.
