#!/bin/bash
# Quick start script for MLflow with DSPy autologging

set -e

echo "🚀 Starting MLflow UI with DSPy autologging..."
echo ""

# Ensure artifact root exists
mkdir -p mlartifacts

# Start MLflow UI
echo "✅ MLflow UI starting on http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run mlflow ui \
    --host localhost \
    --port 5001 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts
