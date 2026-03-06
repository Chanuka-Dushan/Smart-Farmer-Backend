#!/bin/sh
set -e

echo "Starting Smart Farmer Backend..."
echo "Current working directory: $(pwd)"
echo "Listing files in current directory:"
ls -la

echo "Python version:"
python --version

echo "🔧 Fixing OpenCV installation (removing GUI version)..."
pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
pip install --no-cache-dir opencv-python-headless>=4.8.0
echo "✅ OpenCV headless ready"

echo "Installed packages:"
pip list | grep -E "gunicorn|uvicorn|fastapi|opencv"

echo "Starting Gunicorn..."
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
