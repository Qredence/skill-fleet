#!/bin/bash
# Quality gate script for Skills Fleet development.
# Runs all quality checks before allowing commits.

set -e  # Exit on error

echo "🔍 Running Skills Fleet Quality Gates..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to run a check and report results
run_check() {
    local name="$1"
    local command="$2"

    echo -n "Running $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo -e "${YELLOW}Command: $command${NC}"
        FAILURES=$((FAILURES + 1))
        return 1
    fi
}

# 1. Ruff linting
echo "📋 Code Quality Checks"
run_check "Ruff Linting" "uv run ruff check src/ tests/"
run_check "Ruff Formatting" "uv run ruff format --check src/ tests/"
echo ""

# 2. Type checking
echo "🔷 Type Checking"
run_check "ty Type Check" "uv run ty src/"
echo ""

# 3. Security scanning
echo "🔒 Security Checks"
run_check "Bandit Security Scan" "uv run bandit -r src/ -ll"
echo ""

# 4. Unit tests
echo "🧪 Unit Tests"
run_check "Pytest Unit Tests" "uv run pytest tests/unit/ -q"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All quality gates passed!${NC}"
    echo "You may commit your changes."
    exit 0
else
    echo -e "${RED}✗ $FAILURES quality gate(s) failed${NC}"
    echo "Please fix the issues above before committing."
    exit 1
fi
