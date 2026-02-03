#!/bin/bash
# Quick start script for MLflow with DSPy autologging (external access enabled)

set -e

echo "🚀 Starting MLflow UI with DSPy autologging (external access enabled)..."
echo ""

# Ensure artifact root exists
mkdir -p mlartifacts

# Start MLflow UI with external access
echo "✅ MLflow UI starting on http://0.0.0.0:5001 (port 5000 is used by AirPlay)"
echo "🌐 Access from other machines via: http://$(hostname -f).local:5001 or http://$(ipconfig getifaddr en0 2>/dev/null | grep inet | awk '{print $2}'):5001"
echo ""
echo "⚠️  NOTE: Using port 5001 instead of 5000 (AirPlay uses 5000)"
echo "Press Ctrl+C to stop the server"
echo ""

uv run mlflow ui \
    --host 0.0.0.0 \
    --port 5001 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts \
    --allowed-hosts "*" \
    --cors-allowed-origins "*"
