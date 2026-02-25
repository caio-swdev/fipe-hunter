#!/bin/bash
# Run all tests across all FIPE Hunter packages
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Testing business-py ==="
python3 -m pytest "$PROJECT_ROOT/src/libs/business-py/tests" -v "$@"

echo ""
echo "=== Testing infra-py ==="
python3 -m pytest "$PROJECT_ROOT/src/libs/infra-py/tests" -v "$@"

echo ""
echo "=== Testing adapters-py ==="
python3 -m pytest "$PROJECT_ROOT/src/libs/adapters-py/tests" -v "$@"

echo ""
echo "=== Testing fastapi-app ==="
python3 -m pytest "$PROJECT_ROOT/src/apps/fastapi-app/tests" -v "$@"

echo ""
echo "=== All tests passed! ==="
