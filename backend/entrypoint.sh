#!/bin/sh
set -e

# Force output to stderr to ensure visibility
exec 2>&1

echo "========================================" >&2
echo "🚀 Starting Smart Farmer Backend" >&2
echo "========================================" >&2
echo "Current working directory: $(pwd)" >&2
echo "Python version: $(python --version)" >&2

echo "" >&2
echo "🔧 OpenCV Installation Check" >&2
echo "========================================" >&2

# Show current opencv packages
echo "Current OpenCV packages:" >&2
pip list 2>&1 | grep -i opencv || echo "No opencv packages found" >&2

# Check if GUI version is installed
if pip list 2>&1 | grep -E "^opencv-python " | grep -v headless > /dev/null 2>&1; then
    echo "❌ CRITICAL: opencv-python (GUI version) detected!" >&2
    echo "   Attempting to fix..." >&2
    pip uninstall -y opencv-python opencv-contrib-python 2>&1 || true
    pip install --force-reinstall --no-cache-dir opencv-python-headless>=4.8.0 2>&1
    echo "✅ OpenCV headless reinstalled" >&2
else
    echo "✅ OpenCV configuration looks correct" >&2
fi

echo "" >&2
echo "Final OpenCV packages:" >&2
pip list 2>&1 | grep -i opencv || echo "No opencv packages!" >&2

echo "" >&2
echo "========================================" >&2
echo "Starting Gunicorn..." >&2
echo "========================================" >&2
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
