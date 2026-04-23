#!/bin/bash
set -e

echo "========================================" >&2
echo "🚀 Smart Farmer Backend Starting" >&2
echo "========================================" >&2
echo "Python: $(python --version)" >&2
echo "Working Dir: $(pwd)" >&2

echo "" >&2
echo "🔍 OpenCV Check" >&2
echo "========================================" >&2
pip list 2>&1 | grep opencv >&2 || echo "No opencv found!" >&2

# Emergency opencv fix if needed
if pip list 2>&1 | grep -E "^opencv-python " | grep -v headless >/dev/null 2>&1; then
    echo "❌ GUI opencv detected - fixing..." >&2
    pip uninstall -y opencv-python opencv-contrib-python >&2 || true
    pip install --force-reinstall --no-deps opencv-python-headless==4.10.0.84 >&2
    echo "✅ Fixed" >&2
else
    echo "✅ Correct opencv" >&2
fi

echo "" >&2
echo "========================================" >&2
echo "Starting Gunicorn..." >&2
echo "========================================" >&2

exec gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers 4 \
    --bind 0.0.0.0:8080 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output
