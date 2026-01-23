#!/bin/bash
# Quick start script for MLflow with DSPy autologging

set -e

echo "🚀 Starting MLflow UI with DSPy autologging..."
echo ""

# Check if mlruns directory exists
if [ ! -d "mlruns" ]; then
    echo "📁 Creating mlruns directory..."
    mkdir -p mlruns
fi

# Start MLflow UI
echo "✅ MLflow UI starting on http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uv run mlflow ui \
    --host localhost \
    --port 5000 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts
