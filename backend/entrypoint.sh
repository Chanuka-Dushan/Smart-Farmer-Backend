#!/bin/sh
set -e

echo "Starting Smart Farmer Backend..."
echo "Current working directory: $(pwd)"
echo "Listing files in current directory:"
ls -la

echo "Python version:"
python --version

echo "🔧 Verifying OpenCV installation..."
if pip list | grep -E "^opencv-python " | grep -v headless > /dev/null 2>&1; then
    echo "⚠️  Detected opencv-python (GUI version) - removing..."
    pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
    pip install --force-reinstall --no-cache-dir opencv-python-headless>=4.8.0
    echo "✅ OpenCV headless reinstalled"
else
    echo "✅ OpenCV headless already correct"
fi

echo "Installed packages:"
pip list | grep -E "gunicorn|uvicorn|fastapi|opencv|ultralytics"

echo "Starting Gunicorn..."
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
