#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

section() {
  echo ""
  echo "==> $1"
}

section "Python lint"
(
  cd "$ROOT_DIR"
  uv run ruff check .
)

section "Python format"
(
  cd "$ROOT_DIR"
  uv run ruff format .
)

section "Python tests"
(
  cd "$ROOT_DIR"
  uv run pytest
)

section "TUI type-check"
(
  cd "$ROOT_DIR/cli/tui"
  bun run type-check
)
