#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

BACKEND_PASS=0
FRONTEND_PASS=0
BETA_PASS=0

# Run backend tests
echo "=== Running backend tests ==="
cd "$PROJECT_ROOT/backend"
if uv run pytest tests/ -q; then
    BACKEND_PASS=1
    echo "BACKEND PASSED"
else
    echo "BACKEND FAILED"
fi

# Run frontend tests
echo ""
echo "=== Running frontend tests ==="
cd "$PROJECT_ROOT/frontend"
if npm run test; then
    FRONTEND_PASS=1
    echo "FRONTEND PASSED"
else
    echo "FRONTEND FAILED"
fi

# Beta-gate check across all scenarios
echo ""
echo "=== Checking beta gate for all scenarios ==="
cd "$PROJECT_ROOT/backend"
if uv run python "$PROJECT_ROOT/scripts/check_beta_gate.py"; then
    BETA_PASS=1
    echo "BETA GATE PASSED"
else
    BETA_PASS=0
    echo "BETA GATE FAILED"
fi

# Final verdict
echo ""
if [ "$BACKEND_PASS" -eq 1 ] && [ "$FRONTEND_PASS" -eq 1 ] && [ "$BETA_PASS" -eq 1 ]; then
    echo "REGRESSION PASSED"
    exit 0
else
    echo "REGRESSION FAILED"
    exit 1
fi
