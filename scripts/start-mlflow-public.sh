#!/bin/bash
# Quick start script for MLflow with DSPy autologging (external access enabled)

set -e

echo "🚀 Starting MLflow UI with DSPy autologging (external access enabled)..."
echo ""

# Check if mlruns directory exists
if [ ! -d "mlruns" ]; then
    echo "📁 Creating mlruns directory..."
    mkdir -p mlruns
fi

# Start MLflow UI with external access
echo "✅ MLflow UI starting on http://0.0.0.0:5000"
echo "🌐 Access from other machines via: http://$(hostname -f).local:5000 or http://$(ipconfig getifaddr en0 2>/dev/null | grep inet | awk '{print $2}'):5000"
echo ""
echo "⚠️  WARNING: Server is accessible from other devices on your network!"
echo "Press Ctrl+C to stop the server"
echo ""

uv run mlflow ui \
    --host 0.0.0.0 \
    --port 5000 \
    --backend-store-uri sqlite:///mlflow.db \
    --default-artifact-root ./mlartifacts \
    --allowed-hosts "*" \
    --cors-allowed-origins "*"
