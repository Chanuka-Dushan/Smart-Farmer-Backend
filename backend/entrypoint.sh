#!/bin/sh
set -e

# Force ALL output to stderr to ensure visibility in logs
exec 1>&2

echo "========================================"
echo "🚀 Starting Smart Farmer Backend"
echo "========================================"
echo "Current working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "User: $(whoami)"

echo ""
echo "🔧 OpenCV Installation Check"
echo "========================================"

# Show current opencv packages
echo "Current OpenCV packages:"
pip list 2>&1 | grep -i opencv || echo "⚠️  No opencv packages found"

# CRITICAL CHECK: If GUI version exists, ABORT startup
if pip list 2>&1 | grep -E "^opencv-python " | grep -v headless > /dev/null 2>&1; then
    echo "❌❌❌ CRITICAL FAILURE ❌❌❌"
    echo "opencv-python (GUI version) STILL DETECTED!"
    echo "This should have been blocked during build."
    echo "The application CANNOT start with GUI opencv."
    echo ""
    echo "Emergency fix attempt..."
    pip uninstall -y opencv-python opencv-contrib-python 2>&1 || true
    pip install --force-reinstall --no-cache-dir opencv-python-headless==4.10.0.84 2>&1
    echo ""
    echo "Retrying opencv check..."
    pip list 2>&1 | grep -i opencv
    
    if pip list 2>&1 | grep -E "^opencv-python " | grep -v headless > /dev/null 2>&1; then
        echo "❌ Emergency fix FAILED. Aborting startup."
        exit 1
    fi
    echo "✅ Emergency fix successful"
else
    echo "✅ OpenCV configuration correct - only headless version present"
fi

echo ""
echo "Final OpenCV verification:"
pip list 2>&1 | grep -i opencv

echo ""
echo "========================================"
echo "Starting Gunicorn..."
echo "========================================"
exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
