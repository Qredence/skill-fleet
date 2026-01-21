#!/bin/bash
set -e

echo "=== Verifying Migration ==="

echo "[1/5] Checking for old imports..."
if grep -r "agentic_fleet" --include="*.py" src/ tests/ 2>/dev/null; then
    echo "FAIL: Old imports still exist"
    exit 1
fi
echo "PASS: No old imports found"

echo "[2/5] Checking build..."
if ! uv build --quiet 2>/dev/null; then
    echo "FAIL: Build failed"
    exit 1
fi
echo "PASS: Build succeeds"

echo "[3/5] Running tests..."
if ! uv run pytest -q 2>/dev/null; then
    echo "FAIL: Tests failed"
    exit 1
fi
echo "PASS: Tests pass"

echo "[4/5] Checking CLI entrypoint..."
if ! uv run python -c "from skill_fleet.cli import cli_entrypoint" 2>/dev/null; then
    echo "FAIL: CLI import broken"
    exit 1
fi
echo "PASS: CLI import works"

echo "[5/5] Verifying directory structure..."
if [ ! -d "skills" ]; then
    echo "FAIL: skills/ directory missing"
    exit 1
fi
if [ ! -d "src/skill_fleet" ]; then
    echo "FAIL: skill_fleet/ directory missing"
    exit 1
fi
echo "PASS: Directories in place"

echo ""
echo "=== ALL CHECKS PASSED ==="
