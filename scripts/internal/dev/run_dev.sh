#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_URL="${SKILL_FLEET_API_URL:-http://localhost:8000}"
USER_ID="${SKILL_FLEET_USER_ID:-default}"
RELOAD_FLAG=()
LOG_DIR="$ROOT_DIR/.skill_fleet_logs"
API_LOG_FILE="${SKILL_FLEET_API_LOG:-$LOG_DIR/api-dev.log}"

if [[ "${SKILL_FLEET_RELOAD:-1}" == "1" || "${SKILL_FLEET_RELOAD:-}" == "true" ]]; then
  RELOAD_FLAG=("--reload")
fi

mkdir -p "$LOG_DIR"
echo "Starting API server... (logs -> $API_LOG_FILE)"
(
  cd "$ROOT_DIR"
  uv run skill-fleet serve "${RELOAD_FLAG[@]}" >"$API_LOG_FILE" 2>&1
) &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API server to be ready..."
MAX_WAIT=30
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if curl -sf "$API_URL/docs" >/dev/null 2>&1; then
    echo "✅ API server is ready"
    break
  fi
  sleep 0.5
  ELAPSED=$((ELAPSED + 1))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo "⚠️  API server didn't respond in time (may still be loading)"
fi

echo "Starting TUI..."
cd "$ROOT_DIR/cli/tui"

cleanup() {
  echo "Stopping API server (PID $API_PID)..."
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

SKILL_FLEET_API_URL="$API_URL" SKILL_FLEET_USER_ID="$USER_ID" npm run dev
