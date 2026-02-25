#!/bin/bash
# Install all FIPE Hunter packages in development mode
# Order matters: leaf-first (business -> infra -> adapters -> app)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing fipe-business..."
pip install -e "$PROJECT_ROOT/src/libs/business-py"

echo "Installing fipe-infra..."
pip install -e "$PROJECT_ROOT/src/libs/infra-py"

echo "Installing fipe-adapters..."
pip install -e "$PROJECT_ROOT/src/libs/adapters-py"

echo "Installing fipe-hunter-app..."
pip install -e "$PROJECT_ROOT/src/apps/fastapi-app"

echo "All packages installed successfully."
